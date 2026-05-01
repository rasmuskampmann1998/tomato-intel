"""
Social Media Scraper — Reddit, Twitter/X, Instagram, LinkedIn, Facebook, TikTok
Two modes:
  keywords  — search all platforms for configured search terms (multi-language)
  accounts  — scrape specific watched accounts from social_watched_accounts table
  both      — run both (default)

Scheduled every 3 days via .github/workflows/social-scrape.yml
"""
import os
import praw
from apify_client import ApifyClient
from datetime import datetime, timezone, timedelta
from loguru import logger

APIFY_TOKEN = os.environ.get("APIFY_API_TOKEN", "")
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "TomatoIntelBot/1.0")

REDDIT_SUBREDDITS = [
    "agriculture", "farming", "gardening", "horticulture",
    "greenhouse_gardening", "cropfarming", "urbanfarming", "tomatoes"
]

LINKEDIN_TARGET_COMPANIES = [
    "Enza Zaden", "Rijk Zwaan", "Syngenta", "Bejo Seeds", "De Ruiter Seeds",
    "HortiDaily", "Seed World"
]

TOMATO_TRANSLATIONS = {
    "zh": "番茄", "ja": "トマト", "hi": "टमाटर", "es": "tomate",
    "ar": "طماطم", "tr": "domates", "nl": "tomaat", "da": "tomat",
    "de": "Tomate", "fr": "tomate",
}


def _localise_terms(search_terms: list[str], lang: str) -> list[str]:
    if lang == "en" or lang not in TOMATO_TRANSLATIONS:
        return search_terms
    local_word = TOMATO_TRANSLATIONS[lang]
    return [t.lower().replace("tomato", local_word) for t in search_terms]


def load_watched_accounts(platform: str = None) -> list[dict]:
    """Load active watched accounts from social_watched_accounts table."""
    try:
        from db.client import supabase
        q = supabase.table("social_watched_accounts").select("*").eq("active", True)
        if platform:
            q = q.eq("platform", platform)
        return q.execute().data or []
    except Exception as e:
        logger.warning(f"[Social] Could not load watched accounts: {e}")
        return []


def _mark_scraped(handles_by_platform: dict):
    """Update last_scraped_at for the accounts we just scraped."""
    try:
        from db.client import supabase
        now = datetime.utcnow().isoformat()
        for platform, handles in handles_by_platform.items():
            for handle in handles:
                supabase.table("social_watched_accounts").update(
                    {"last_scraped_at": now}
                ).eq("platform", platform).eq("handle", handle).execute()
    except Exception:
        pass


# ──────────────────────────────────────────────
# REDDIT — keyword search
# ──────────────────────────────────────────────

def scrape_reddit(search_terms: list[str], time_filter: str = "week",
                  extra_subreddits: list[str] = None) -> list[dict]:
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        logger.warning("[Reddit] No credentials — skipping")
        return []
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
            check_for_async=False,
        )
    except Exception as e:
        logger.error(f"[Reddit] PRAW init failed: {e}")
        return []

    subreddits = list(dict.fromkeys(REDDIT_SUBREDDITS + (extra_subreddits or [])))
    all_items = []
    seen_urls = set()

    for term in search_terms:
        for subreddit_name in subreddits:
            try:
                sub = reddit.subreddit(subreddit_name)
                for post in sub.search(term, sort="relevance", time_filter=time_filter, limit=15):
                    url = f"https://www.reddit.com{post.permalink}"
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    created_dt = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
                    all_items.append({
                        "source_name": "Reddit",
                        "category_slug": "social",
                        "title": post.title,
                        "url": url,
                        "content": f"r/{subreddit_name} | Score: {post.score} | Comments: {post.num_comments}\n\n{post.selftext[:500]}",
                        "language": "en",
                        "published_at": created_dt.isoformat(),
                        "platform": "reddit",
                        "author": str(post.author) if post.author else "",
                        "like_count": post.score,
                        "comment_count": post.num_comments,
                        "share_count": None,
                        "view_count": None,
                        "post_type": "post",
                    })
            except Exception as e:
                logger.warning(f"[Reddit] r/{subreddit_name} '{term}': {e}")

    logger.info(f"[Reddit] {len(all_items)} posts")
    return all_items


# ──────────────────────────────────────────────
# TWITTER / X — keyword search
# ──────────────────────────────────────────────

def _parse_twitter_results(results: list) -> list[dict]:
    items = []
    for r in results:
        author = r.get("author", {})
        url = r.get("url", "")
        text = r.get("text", "")
        if not url or not text:
            continue
        items.append({
            "source_name": "Twitter / X",
            "category_slug": "social",
            "title": text[:120],
            "url": url,
            "content": text,
            "language": r.get("lang", "en"),
            "published_at": r.get("createdAt"),
            "platform": "twitter",
            "author": author.get("userName", ""),
            "like_count": r.get("likeCount", 0),
            "comment_count": r.get("replyCount", 0),
            "share_count": r.get("retweetCount", 0),
            "view_count": r.get("viewCount", 0),
            "post_type": "tweet",
        })
    return items


def scrape_twitter(search_terms: list[str], languages: list[str] = None) -> list[dict]:
    if not APIFY_TOKEN:
        logger.warning("[Twitter] No Apify token — skipping")
        return []
    now_utc = datetime.utcnow()
    since = (now_utc - timedelta(days=3)).strftime("%Y-%m-%d_%H:%M:%S_UTC")
    until = now_utc.strftime("%Y-%m-%d_%H:%M:%S_UTC")
    try:
        client = ApifyClient(APIFY_TOKEN)
        run = client.actor("CJdippxWmn9uRfooo").call(run_input={
            "searchTerms": search_terms,
            "sort": "Latest",
            "maxItems": 50,
            "minimumRetweets": 2,
            "minimumFavorites": 5,
            "since": since,
            "until": until,
            "queryType": "Latest",
        })
        results = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        items = _parse_twitter_results(results)
        logger.info(f"[Twitter] {len(items)} tweets (keyword)")
        return items
    except Exception as e:
        logger.error(f"[Twitter] keyword scrape failed: {e}")
        return []


def scrape_twitter_accounts(accounts: list[dict]) -> list[dict]:
    """Scrape recent tweets from specific handles."""
    handles = [a["handle"] for a in accounts if a["platform"] == "twitter"]
    if not handles or not APIFY_TOKEN:
        return []
    try:
        client = ApifyClient(APIFY_TOKEN)
        run = client.actor("CJdippxWmn9uRfooo").call(run_input={
            "twitterHandles": handles,
            "maxItems": 15,
            "sort": "Latest",
        })
        results = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        items = _parse_twitter_results(results)
        _mark_scraped({"twitter": handles})
        logger.info(f"[Twitter] {len(items)} tweets (accounts: {handles})")
        return items
    except Exception as e:
        logger.error(f"[Twitter] account scrape failed: {e}")
        return []


# ──────────────────────────────────────────────
# INSTAGRAM — hashtag search + profile scraping
# ──────────────────────────────────────────────

def _parse_instagram_results(results: list) -> list[dict]:
    items = []
    for r in results:
        posts = r.get("topPosts", []) + r.get("latestPosts", [])
        if not posts:
            # direct item format
            posts = [r] if r.get("url") else []
        for post in posts:
            url = post.get("url", "")
            caption = post.get("caption", "")
            if not url:
                continue
            items.append({
                "source_name": "Instagram",
                "category_slug": "social",
                "title": caption[:120] if caption else f"Instagram post by @{post.get('ownerUsername', '')}",
                "url": url,
                "content": caption,
                "language": "en",
                "published_at": post.get("timestamp"),
                "platform": "instagram",
                "author": post.get("ownerUsername", ""),
                "like_count": post.get("likesCount", 0),
                "comment_count": post.get("commentsCount", 0),
                "share_count": None,
                "view_count": post.get("videoPlayCount", 0),
                "post_type": post.get("type", "post"),
            })
    return items


def scrape_instagram(search_terms: list[str]) -> list[dict]:
    if not APIFY_TOKEN:
        logger.warning("[Instagram] No Apify token — skipping")
        return []
    hashtags = set()
    for term in search_terms:
        for word in term.split():
            if len(word) > 2:
                hashtags.add(word.lower().replace("-", "").replace("/", ""))
    hashtags.update(["tomato", "horticulture", "seedbreeding"])
    hashtags = list(hashtags)[:8]
    try:
        client = ApifyClient(APIFY_TOKEN)
        run = client.actor("apify/instagram-scraper").call(run_input={
            "searchType": "hashtag",
            "search": hashtags[0],
            "searchLimit": len(hashtags),
            "resultsType": "posts",
            "onlyPostsNewerThan": "3 days",
            "resultsLimit": 30,
            "addParentData": False,
        })
        results = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        items = _parse_instagram_results(results)
        logger.info(f"[Instagram] {len(items)} posts (hashtag)")
        return items
    except Exception as e:
        logger.error(f"[Instagram] hashtag scrape failed: {e}")
        return []


def scrape_instagram_accounts(accounts: list[dict]) -> list[dict]:
    """Scrape recent posts from specific Instagram profiles."""
    usernames = [a["handle"] for a in accounts if a["platform"] == "instagram"]
    if not usernames or not APIFY_TOKEN:
        return []
    try:
        client = ApifyClient(APIFY_TOKEN)
        run = client.actor("apify/instagram-scraper").call(run_input={
            "usernames": usernames,
            "resultsType": "posts",
            "resultsLimit": 10,
        })
        results = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        items = _parse_instagram_results(results)
        _mark_scraped({"instagram": usernames})
        logger.info(f"[Instagram] {len(items)} posts (accounts: {usernames})")
        return items
    except Exception as e:
        logger.error(f"[Instagram] account scrape failed: {e}")
        return []


# ──────────────────────────────────────────────
# LINKEDIN — keyword search + company pages
# ──────────────────────────────────────────────

def _parse_linkedin_result(r: dict, lang: str = "en") -> dict | None:
    url = r.get("postUrl", r.get("url", ""))
    text = r.get("text", r.get("content", ""))
    if not url or not text:
        return None
    return {
        "source_name": "LinkedIn",
        "category_slug": "social",
        "title": text[:120],
        "url": url,
        "content": text,
        "language": lang,
        "published_at": r.get("publishedAt", r.get("postedDate")),
        "platform": "linkedin",
        "author": r.get("authorName", r.get("author_name", "")),
        "like_count": r.get("likeCount", r.get("total_reactions", 0)),
        "comment_count": r.get("commentCount", r.get("comments", 0)),
        "share_count": r.get("shareCount", r.get("shares", 0)),
        "view_count": None,
        "post_type": "post",
    }


def scrape_linkedin(search_terms: list[str], languages: list[str] = None) -> list[dict]:
    if not APIFY_TOKEN:
        logger.warning("[LinkedIn] No Apify token — skipping")
        return []
    langs = languages or ["en"]
    all_items = []
    for lang in langs:
        for term in _localise_terms(search_terms, lang):
            try:
                client = ApifyClient(APIFY_TOKEN)
                run = client.actor("apify/linkedin-post-search-scraper").call(run_input={
                    "keywords": term,
                    "datePosted": "past-week",
                    "maxResults": 20,
                    "proxyConfiguration": {"useApifyProxy": True},
                })
                results = list(client.dataset(run["defaultDatasetId"]).iterate_items())
                for r in results:
                    item = _parse_linkedin_result(r, lang)
                    if item:
                        all_items.append(item)
                logger.info(f"[LinkedIn] '{term}' ({lang}): {len(results)} posts")
            except Exception as e:
                logger.error(f"[LinkedIn] keyword scrape failed '{term}' ({lang}): {e}")
    return all_items


def scrape_linkedin_accounts(accounts: list[dict]) -> list[dict]:
    """Scrape recent posts from specific LinkedIn company pages."""
    slugs = [a["handle"] for a in accounts if a["platform"] == "linkedin"]
    if not slugs or not APIFY_TOKEN:
        return []
    company_urls = [f"https://www.linkedin.com/company/{s}" for s in slugs]
    try:
        client = ApifyClient(APIFY_TOKEN)
        run = client.actor("apify/linkedin-company-scraper").call(run_input={
            "companyUrls": company_urls,
            "maxPosts": 10,
            "proxyConfiguration": {"useApifyProxy": True},
        })
        results = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        all_items = []
        for r in results:
            # Company scraper returns posts array inside each result
            for post in r.get("posts", [r]):
                item = _parse_linkedin_result(post)
                if item:
                    # Tag with company display name
                    acct = next((a for a in accounts if a["handle"] in r.get("companyUrl", "")), None)
                    if acct:
                        item["author"] = acct.get("display_name") or item["author"]
                    all_items.append(item)
        _mark_scraped({"linkedin": slugs})
        logger.info(f"[LinkedIn] {len(all_items)} posts (companies: {slugs})")
        return all_items
    except Exception as e:
        logger.error(f"[LinkedIn] company scrape failed: {e}")
        return []


# ──────────────────────────────────────────────
# FACEBOOK — keyword search + page scraping
# ──────────────────────────────────────────────

def _parse_facebook_result(r: dict, lang: str = "en") -> dict | None:
    url = r.get("url", r.get("postUrl", ""))
    text = r.get("text", r.get("message", ""))
    if not url:
        return None
    return {
        "source_name": "Facebook",
        "category_slug": "social",
        "title": text[:120] if text else f"Facebook post ({lang})",
        "url": url,
        "content": text,
        "language": lang,
        "published_at": r.get("time", r.get("timestamp")),
        "platform": "facebook",
        "author": r.get("pageName", r.get("userName", "")),
        "like_count": r.get("likes", 0),
        "comment_count": r.get("comments", 0),
        "share_count": r.get("shares", 0),
        "view_count": None,
        "post_type": "post",
    }


def scrape_facebook(search_terms: list[str], languages: list[str] = None) -> list[dict]:
    if not APIFY_TOKEN:
        logger.warning("[Facebook] No Apify token — skipping")
        return []
    langs = languages or ["en"]
    all_items = []
    for lang in langs:
        localised = _localise_terms(search_terms, lang)
        query = " OR ".join(localised[:3])
        try:
            client = ApifyClient(APIFY_TOKEN)
            run = client.actor("apify/facebook-posts-scraper").call(run_input={
                "searchQueries": [query],
                "maxPostsPerQuery": 20,
                "onlyPostsNewerThan": "7 days",
            })
            results = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            for r in results:
                item = _parse_facebook_result(r, lang)
                if item:
                    all_items.append(item)
            logger.info(f"[Facebook] '{query}' ({lang}): {len(results)} posts")
        except Exception as e:
            logger.error(f"[Facebook] keyword scrape failed ({lang}): {e}")
    return all_items


def scrape_facebook_accounts(accounts: list[dict]) -> list[dict]:
    """Scrape recent posts from specific Facebook pages."""
    fb_accounts = [a for a in accounts if a["platform"] == "facebook"]
    if not fb_accounts or not APIFY_TOKEN:
        return []
    start_urls = [
        {"url": a.get("profile_url") or f"https://www.facebook.com/{a['handle']}"}
        for a in fb_accounts
    ]
    try:
        client = ApifyClient(APIFY_TOKEN)
        run = client.actor("apify/facebook-posts-scraper").call(run_input={
            "startUrls": start_urls,
            "maxPostsPerPage": 10,
            "onlyPostsNewerThan": "7 days",
        })
        results = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        items = [item for r in results if (item := _parse_facebook_result(r)) is not None]
        _mark_scraped({"facebook": [a["handle"] for a in fb_accounts]})
        logger.info(f"[Facebook] {len(items)} posts (pages)")
        return items
    except Exception as e:
        logger.error(f"[Facebook] page scrape failed: {e}")
        return []


# ──────────────────────────────────────────────
# TIKTOK — keyword + profile scraping
# ──────────────────────────────────────────────

def _parse_tiktok_result(r: dict, lang: str = "en") -> dict | None:
    url = r.get("webVideoUrl", r.get("url", ""))
    text = r.get("text", r.get("desc", ""))
    if not url:
        return None
    return {
        "source_name": "TikTok",
        "category_slug": "social",
        "title": text[:120] if text else f"TikTok video ({lang})",
        "url": url,
        "content": text,
        "language": lang,
        "published_at": r.get("createTimeISO", r.get("createTime")),
        "platform": "tiktok",
        "author": r.get("authorMeta", {}).get("name", r.get("author", "")),
        "like_count": r.get("diggCount", r.get("stats", {}).get("diggCount", 0)),
        "comment_count": r.get("commentCount", r.get("stats", {}).get("commentCount", 0)),
        "share_count": r.get("shareCount", r.get("stats", {}).get("shareCount", 0)),
        "view_count": r.get("playCount", r.get("stats", {}).get("playCount", 0)),
        "post_type": "video",
    }


def scrape_tiktok(search_terms: list[str], languages: list[str] = None) -> list[dict]:
    if not APIFY_TOKEN:
        logger.warning("[TikTok] No Apify token — skipping")
        return []
    langs = languages or ["en"]
    all_items = []
    for lang in langs:
        for term in _localise_terms(search_terms, lang)[:2]:
            try:
                client = ApifyClient(APIFY_TOKEN)
                run = client.actor("clockworks/free-tiktok-scraper").call(run_input={
                    "hashtags": [term.replace(" ", "")],
                    "searchQueries": [term],
                    "maxResults": 20,
                    "scrapeType": "search",
                })
                results = list(client.dataset(run["defaultDatasetId"]).iterate_items())
                for r in results:
                    item = _parse_tiktok_result(r, lang)
                    if item:
                        all_items.append(item)
                logger.info(f"[TikTok] '{term}' ({lang}): {len(results)} videos")
            except Exception as e:
                logger.error(f"[TikTok] keyword scrape failed '{term}' ({lang}): {e}")
    return all_items


def scrape_tiktok_accounts(accounts: list[dict]) -> list[dict]:
    """Scrape recent videos from specific TikTok profiles."""
    profiles = [a["handle"] for a in accounts if a["platform"] == "tiktok"]
    if not profiles or not APIFY_TOKEN:
        return []
    try:
        client = ApifyClient(APIFY_TOKEN)
        run = client.actor("clockworks/free-tiktok-scraper").call(run_input={
            "profiles": profiles,
            "resultsPerPage": 10,
            "scrapeType": "user",
        })
        results = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        items = [item for r in results if (item := _parse_tiktok_result(r)) is not None]
        _mark_scraped({"tiktok": profiles})
        logger.info(f"[TikTok] {len(items)} videos (profiles: {profiles})")
        return items
    except Exception as e:
        logger.error(f"[TikTok] profile scrape failed: {e}")
        return []


# ──────────────────────────────────────────────
# ORCHESTRATOR
# ──────────────────────────────────────────────

def run_social_scrape(
    search_terms: list[str],
    languages: list[str] = None,
    platforms: list[str] = None,
    time_filter: str = "week",   # was "day" — changed for 3-day cadence
    mode: str = "both",          # "keywords" | "accounts" | "both"
) -> list[dict]:
    """
    Run all enabled social media scrapers. Returns combined results.
    mode="both" runs keyword search AND specific account/profile scraping.
    """
    if platforms is None:
        platforms = ["reddit", "twitter", "instagram", "linkedin", "facebook", "tiktok"]

    all_items = []

    # ── Keyword mode ───────────────────────────────────────────────────────────
    if mode in ("keywords", "both"):
        if "reddit" in platforms:
            # Pull watched Reddit subs from DB to include alongside defaults
            reddit_accounts = load_watched_accounts("reddit")
            extra_subs = [a["handle"] for a in reddit_accounts]
            all_items.extend(scrape_reddit(search_terms, time_filter=time_filter,
                                           extra_subreddits=extra_subs))
        if "twitter" in platforms:
            all_items.extend(scrape_twitter(search_terms, languages))
        if "instagram" in platforms:
            all_items.extend(scrape_instagram(search_terms))
        if "linkedin" in platforms:
            all_items.extend(scrape_linkedin(search_terms, languages))
        if "facebook" in platforms:
            all_items.extend(scrape_facebook(search_terms, languages))
        if "tiktok" in platforms:
            all_items.extend(scrape_tiktok(search_terms, languages))

    # ── Account/profile mode ───────────────────────────────────────────────────
    if mode in ("accounts", "both"):
        watched = load_watched_accounts()
        if watched:
            if "twitter" in platforms:
                tw = [a for a in watched if a["platform"] == "twitter"]
                if tw:
                    all_items.extend(scrape_twitter_accounts(tw))
            if "linkedin" in platforms:
                li = [a for a in watched if a["platform"] == "linkedin"]
                if li:
                    all_items.extend(scrape_linkedin_accounts(li))
            if "instagram" in platforms:
                ig = [a for a in watched if a["platform"] == "instagram"]
                if ig:
                    all_items.extend(scrape_instagram_accounts(ig))
            if "facebook" in platforms:
                fb = [a for a in watched if a["platform"] == "facebook"]
                if fb:
                    all_items.extend(scrape_facebook_accounts(fb))
            if "tiktok" in platforms:
                tt = [a for a in watched if a["platform"] == "tiktok"]
                if tt:
                    all_items.extend(scrape_tiktok_accounts(tt))
        else:
            logger.info("[Social] No watched accounts found in DB — skipping account mode")

    logger.info(f"[Social] Total: {len(all_items)} items across {len(platforms)} platforms (mode={mode})")
    return all_items
