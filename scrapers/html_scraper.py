"""
HTML Scraper — Layer 2
Direct HTTP + BeautifulSoup for sites without RSS.
Extracts article titles and links from article list pages.
Falls back silently so orchestrator can escalate to Apify.
"""
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from typing import Optional
from loguru import logger
import re

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Per-domain CSS selectors — override source-level css_selector if needed
DOMAIN_SELECTORS = {
    "hortiadvisor.com":       [".news-item h3 a", ".article-title a", "h3 a"],
    "hortidaily.com":         ["a[href*='/article/']"],
    "gfactueel.nl":           [".nieuws-item__title a", ".article-header a", ".nieuws-item a", ".article-item h3 a", "h2 a", "h3 a"],
    "greentech.nl":           [".article__title a", ".news-item__title a", ".article-teaser h3 a", ".news-card a", "h2 a"],
    "gartnertidende.dk":      [".teaser__title a", ".article-title a", "article h2 a", "article h3 a", ".post-title a"],
    "veggiesfrommexico.com":  [".post-title a", "article h2 a", "h3 a"],
    "ahsgardening.org":       [".post-title a", "article h2 a", "h3 a"],
    "revistas.chapingo.mx":   [".article-title a", ".titulo a", "h3 a"],
    "rijkzwaan.com":          ["article h3 a", ".press-release-title a", "h3 a"],
    "enzazaden.com":          [".news-item h3 a", "article h3 a", "h3 a"],
    "bejo.com":               ["h2.teaser__title a", "article h2 a", "h3 a"],
    "deruiterseeds.com":      ["article h3 a", ".news-item h3 a", "h3 a"],
    "syngenta.com":           [".news-card h3 a", "article h3 a", "h3 a"],
    "apnews.com":             ["h3.PagePromo-title a", "[data-key='card-headline'] a", ".PagePromo-title a", "h2 a"],
    "hortweek.com":           [".article-list-item h3 a", ".teaser__title a", "article h2 a", "h3 a"],
    "academic.oup.com":       [".sri-title a", ".article-link a", "h3.title a", "h3 a"],
}

# Generic fallback selectors tried in order
GENERIC_SELECTORS = [
    "article h2 a", "article h3 a",
    ".post-title a", ".entry-title a",
    "h2.title a", "h3.title a",
    ".news-title a", ".article-title a",
    ".item-title a",
]


def _get_selectors(url: str, css_selector: Optional[str]) -> list[str]:
    """Return ordered list of selectors to try for this URL."""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.replace("www.", "")
    selectors = []
    if css_selector:
        selectors.append(css_selector)
    domain_specific = DOMAIN_SELECTORS.get(domain, [])
    selectors.extend(s for s in domain_specific if s not in selectors)
    selectors.extend(s for s in GENERIC_SELECTORS if s not in selectors)
    return selectors


def _extract_date(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    """Try to find a publication date in common locations."""
    for selector in ["time[datetime]", "meta[property='article:published_time']",
                     ".date", ".post-date", "span.date", ".published"]:
        el = soup.select_one(selector)
        if el:
            dt = el.get("datetime") or el.get("content") or el.get_text(strip=True)
            if dt:
                return dt[:50]
    return None


def scrape_html(source: dict) -> list[dict]:
    """
    Scrape a single HTML source's article list page.
    Returns list of item dicts. Returns [] on any failure.
    """
    url = source.get("url")
    if not url:
        return []

    css_selector = source.get("css_selector")
    selectors = _get_selectors(url, css_selector)

    logger.info(f"[HTML] Fetching {source['name']} from {url}")

    try:
        with httpx.Client(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.warning(f"[HTML] HTTP {e.response.status_code} for {url}")
        return []
    except Exception as e:
        if "CERTIFICATE" in str(e).upper() or "SSL" in str(e).upper():
            logger.warning(f"[HTML] SSL error for {url}, retrying without verification")
            try:
                with httpx.Client(headers=HEADERS, timeout=20, follow_redirects=True, verify=False) as client:
                    resp = client.get(url)
                    resp.raise_for_status()
            except Exception as e2:
                logger.error(f"[HTML] SSL bypass also failed for {url}: {e2}")
                return []
        else:
            logger.error(f"[HTML] Request failed for {url}: {e}")
            return []

    soup = BeautifulSoup(resp.text, "lxml")
    items = []

    for selector in selectors:
        links = soup.select(selector)
        if not links:
            continue

        logger.debug(f"[HTML] {source['name']}: matched selector '{selector}' — {len(links)} links")

        for link in links[:30]:  # cap at 30 articles per source
            href = link.get("href", "").strip()
            if not href or href.startswith("#") or href.startswith("javascript"):
                continue

            # Make absolute URL
            if href.startswith("http"):
                article_url = href
            else:
                from urllib.parse import urljoin
                article_url = urljoin(url, href)

            title = link.get_text(strip=True)
            if not title or len(title) < 5:
                title = link.get("title", "").strip()

            items.append({
                "source_name": source["name"],
                "category_slug": source.get("category_slug", "news"),
                "title": title,
                "url": article_url,
                "content": "",  # enriched later by Claude if needed
                "language": source.get("language", "en"),
                "published_at": None,
                "platform": None,
            })

        if items:
            break  # found working selector, stop trying

    if not items:
        logger.warning(f"[HTML] No items extracted from {url} — all selectors failed")

    logger.info(f"[HTML] {source['name']}: {len(items)} items")
    return items


def scrape_all_html(sources: list[dict]) -> list[dict]:
    """Scrape all HTML sources in the provided list."""
    all_items = []
    for source in sources:
        if source.get("scrape_type") != "html":
            continue
        items = scrape_html(source)
        all_items.extend(items)
    return all_items
