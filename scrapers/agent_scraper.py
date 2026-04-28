"""
agent_scraper.py — Agentic URL analysis loop

Tries 8 strategies in cost order until one returns ≥1 article.
Yields status dicts for SSE streaming to the frontend.

Strategy order (cheapest first):
  1. RSS detection      — free  (parse <link> tags in HTML)
  2. Claude Sonnet      — ~$0.003 (page structure analysis → config)
  3. HTML/Playwright    — free  (test Claude's suggested config)
  4. Jina AI Reader     — free  (r.jina.ai renders JS → markdown → extract links)
  5. ZenRows            — ~$0.001 (anti-bot residential proxies → HTML → CSS selector)
  6. Firecrawl          — free tier (JS render → structured links, 100 req/month)
  7. Claude Haiku       — ~$0.0002 (direct LLM extraction from raw HTML)
  8. Apify              — ~$0.05  (rotating proxies, last resort)

Usage (from source_routes.py):
  async for status in analyze_url(url, category_slug, user_id):
      yield f"data: {json.dumps(status)}\\n\\n"

Each status dict:
  {step, strategy, status: "running"|"success"|"failed", items_found, config, message}

Final dict always has strategy="complete" + terminal status.
"""

import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import AsyncGenerator, Optional

import httpx
from bs4 import BeautifulSoup
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
SONNET_MODEL = "claude-sonnet-4-5"
MAX_HTML_CHARS = 40_000
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# ── Sync helpers ──────────────────────────────────────────────────────────────

def _fetch_html(url: str) -> Optional[str]:
    try:
        with httpx.Client(headers=HEADERS, timeout=20, follow_redirects=True) as c:
            r = c.get(url)
            r.raise_for_status()
            return r.text
    except Exception as e:
        logger.debug(f"[agent] httpx fetch failed for {url}: {e}")
        return None


def _find_rss_url(html: str, page_url: str) -> Optional[str]:
    from urllib.parse import urljoin
    soup = BeautifulSoup(html, "lxml")
    for link in soup.find_all("link", type=re.compile(r"application/(rss|atom)\+xml")):
        href = (link.get("href") or "").strip()
        if href:
            return href if href.startswith("http") else urljoin(page_url, href)
    return None


def _test_rss(rss_url: str) -> list[dict]:
    import feedparser
    try:
        feed = feedparser.parse(rss_url, request_headers={"User-Agent": "TomatoIntelBot/1.0"})
        items = []
        for entry in (feed.entries or [])[:5]:
            url = entry.get("link") or entry.get("id", "")
            title = (entry.get("title") or "").strip()
            if url and title:
                items.append({"title": title, "url": url})
        return items
    except Exception:
        return []


def _claude_analyze_html(html: str, page_url: str) -> dict:
    """Send page HTML to Claude Sonnet. Returns JSON scraper config."""
    import anthropic
    if not CLAUDE_API_KEY:
        return {}
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
        tag.decompose()
    clean = str(soup.body or soup)[:MAX_HTML_CHARS]

    prompt = f"""You are configuring a web scraper for an agriculture intelligence platform.
Analyze this HTML page and return a JSON scraper configuration.

Page URL: {page_url}

HTML (truncated):
{clean}

Check the <head> section for RSS/Atom <link rel=alternate> tags first.

Return ONLY valid JSON, no other text:
{{
  "scrape_type": "rss" | "html" | "playwright",
  "rss_url": "<full RSS URL if found in HTML head, else null>",
  "css_selector": "<CSS selector for article <a> tags if scrape_type=html, else null>",
  "language": "<ISO 639-1 language code>",
  "reasoning": "<one sentence>"
}}

Rules:
- If you see <link rel="alternate" type="application/rss+xml" href="...">, use scrape_type=rss
- For css_selector target <a> elements: e.g. "article h2 a", ".post-title a", "h3.entry-title a"
- If body text is very sparse (JS-rendered app), use scrape_type=playwright"""

    try:
        resp = client.messages.create(
            model=SONNET_MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"[agent] Claude Sonnet analysis failed: {e}")
        return {}


def _test_html_scrape(url: str, css_selector: str) -> list[dict]:
    from scrapers.html_scraper import scrape_html
    return scrape_html({"name": "agent-test", "url": url,
                        "css_selector": css_selector, "scrape_type": "html", "language": "en"})


def _test_playwright_scrape(url: str, css_selector: str) -> list[dict]:
    from scrapers.playwright_scraper import scrape_playwright
    return scrape_playwright({"name": "agent-test", "url": url,
                              "css_selector": css_selector, "scrape_type": "playwright", "language": "en"})


def _test_jina(url: str) -> list[dict]:
    from scrapers.jina_scraper import scrape_jina
    return scrape_jina({"name": "agent-test", "url": url, "language": "en"})


def _test_zenrows(url: str, css_selector: str) -> list[dict]:
    from scrapers.zenrows_scraper import scrape_zenrows
    return scrape_zenrows({"name": "agent-test", "url": url,
                           "css_selector": css_selector, "scrape_type": "zenrows", "language": "en"})


def _test_firecrawl(url: str) -> list[dict]:
    from scrapers.firecrawl_scraper import scrape_firecrawl
    return scrape_firecrawl({"name": "agent-test", "url": url, "language": "en"})


def _test_apify(url: str) -> list[dict]:
    from scrapers.apify_scraper import scrape_apify_web
    return scrape_apify_web({"name": "agent-test", "url": url, "scrape_type": "apify", "language": "en"})


def _status(step: int, strategy: str, status: str, items: int,
            config: Optional[dict], message: str) -> dict:
    return {"step": step, "strategy": strategy, "status": status,
            "items_found": items, "config": config, "message": message}


# ── Agentic loop ──────────────────────────────────────────────────────────────

async def analyze_url(
    url: str,
    category_slug: str,
    user_id: str,
) -> AsyncGenerator[dict, None]:
    """
    Async generator — yields status dicts, one per strategy attempt.
    Stops on first strategy that returns ≥1 item.
    Final yield always has strategy="complete" with terminal status.
    """
    loop = asyncio.get_event_loop()
    html: Optional[str] = None
    claude_cfg: dict = {}

    # ── Strategy 1: RSS detection ─────────────────────────────
    yield _status(1, "RSS detection", "running", 0, None, "Fetching page...")

    html = await loop.run_in_executor(None, _fetch_html, url)
    if not html:
        yield _status(1, "RSS detection", "failed", 0, None,
                      "Could not fetch page — check the URL and try again.")
        yield _status(0, "complete", "failed", 0, None, "All strategies failed.")
        return

    rss_url = await loop.run_in_executor(None, _find_rss_url, html, url)
    if rss_url:
        yield _status(1, "RSS detection", "running", 0, None, f"Found RSS feed: {rss_url} — testing...")
        items = await loop.run_in_executor(None, _test_rss, rss_url)
        if items:
            config = {"scrape_type": "rss", "rss_url": rss_url, "css_selector": None}
            yield _status(1, "RSS detection", "success", len(items), config,
                          f"RSS confirmed — {len(items)} articles found.")
            yield _status(0, "complete", "success", len(items), config, "Source ready to add.")
            return
        yield _status(1, "RSS detection", "failed", 0, None,
                      f"RSS feed found but returned 0 items: {rss_url}")
    else:
        yield _status(1, "RSS detection", "failed", 0, None, "No RSS feed found in page <head>.")

    # ── Strategy 2: Claude Sonnet analysis ───────────────────
    yield _status(2, "Claude analysis", "running", 0, None,
                  "Asking Claude Sonnet to analyse page structure...")

    claude_cfg = await loop.run_in_executor(None, _claude_analyze_html, html, url)
    if not claude_cfg:
        yield _status(2, "Claude analysis", "failed", 0, None,
                      "Claude returned no config — trying fallback strategies.")
    else:
        yield _status(2, "Claude analysis", "running", 0, claude_cfg,
                      f"Claude recommends: {claude_cfg.get('scrape_type')} "
                      f"({claude_cfg.get('reasoning', '')}). Testing...")

        # ── Strategy 3: Test Claude's config ─────────────────
        css = claude_cfg.get("css_selector") or ""
        lang = claude_cfg.get("language", "en")
        scrape_type = claude_cfg.get("scrape_type", "html")

        if scrape_type == "playwright":
            yield _status(3, "Playwright scrape", "running", 0, None,
                          "Running headless Chromium (JS-rendered site)...")
            items = await loop.run_in_executor(None, _test_playwright_scrape, url, css)
        else:
            yield _status(3, "HTML scrape", "running", 0, None,
                          f"Testing HTML scrape with selector: '{css or 'auto'}'...")
            items = await loop.run_in_executor(None, _test_html_scrape, url, css)

        if items:
            winning_scrape_type = "playwright" if scrape_type == "playwright" else "html"
            config = {"scrape_type": winning_scrape_type, "rss_url": None,
                      "css_selector": css or None, "language": lang}
            label = "Playwright" if scrape_type == "playwright" else "HTML"
            yield _status(3, f"{label} scrape", "success", len(items), config,
                          f"{label} scrape succeeded — {len(items)} articles.")
            yield _status(0, "complete", "success", len(items), config, "Source ready to add.")
            return

        label = "Playwright" if scrape_type == "playwright" else "HTML"
        yield _status(3, f"{label} scrape", "failed", 0, None,
                      f"{label} scrape returned 0 items.")

    # ── Strategy 4: Jina AI Reader ────────────────────────────
    yield _status(4, "Jina AI Reader", "running", 0, None,
                  "Trying Jina AI Reader (free JS rendering, no API key needed)...")
    try:
        items = await loop.run_in_executor(None, _test_jina, url)
    except Exception as e:
        logger.warning(f"[agent] Jina error: {e}")
        items = []

    if items:
        config = {"scrape_type": "html", "rss_url": None,
                  "css_selector": None, "language": claude_cfg.get("language", "en")}
        yield _status(4, "Jina AI Reader", "success", len(items), config,
                      f"Jina extracted {len(items)} article links.")
        yield _status(0, "complete", "success", len(items), config, "Source ready to add.")
        return
    yield _status(4, "Jina AI Reader", "failed", 0, None,
                  "Jina returned 0 article links.")

    # ── Strategy 5: ZenRows (anti-bot) ───────────────────────
    css = claude_cfg.get("css_selector") or ""
    yield _status(5, "ZenRows scrape", "running", 0, None,
                  "Trying ZenRows anti-bot scraper (~$0.001, residential proxies)...")
    try:
        items = await loop.run_in_executor(None, _test_zenrows, url, css)
    except Exception as e:
        logger.warning(f"[agent] ZenRows error: {e}")
        items = []

    if items:
        config = {"scrape_type": "html", "rss_url": None,
                  "css_selector": css or None, "language": claude_cfg.get("language", "en")}
        yield _status(5, "ZenRows scrape", "success", len(items), config,
                      f"ZenRows bypassed bot protection — {len(items)} articles.")
        yield _status(0, "complete", "success", len(items), config, "Source ready to add.")
        return
    yield _status(5, "ZenRows scrape", "failed", 0, None,
                  "ZenRows returned 0 items.")

    # ── Strategy 6: Firecrawl ─────────────────────────────────
    yield _status(6, "Firecrawl", "running", 0, None,
                  "Trying Firecrawl (free tier, structured link extraction)...")
    try:
        items = await loop.run_in_executor(None, _test_firecrawl, url)
    except Exception as e:
        logger.warning(f"[agent] Firecrawl error: {e}")
        items = []

    if items:
        config = {"scrape_type": "html", "rss_url": None,
                  "css_selector": None, "language": claude_cfg.get("language", "en")}
        yield _status(6, "Firecrawl", "success", len(items), config,
                      f"Firecrawl extracted {len(items)} article links.")
        yield _status(0, "complete", "success", len(items), config, "Source ready to add.")
        return
    yield _status(6, "Firecrawl", "failed", 0, None,
                  "Firecrawl returned 0 items.")

    # ── Strategy 7: Claude Haiku direct extraction ────────────
    yield _status(7, "Claude Haiku extraction", "running", 0, None,
                  "Trying Claude Haiku direct extraction (~$0.0002)...")
    try:
        from scrapers.claude_scraper import _extract_with_claude
        items = await loop.run_in_executor(None, _extract_with_claude, html, url)
    except Exception as e:
        logger.warning(f"[agent] Haiku extraction error: {e}")
        items = []

    if items:
        config = {"scrape_type": "html", "rss_url": None, "css_selector": None, "language": "en"}
        yield _status(7, "Claude Haiku extraction", "success", len(items), config,
                      f"Claude Haiku extracted {len(items)} articles. Will re-extract each scrape run.")
        yield _status(0, "complete", "success", len(items), config, "Source ready to add.")
        return
    yield _status(7, "Claude Haiku extraction", "failed", 0, None,
                  "Haiku returned 0 items.")

    # ── Strategy 8: Apify web-scraper ────────────────────────
    yield _status(8, "Apify web-scraper", "running", 0, None,
                  "Trying Apify web-scraper (~$0.05, last resort)...")
    try:
        items = await loop.run_in_executor(None, _test_apify, url)
    except Exception as e:
        logger.warning(f"[agent] Apify error: {e}")
        items = []

    if items:
        config = {"scrape_type": "apify", "rss_url": None, "css_selector": None, "language": "en"}
        yield _status(8, "Apify web-scraper", "success", len(items), config,
                      f"Apify succeeded — {len(items)} articles.")
        yield _status(0, "complete", "success", len(items), config, "Source ready to add.")
        return
    yield _status(8, "Apify web-scraper", "failed", 0, None,
                  "Apify returned 0 items.")

    yield _status(0, "complete", "failed", 0, None,
                  "All 8 strategies failed. This site may be behind a hard paywall or aggressive bot-blocking.")
