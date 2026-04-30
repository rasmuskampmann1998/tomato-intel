"""
Crawl4AI Scraper — Layer 3.5
Headless Chromium with built-in anti-bot bypass (stealth mode).
Used after Playwright fails for JS-heavy or 403-protected sites.
Falls back gracefully so orchestrator can escalate to ZenRows.
"""
import asyncio
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from loguru import logger


def scrape_crawl4ai(source: dict) -> list[dict]:
    """
    Scrape a single source using Crawl4AI headless browser with anti-bot bypass.
    Returns list of item dicts. Returns [] on any failure.
    """
    url = source.get("url")
    if not url:
        return []

    async def _run() -> list[dict]:
        try:
            from crawl4ai import AsyncWebCrawler
        except ImportError:
            logger.error("[Crawl4AI] crawl4ai not installed — run: pip install crawl4ai")
            return []

        items = []
        try:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url)
                if not result.success:
                    logger.warning(f"[Crawl4AI] {source['name']}: crawl returned success=False")
                    return items

                # Strategy 1: CSS selector on rendered HTML
                css = source.get("css_selector", "")
                if css and result.html:
                    soup = BeautifulSoup(result.html, "lxml")
                    links = soup.select(css)
                    logger.debug(f"[Crawl4AI] {source['name']}: CSS '{css}' matched {len(links)} links")
                    for link in links[:30]:
                        href = link.get("href", "").strip()
                        title = link.get_text(strip=True)
                        if not href or not title or len(title) < 5:
                            continue
                        if href.startswith("#") or href.startswith("javascript"):
                            continue
                        if not href.startswith("http"):
                            href = urljoin(url, href)
                        items.append({"title": title, "href": href})

                # Strategy 2: generic selectors on rendered HTML
                if not items and result.html:
                    soup = BeautifulSoup(result.html, "lxml")
                    for sel in ["article h2 a", "article h3 a", "h2 a", "h3 a", ".post-title a", ".entry-title a"]:
                        links = soup.select(sel)
                        if links:
                            logger.debug(f"[Crawl4AI] {source['name']}: generic '{sel}' matched {len(links)}")
                            for link in links[:30]:
                                href = link.get("href", "").strip()
                                title = link.get_text(strip=True)
                                if href and title and len(title) > 5 and not href.startswith("#"):
                                    if not href.startswith("http"):
                                        href = urljoin(url, href)
                                    items.append({"title": title, "href": href})
                            if items:
                                break

                # Strategy 3: parse markdown links (same domain only)
                if not items and result.markdown:
                    base_netloc = urlparse(url).netloc
                    for m in re.finditer(r'\[([^\]]{5,120})\]\((https?://[^\)]+)\)', result.markdown):
                        title, href = m.group(1).strip(), m.group(2)
                        if urlparse(href).netloc == base_netloc:
                            items.append({"title": title, "href": href})
                        if len(items) >= 30:
                            break

        except Exception as e:
            try:
                logger.error(f"[Crawl4AI] {source['name']}: {str(e).encode('ascii', errors='replace').decode()}")
            except Exception:
                logger.error(f"[Crawl4AI] {source['name']}: scrape error")

        return items

    try:
        raw = asyncio.run(_run())
    except Exception as e:
        try:
            logger.error(f"[Crawl4AI] asyncio.run failed for {source['name']}: {str(e).encode('ascii', errors='replace').decode()}")
        except Exception:
            logger.error(f"[Crawl4AI] asyncio.run failed for {source['name']}")
        return []

    out = []
    for r in raw:
        out.append({
            "source_name": source["name"],
            "category_slug": source.get("category_slug", "news"),
            "title": r["title"],
            "url": r["href"],
            "content": "",
            "language": source.get("language", "en"),
            "published_at": None,
            "platform": None,
        })

    logger.info(f"[Crawl4AI] {source['name']}: {len(out)} items")
    return out
