"""
ZenRows Scraper — Layer 4
Anti-bot bypass + JS rendering via ZenRows API.
Use for sites that block Playwright (Cloudflare, DataDome, PerimeterX).
Cost: ~$0.001/request with premium proxies.
API key: ZENROWS_API_KEY env var.
"""
import os
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from loguru import logger

ZENROWS_API_KEY = os.environ.get("ZENROWS_API_KEY", "")
ZENROWS_BASE = "https://api.zenrows.com/v1/"

# Generic fallback selectors (same as html_scraper)
GENERIC_SELECTORS = [
    "article h2 a", "article h3 a",
    ".post-title a", ".entry-title a",
    "h2.title a", "h3.title a",
    ".news-title a", ".article-title a",
    ".item-title a",
]


def scrape_zenrows(source: dict, js_render: bool = True, premium_proxy: bool = True) -> list[dict]:
    """
    Scrape a single source via ZenRows API.
    js_render=True: ZenRows renders JS before returning HTML.
    premium_proxy=True: Uses residential proxies (~3× anti-bot success rate).
    Returns [] on any failure.
    """
    if not ZENROWS_API_KEY:
        logger.warning("[ZenRows] ZENROWS_API_KEY not set — skipping")
        return []

    url = source.get("url")
    if not url:
        return []

    logger.info(f"[ZenRows] Fetching {source['name']} (js={js_render}, premium={premium_proxy})")

    params = {
        "apikey": ZENROWS_API_KEY,
        "url": url,
    }
    if js_render:
        params["js_render"] = "true"
    if premium_proxy:
        params["premium_proxy"] = "true"

    try:
        with httpx.Client(timeout=60) as client:
            resp = client.get(ZENROWS_BASE, params=params)
            resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.warning(f"[ZenRows] HTTP {e.response.status_code} for {url}: {e.response.text[:200]}")
        return []
    except Exception as e:
        logger.error(f"[ZenRows] Request failed for {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    css_selector = source.get("css_selector")

    selectors_to_try = []
    if css_selector:
        selectors_to_try.append(css_selector)
    selectors_to_try.extend(GENERIC_SELECTORS)

    items = []
    for selector in selectors_to_try:
        links = soup.select(selector)
        if not links:
            continue

        logger.debug(f"[ZenRows] {source['name']}: matched selector '{selector}' — {len(links)} links")

        for link in links[:30]:
            href = link.get("href", "").strip()
            if not href or href.startswith("#") or href.startswith("javascript"):
                continue
            if not href.startswith("http"):
                href = urljoin(url, href)

            title = link.get_text(strip=True)
            if not title or len(title) < 5:
                title = link.get("title", "").strip()
            if not title or len(title) < 5:
                continue

            items.append({
                "source_name": source["name"],
                "category_slug": source.get("category_slug", "news"),
                "title": title,
                "url": href,
                "content": "",
                "language": source.get("language", "en"),
                "published_at": None,
                "platform": None,
            })

        if items:
            break

    if not items:
        logger.warning(f"[ZenRows] No items extracted from {url}")

    logger.info(f"[ZenRows] {source['name']}: {len(items)} items")
    return items
