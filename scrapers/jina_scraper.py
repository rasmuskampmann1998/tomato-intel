"""
jina_scraper.py — Jina AI Reader scraper (free, no API key required)

Fetches any URL via https://r.jina.ai/{url}, which returns clean
LLM-friendly markdown including all hyperlinks. Extracts article
links from the markdown using regex.

Works for JS-rendered sites without Playwright overhead.
"""

import re
import httpx
from loguru import logger

JINA_BASE = "https://r.jina.ai"
JINA_HEADERS = {
    "Accept": "text/plain",
    "X-Return-Format": "markdown",
}


def scrape_jina(source: dict) -> list[dict]:
    """
    Fetch a page via Jina Reader and extract article links from returned markdown.
    Returns list of {title, url, content, language, published_at, source_name, category_slug, platform}.
    """
    url = source.get("url", "")
    if not url:
        return []

    try:
        with httpx.Client(timeout=25, follow_redirects=True) as c:
            r = c.get(f"{JINA_BASE}/{url}", headers=JINA_HEADERS)
            r.raise_for_status()
            markdown = r.text
    except Exception as e:
        logger.debug(f"[jina] fetch failed for {url}: {e}")
        return []

    items = []
    seen_urls = set()

    # Extract [Title](https://...) markdown links
    for match in re.finditer(r'\[([^\]]{10,300})\]\((https?://[^\)\s]+)\)', markdown):
        title = match.group(1).strip()
        link = match.group(2).strip()

        # Skip if same domain root (navigation links, not articles)
        if link == url or link in seen_urls:
            continue
        # Skip obvious non-article links
        if any(skip in link for skip in ('#', 'javascript:', 'mailto:', '/tag/', '/category/', '/author/')):
            continue

        seen_urls.add(link)
        items.append({
            "title": title,
            "url": link,
            "content": "",
            "language": source.get("language", "en"),
            "published_at": None,
            "source_name": source.get("name", ""),
            "category_slug": source.get("category_slug", ""),
            "platform": None,
        })

        if len(items) >= 20:
            break

    logger.debug(f"[jina] extracted {len(items)} article links from {url}")
    return items
