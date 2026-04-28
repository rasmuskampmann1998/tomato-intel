"""
firecrawl_scraper.py — Firecrawl scraper (free tier: 100 req/month)

Uses the Firecrawl API to scrape a URL and return structured article links.
Firecrawl handles JS rendering, CAPTCHAs, and returns clean markdown + links.

Requires: FIRECRAWL_API_TOKEN env var
Free tier: 100 requests/month at app.firecrawl.dev
"""

import os
import httpx
from loguru import logger

FIRECRAWL_KEY = os.environ.get("FIRECRAWL_API_TOKEN", "")
FIRECRAWL_BASE = "https://api.firecrawl.dev/v1"


def scrape_firecrawl(source: dict) -> list[dict]:
    """
    Fetch a page via Firecrawl and extract article links from the response.
    Returns list of {title, url, content, language, published_at, source_name, category_slug, platform}.
    """
    if not FIRECRAWL_KEY:
        logger.debug("[firecrawl] FIRECRAWL_API_TOKEN not set — skipping")
        return []

    url = source.get("url", "")
    if not url:
        return []

    try:
        resp = httpx.post(
            f"{FIRECRAWL_BASE}/scrape",
            headers={
                "Authorization": f"Bearer {FIRECRAWL_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "url": url,
                "formats": ["links"],
                "onlyMainContent": True,
            },
            timeout=35,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.debug(f"[firecrawl] error for {url}: {e}")
        return []

    links = (data.get("data") or {}).get("links") or []
    items = []
    seen_urls = set()

    for link in links:
        href = (link.get("href") or link if isinstance(link, str) else "").strip()
        text = (link.get("text") or link.get("title") or "").strip() if isinstance(link, dict) else ""

        if not href.startswith("http") or href == url or href in seen_urls:
            continue
        if len(text) < 10:
            continue

        seen_urls.add(href)
        items.append({
            "title": text,
            "url": href,
            "content": "",
            "language": source.get("language", "en"),
            "published_at": None,
            "source_name": source.get("name", ""),
            "category_slug": source.get("category_slug", ""),
            "platform": None,
        })

        if len(items) >= 20:
            break

    logger.debug(f"[firecrawl] extracted {len(items)} article links from {url}")
    return items
