"""
Apify Scraper — Layer 3
For JS-heavy or anti-bot protected sites that RSS/HTML can't handle.
Uses apify/web-scraper actor with rotating proxies.
"""
import os
from apify_client import ApifyClient
from loguru import logger

APIFY_TOKEN = os.environ.get("APIFY_API_TOKEN", "")


def _get_client() -> ApifyClient:
    if not APIFY_TOKEN:
        raise RuntimeError("APIFY_API_TOKEN not set")
    return ApifyClient(APIFY_TOKEN)


def scrape_apify_web(source: dict, search_terms: list[str] = None) -> list[dict]:
    """
    Scrape a single source using Apify web-scraper actor.
    Falls back gracefully on any error.
    """
    url = source.get("url")
    actor = source.get("apify_actor") or "apify/web-scraper"
    if not url:
        return []

    logger.info(f"[Apify] Scraping {source['name']} with actor {actor}")

    try:
        client = _get_client()

        run_input = {
            "startUrls": [{"url": url}],
            "maxCrawlPages": 15,
            "maxCrawlDepth": 1,
            "pageFunction": """
async function pageFunction(context) {
    const { request, log } = context;
    const items = [];
    const selectors = [
        'article h2 a', 'article h3 a', '.post-title a', '.entry-title a',
        '.news-title a', 'h2.title a', '.article-title a', 'h3 a', 'h2 a'
    ];
    for (const sel of selectors) {
        const els = document.querySelectorAll(sel);
        if (els.length === 0) continue;
        for (const el of els) {
            const href = el.getAttribute('href');
            const title = (el.textContent || '').trim();
            if (href && title && title.length > 5) {
                items.push({
                    url: href.startsWith('http') ? href : new URL(href, request.url).href,
                    title: title,
                    source: request.url
                });
            }
        }
        if (items.length > 0) break;
    }
    return items;
}
""",
            "proxyConfiguration": {"useApifyProxy": True},
        }

        run = client.actor(actor).call(run_input=run_input)
        results = list(client.dataset(run["defaultDatasetId"]).iterate_items())

        items = []
        for r in results:
            item_url = r.get("url", "")
            title = r.get("title", "")
            if not item_url or not title:
                continue
            items.append({
                "source_name": source["name"],
                "category_slug": source.get("category_slug", "news"),
                "title": title,
                "url": item_url,
                "content": r.get("text", ""),
                "language": source.get("language", "en"),
                "published_at": None,
                "platform": None,
            })

        logger.info(f"[Apify] {source['name']}: {len(items)} items")
        return items

    except Exception as e:
        logger.error(f"[Apify] Failed for {source['name']}: {e}")
        return []


def scrape_apify_content_crawler(source: dict) -> list[dict]:
    """
    Layer 5: Apify website-content-crawler actor.
    AI-powered crawl — renders JS, returns clean Markdown text per article.
    More expensive (~$0.10/run) but highest success rate for blocked/complex sites.
    """
    url = source.get("url")
    if not url:
        return []

    logger.info(f"[Apify-CC] Crawling {source['name']} with website-content-crawler")

    try:
        client = _get_client()

        run_input = {
            "startUrls": [{"url": url}],
            "maxCrawlPages": 20,
            "maxCrawlDepth": 1,
            "crawlerType": "playwright:firefox",
            "removeCookieWarnings": True,
            "clickElementsCssSelector": "[aria-label='Accept cookies']",
        }

        run = client.actor("apify/website-content-crawler").call(run_input=run_input)
        results = list(client.dataset(run["defaultDatasetId"]).iterate_items())

        items = []
        for r in results:
            item_url = r.get("url", "")
            title = r.get("metadata", {}).get("title", "") or r.get("title", "")
            content = r.get("markdown", "") or r.get("text", "")
            if not item_url or not title or len(title) < 5:
                continue
            items.append({
                "source_name": source["name"],
                "category_slug": source.get("category_slug", "news"),
                "title": title,
                "url": item_url,
                "content": content[:3000],
                "language": source.get("language", "en"),
                "published_at": None,
                "platform": None,
            })

        logger.info(f"[Apify-CC] {source['name']}: {len(items)} items")
        return items

    except Exception as e:
        logger.error(f"[Apify-CC] Failed for {source['name']}: {e}")
        return []


def scrape_all_apify(sources: list[dict]) -> list[dict]:
    """Scrape all Apify sources."""
    all_items = []
    for source in sources:
        if source.get("scrape_type") != "apify":
            continue
        items = scrape_apify_web(source)
        all_items.extend(items)
    return all_items
