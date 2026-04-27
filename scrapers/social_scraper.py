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

def scrape_linkedin(search_terms: list[str]) -> list[dict]:
    """
    Scrape LinkedIn posts via Apify.
    Replaces utils/linkedin_fetcher.py which used Selenium (too fragile).
    """
    if not APIFY_TOKEN:
        logger.warning("[LinkedIn] No Apify token — skipping")
        return []

    all_items = []

    for term in search_terms:
        try:
            client = ApifyClient(APIFY_TOKEN)
            run_input = {
                "keywords": term,
                "datePosted": "past-week",
                "maxResults": 25,
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
                    "language": "en",
                    "published_at": r.get("publishedAt", r.get("postedDate")),
                    "platform": "linkedin",
                    "author": r.get("authorName", r.get("author_name", "")),
                    "like_count": r.get("likeCount", r.get("total_reactions", 0)),
                    "comment_count": r.get("commentCount", r.get("comments", 0)),
                    "share_count": r.get("shareCount", r.get("shares", 0)),
                    "view_count": None,
                    "post_type": "post",
                })

            logger.info(f"[LinkedIn] '{term}': {len(results)} posts")

        except Exception as e:
            logger.error(f"[LinkedIn] Apify scrape failed for '{term}': {e}")

    return all_items


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
        platforms = ["reddit", "twitter", "instagram", "linkedin"]

    all_items = []

    if "reddit" in platforms:
        all_items.extend(scrape_reddit(search_terms, time_filter=time_filter))
    if "twitter" in platforms:
        all_items.extend(scrape_twitter(search_terms, languages))
    if "instagram" in platforms:
        all_items.extend(scrape_instagram(search_terms))
    if "linkedin" in platforms:
        all_items.extend(scrape_linkedin(search_terms))

    logger.info(f"[Social] Total: {len(all_items)} items across {len(platforms)} platforms")
    return all_items
