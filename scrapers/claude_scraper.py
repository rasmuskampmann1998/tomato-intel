"""
Claude AI Scraper — Layer 6 (last resort)
Uses Claude Haiku to extract article titles + URLs from raw HTML.
No CSS selectors needed — works on any page layout.
Fetches HTML via httpx first, falls back to Playwright for JS-heavy sites.

Cost: ~$0.0002 per page (Haiku input ~10k tokens)
Use when: all other layers return 0 items.
"""
import os
import json
import httpx
import asyncio
from pathlib import Path
from typing import Optional
from loguru import logger
from dotenv import load_dotenv
import anthropic

load_dotenv()

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
HAIKU_MODEL = "claude-haiku-4-5-20251001"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Max HTML chars to send to Claude — keeps cost low
MAX_HTML_CHARS = 40_000


def _get_client() -> anthropic.Anthropic:
    if not CLAUDE_API_KEY:
        raise RuntimeError("CLAUDE_API_KEY not set")
    return anthropic.Anthropic(api_key=CLAUDE_API_KEY)


def _fetch_html_httpx(url: str) -> Optional[str]:
    try:
        with httpx.Client(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception as e:
        logger.debug(f"[Claude] httpx failed for {url}: {e}")
        return None


def _fetch_html_playwright(url: str) -> Optional[str]:
    try:
        from scrapers.playwright_scraper import _fetch_html_with_playwright
        return asyncio.run(_fetch_html_with_playwright(url))
    except Exception as e:
        logger.debug(f"[Claude] Playwright failed for {url}: {e}")
        return None


def _extract_with_claude(html: str, page_url: str) -> list[dict]:
    """
    Send truncated HTML to Claude Haiku.
    Returns list of {title, url} dicts or [].
    """
    client = _get_client()

    # Strip head/scripts/styles to surface body content before truncating
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "head", "nav", "footer", "iframe", "noscript"]):
        tag.decompose()
    # Use the cleaned body text as the HTML snippet
    clean_html = str(soup.body or soup)[:MAX_HTML_CHARS]
    html_snippet = clean_html

    prompt = f"""You are extracting article links from a web page.

Page URL: {page_url}

HTML content (may be truncated):
{html_snippet}

Extract all article/news item links from this page. For each article, return:
- title: the article title text
- url: the full absolute URL (resolve relative URLs using the page URL above)

Rules:
- Only include items that look like articles, news posts, or research papers
- Skip navigation links, ads, pagination, cookie notices, social media links
- If a URL is relative (starts with /), prepend the domain from the page URL
- Return at least 5 items if available

Respond ONLY with a JSON array, no other text:
[{{"title": "...", "url": "..."}}]

If no articles found, return: []"""

    try:
        resp = client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = resp.content[0].text.strip()

        # Strip markdown code block if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()

        items = json.loads(raw)
        if not isinstance(items, list):
            return []
        return items

    except json.JSONDecodeError as e:
        logger.warning(f"[Claude] JSON parse error: {e}")
        return []
    except Exception as e:
        logger.error(f"[Claude] API call failed: {e}")
        return []


def scrape_claude(source: dict) -> list[dict]:
    """
    Scrape a source using Claude Haiku to extract article links from HTML.
    Tries httpx first, falls back to Playwright for JS-heavy pages.
    Returns list of scraped item dicts.
    """
    url = source.get("url")
    if not url:
        return []

    if not CLAUDE_API_KEY:
        logger.warning("[Claude] CLAUDE_API_KEY not set — skipping AI scraper")
        return []

    logger.info(f"[Claude] AI-scraping {source['name']} at {url}")

    # Try httpx first (fast, free)
    html = _fetch_html_httpx(url)

    # Fall back to Playwright if httpx fails or page is JS-rendered
    if not html:
        logger.info(f"[Claude] httpx failed, trying Playwright for {source['name']}")
        html = _fetch_html_playwright(url)

    if not html:
        logger.warning(f"[Claude] Could not fetch HTML for {source['name']}")
        return []

    logger.debug(f"[Claude] HTML: {len(html)} raw chars fetched, sending to Haiku")

    raw_items = _extract_with_claude(html, url)
    if not raw_items:
        logger.warning(f"[Claude] No items extracted for {source['name']}")
        return []

    # Normalise into standard scraped item format
    from urllib.parse import urljoin, urlparse
    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

    items = []
    for r in raw_items:
        title = (r.get("title") or "").strip()
        item_url = (r.get("url") or "").strip()

        if not title or not item_url or len(title) < 5:
            continue

        # Make absolute
        if item_url.startswith("//"):
            item_url = "https:" + item_url
        elif item_url.startswith("/"):
            item_url = base + item_url
        elif not item_url.startswith("http"):
            item_url = urljoin(url, item_url)

        items.append({
            "source_name": source["name"],
            "category_slug": source.get("category_slug", "news"),
            "title": title,
            "url": item_url,
            "content": "",
            "language": source.get("language", "en"),
            "published_at": None,
            "platform": None,
        })

    logger.info(f"[Claude] {source['name']}: {len(items)} items extracted by Haiku")
    return items
