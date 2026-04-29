"""
Social Media Scraper — Reddit, Twitter/X, Instagram, LinkedIn
- Reddit: Direct PRAW (official API, free) — replaces fragile LangChain wrapper
- Twitter/X: Apify actor CJdippxWmn9uRfooo (existing, working)
- Instagram: Apify apify/instagram-scraper (existing, working)
- LinkedIn: Apify apify/linkedin-post-search-scraper (replaces Selenium)
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

# Core "tomato" translations for building non-English search queries
TOMATO_TRANSLATIONS = {
    "zh": "番茄",
    "ja": "トマト",
    "hi": "टमाटर",
    "es": "tomate",
    "ar": "طماطم",
    "tr": "domates",
    "nl": "tomaat",
    "da": "tomat",
    "de": "Tomate",
    "fr": "tomate",
}


def _localise_terms(search_terms: list[str], lang: str) -> list[str]:
    """Replace 'tomato' (case-insensitive) in each term with the target-language word."""
    if lang == "en" or lang not in TOMATO_TRANSLATIONS:
        return search_terms
    local_word = TOMATO_TRANSLATIONS[lang]
    localised = []
    for term in search_terms:
        localised.append(term.lower().replace("tomato", local_word))
    return localised


# ──────────────────────────────────────────────
# REDDIT — Direct PRAW (no LangChain wrapper)
# ──────────────────────────────────────────────

def scrape_reddit(search_terms: list[str], time_filter: str = "day") -> list[dict]:
    """
    Search Reddit using PRAW official API.
    Much more reliable than the LangChain wrapper which used fragile regex parsing.
    """
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

    all_items = []
    seen_urls = set()

    for term in search_terms:
        for subreddit_name in REDDIT_SUBREDDITS:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                results = subreddit.search(term, sort="relevance", time_filter=time_filter, limit=15)

                for post in results:
                    url = f"https://www.reddit.com{post.permalink}"
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    created_dt = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
                    content = f"r/{subreddit_name} | Score: {post.score} | Comments: {post.num_comments}\n\n{post.selftext[:500]}"

                    all_items.append({
                        "source_name": "Reddit",
                        "category_slug": "social",
                        "title": post.title,
                        "url": url,
                        "content": content,
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
                logger.warning(f"[Reddit] r/{subreddit_name} search '{term}' failed: {e}")

    logger.info(f"[Reddit] Total: {len(all_items)} posts")
    return all_items


# ──────────────────────────────────────────────
# TWITTER / X — Apify (existing working code)
# ──────────────────────────────────────────────

def scrape_twitter(search_terms: list[str], languages: list[str] = None) -> list[dict]:
    """
    Scrape Twitter/X via Apify actor CJdippxWmn9uRfooo.
    Reuses logic from utils/twitter_fetcher.py with updated API key.
    """
    if not APIFY_TOKEN:
        logger.warning("[Twitter] No Apify token — skipping")
        return []

    now_utc = datetime.utcnow()
    since = (now_utc - timedelta(hours=24)).strftime("%Y-%m-%d_%H:%M:%S_UTC")
    until = now_utc.strftime("%Y-%m-%d_%H:%M:%S_UTC")

    try:
        client = ApifyClient(APIFY_TOKEN)
        run_input = {
            "searchTerms": search_terms,
            "sort": "Latest",
            "maxItems": 50,
            "minimumRetweets": 2,
            "minimumFavorites": 5,
            "since": since,
            "until": until,
            "queryType": "Latest",
        }

        run = client.actor("CJdippxWmn9uRfooo").call(run_input=run_input)
        results = list(client.dataset(run["defaultDatasetId"]).iterate_items())

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

        logger.info(f"[Twitter] {len(items)} tweets")
        return items

    except Exception as e:
        logger.error(f"[Twitter] Apify scrape failed: {e}")
        return []


# ──────────────────────────────────────────────
# INSTAGRAM — Apify (existing working code)
# ──────────────────────────────────────────────

def scrape_instagram(search_terms: list[str]) -> list[dict]:
    """
    Scrape Instagram hashtags via Apify apify/instagram-scraper.
    Reuses logic from utils/instagram_fetcher.py.
    Converts search_terms to hashtags: "tomato ToBRFV" → ["tomato", "tobRFV"]
    """
    if not APIFY_TOKEN:
        logger.warning("[Instagram] No Apify token — skipping")
        return []

    # Convert terms to hashtags
    hashtags = set()
    for term in search_terms:
        for word in term.split():
            if len(word) > 2:
                hashtags.add(word.lower().replace("-", "").replace("/", ""))
    hashtags.update(["tomato", "horticulture", "seedbreeding"])
    hashtags = list(hashtags)[:8]  # cap to control Apify costs

    all_items = []

    try:
        client = ApifyClient(APIFY_TOKEN)
        run_input = {
            "searchType": "hashtag",
            "search": hashtags[0],  # primary hashtag
            "searchLimit": len(hashtags),
            "resultsType": "posts",
            "onlyPostsNewerThan": "2 days",
            "resultsLimit": 30,
            "addParentData": False,
        }

        run = client.actor("apify/instagram-scraper").call(run_input=run_input)
        results = list(client.dataset(run["defaultDatasetId"]).iterate_items())

        for r in results:
            posts = r.get("topPosts", []) + r.get("latestPosts", [])
            for post in posts:
                url = post.get("url", "")
                caption = post.get("caption", "")
                if not url:
                    continue
                all_items.append({
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

        logger.info(f"[Instagram] {len(all_items)} posts")
        return all_items

    except Exception as e:
        logger.error(f"[Instagram] Apify scrape failed: {e}")
        return []


# ──────────────────────────────────────────────
# LINKEDIN — Apify (replaces broken Selenium)
# ──────────────────────────────────────────────

def scrape_linkedin(search_terms: list[str], languages: list[str] = None) -> list[dict]:
    """
    Scrape LinkedIn posts via Apify.
    Sends one query per language using localised search terms.
    """
    if not APIFY_TOKEN:
        logger.warning("[LinkedIn] No Apify token — skipping")
        return []

    langs = languages or ["en"]
    all_items = []

    for lang in langs:
        localised = _localise_terms(search_terms, lang)
        for term in localised:
            try:
                client = ApifyClient(APIFY_TOKEN)
                run_input = {
                    "keywords": term,
                    "datePosted": "past-week",
                    "maxResults": 20,
                    "proxyConfiguration": {"useApifyProxy": True},
                }

                run = client.actor("apify/linkedin-post-search-scraper").call(run_input=run_input)
                results = list(client.dataset(run["defaultDatasetId"]).iterate_items())

                for r in results:
                    url = r.get("postUrl", r.get("url", ""))
                    text = r.get("text", r.get("content", ""))
                    if not url or not text:
                        continue
                    all_items.append({
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
                    })

                logger.info(f"[LinkedIn] '{term}' ({lang}): {len(results)} posts")

            except Exception as e:
                logger.error(f"[LinkedIn] Apify scrape failed for '{term}' ({lang}): {e}")

    return all_items


def scrape_facebook(search_terms: list[str], languages: list[str] = None) -> list[dict]:
    """
    Scrape Facebook posts via Apify apify/facebook-posts-scraper.
    Sends localised queries per language.
    """
    if not APIFY_TOKEN:
        logger.warning("[Facebook] No Apify token — skipping")
        return []

    langs = languages or ["en"]
    all_items = []

    for lang in langs:
        localised = _localise_terms(search_terms, lang)
        query = " OR ".join(localised[:3])  # combine top 3 terms as OR query
        try:
            client = ApifyClient(APIFY_TOKEN)
            run_input = {
                "searchQueries": [query],
                "maxPostsPerQuery": 20,
                "onlyPostsNewerThan": "7 days",
            }

            run = client.actor("apify/facebook-posts-scraper").call(run_input=run_input)
            results = list(client.dataset(run["defaultDatasetId"]).iterate_items())

            for r in results:
                url = r.get("url", r.get("postUrl", ""))
                text = r.get("text", r.get("message", ""))
                if not url:
                    continue
                all_items.append({
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
                })

            logger.info(f"[Facebook] '{query}' ({lang}): {len(results)} posts")

        except Exception as e:
            logger.error(f"[Facebook] Apify scrape failed ({lang}): {e}")

    return all_items


def scrape_tiktok(search_terms: list[str], languages: list[str] = None) -> list[dict]:
    """
    Scrape TikTok posts via Apify clockworks/free-tiktok-scraper.
    Sends one keyword per language.
    """
    if not APIFY_TOKEN:
        logger.warning("[TikTok] No Apify token — skipping")
        return []

    langs = languages or ["en"]
    all_items = []

    for lang in langs:
        localised = _localise_terms(search_terms, lang)
        for term in localised[:2]:  # cap to 2 terms per language to limit Apify cost
            try:
                client = ApifyClient(APIFY_TOKEN)
                run_input = {
                    "hashtags": [term.replace(" ", "")],
                    "resultsPerPage": 20,
                    "scrapeType": "search",
                    "searchQueries": [term],
                    "maxResults": 20,
                }

                run = client.actor("clockworks/free-tiktok-scraper").call(run_input=run_input)
                results = list(client.dataset(run["defaultDatasetId"]).iterate_items())

                for r in results:
                    url = r.get("webVideoUrl", r.get("url", ""))
                    text = r.get("text", r.get("desc", ""))
                    if not url:
                        continue
                    all_items.append({
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
                    })

                logger.info(f"[TikTok] '{term}' ({lang}): {len(results)} videos")

            except Exception as e:
                logger.error(f"[TikTok] Apify scrape failed for '{term}' ({lang}): {e}")


# ──────────────────────────────────────────────
# ORCHESTRATOR
# ──────────────────────────────────────────────

def run_social_scrape(
    search_terms: list[str],
    languages: list[str] = None,
    platforms: list[str] = None,
    time_filter: str = "day",
) -> list[dict]:
    """Run all enabled social media scrapers and return combined results."""
    if platforms is None:
        platforms = ["reddit", "twitter", "instagram", "linkedin", "facebook", "tiktok"]

    all_items = []

    if "reddit" in platforms:
        # Reddit PRAW is English-only (no official non-English subreddit coverage)
        all_items.extend(scrape_reddit(search_terms, time_filter=time_filter))
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

    logger.info(f"[Social] Total: {len(all_items)} items across {len(platforms)} platforms")
    return all_items
