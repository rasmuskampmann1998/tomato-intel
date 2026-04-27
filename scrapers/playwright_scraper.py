"""
Playwright Scraper — Layer 3
Async headless Chromium for JS-heavy sites that httpx can't render.
Free (local browser), slower than httpx but handles React/Vue/Angular sites.
Falls back gracefully so orchestrator can escalate to ZenRows.
"""
import asyncio
from typing import Optional
from loguru import logger
from urllib.parse import urljoin, urlparse


async def _scrape_with_playwright(url: str, css_selector: str, source_name: str) -> list[dict]:
    """Internal async function — runs Playwright headless Chromium."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("[Playwright] playwright not installed — run: pip install playwright && playwright install chromium")
        return []

    items = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 900},
            )
            page = await context.new_page()

            # Block images/fonts/media to speed up load
            await page.route("**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf,mp4,mp3}", lambda r: r.abort())

            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            # Brief wait for JS rendering
            await page.wait_for_timeout(2000)

            # Try provided selector first, then generic fallbacks
            selectors_to_try = []
            if css_selector:
                selectors_to_try.append(css_selector)
            selectors_to_try.extend([
                "article h2 a", "article h3 a",
                ".post-title a", ".entry-title a",
                "h2.title a", "h3.title a",
                ".news-title a", ".article-title a",
                ".item-title a", "h2 a", "h3 a",
            ])

            for selector in selectors_to_try:
                try:
                    elements = await page.query_selector_all(selector)
                    if not elements:
                        continue
                    logger.debug(f"[Playwright] {source_name}: matched '{selector}' — {len(elements)} links")
                    for el in elements[:30]:
                        href = await el.get_attribute("href") or ""
                        href = href.strip()
                        if not href or href.startswith("#") or href.startswith("javascript"):
                            continue
                        if not href.startswith("http"):
                            href = urljoin(url, href)
                        title = (await el.inner_text()).strip()
                        if not title or len(title) < 5:
                            title = await el.get_attribute("title") or ""
                        if title and len(title) >= 5:
                            items.append(href_title := {"href": href, "title": title})
                    if items:
                        break
                except Exception:
                    continue

        finally:
            await browser.close()

    return items


async def _fetch_html_with_playwright(url: str) -> Optional[str]:
    """Fetch raw HTML from a URL using Playwright. Used by claude_scraper."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            )
            page = await context.new_page()
            await page.route("**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf,mp4,mp3}", lambda r: r.abort())
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            return await page.content()
        except Exception as e:
            logger.debug(f"[Playwright] HTML fetch failed for {url}: {e}")
            return None
        finally:
            await browser.close()


def scrape_playwright(source: dict) -> list[dict]:
    """
    Scrape a single source using headless Playwright.
    Synchronous wrapper around async implementation.
    Returns list of item dicts. Returns [] on any failure.
    """
    url = source.get("url")
    if not url:
        return []

    css_selector = source.get("css_selector", "")
    logger.info(f"[Playwright] Rendering {source['name']} at {url}")

    try:
        raw_items = asyncio.run(_scrape_with_playwright(url, css_selector, source["name"]))
    except Exception as e:
        logger.error(f"[Playwright] Failed for {source['name']}: {e}")
        return []

    items = []
    for r in raw_items:
        items.append({
            "source_name": source["name"],
            "category_slug": source.get("category_slug", "news"),
            "title": r["title"],
            "url": r["href"],
            "content": "",
            "language": source.get("language", "en"),
            "published_at": None,
            "platform": None,
        })

    logger.info(f"[Playwright] {source['name']}: {len(items)} items")
    return items
