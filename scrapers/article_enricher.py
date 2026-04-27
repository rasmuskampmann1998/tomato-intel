"""
Article Enricher
Fetches full article body text for scraped items that have a URL but no content.
Runs after the main scraper pass — enriches items in-place before DB save.

Usage (standalone):
    python scrapers/article_enricher.py --source "Hortidaily" --limit 20
"""
import sys
import time
import argparse
from pathlib import Path
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Per-domain CSS selector for article body
CONTENT_SELECTORS = {
    "hortidaily.com":        ["article p", ".article-body", ".article-content"],
    "seedworld.com":         [".entry-content", "article .content", "article p"],
    "krishijagran.com":      [".article-body", ".article-content", "article p"],
    "theconversation.com":   [".article-body", ".content-body", "article p"],
    "apnews.com":            [".RichTextStoryBody", "article p"],
    "hortweek.com":          [".article-body", ".article__body", "article p"],
    "gartnertidende.dk":     [".article-body", "article p"],
    "gfactueel.nl":          [".article-body", "article p"],
    "greentech.nl":          [".article-content", "article p"],
}

GENERIC_CONTENT_SELECTORS = [
    ".article-body", ".article-content", ".post-content",
    ".entry-content", ".story-body", ".content-body",
    "article .content", "article p",
]

MAX_CONTENT_CHARS = 4000


def _get_domain(url: str) -> str:
    from urllib.parse import urlparse
    return urlparse(url).netloc.replace("www.", "")


def fetch_article_content(url: str) -> Optional[str]:
    """
    Fetch full article text from a URL.
    Returns None if content can't be extracted.
    """
    domain = _get_domain(url)
    selectors = CONTENT_SELECTORS.get(domain, []) + GENERIC_CONTENT_SELECTORS

    try:
        with httpx.Client(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
    except Exception as e:
        logger.debug(f"[Enricher] Failed to fetch {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    for selector in selectors:
        elements = soup.select(selector)
        if not elements:
            continue
        text = " ".join(el.get_text(separator=" ", strip=True) for el in elements)
        text = " ".join(text.split())  # normalize whitespace
        if len(text) > 100:
            return text[:MAX_CONTENT_CHARS]

    return None


def enrich_items(items: list[dict], delay: float = 0.5) -> list[dict]:
    """
    Enrich a list of scraped items with full article content.
    Modifies items in-place; returns the same list.
    Only enriches items where content is empty.
    """
    to_enrich = [i for i in items if not i.get("content")]
    logger.info(f"[Enricher] Enriching {len(to_enrich)} items (of {len(items)} total)")

    for idx, item in enumerate(to_enrich):
        url = item.get("url", "")
        if not url:
            continue
        content = fetch_article_content(url)
        if content:
            item["content"] = content
            logger.debug(f"[Enricher] [{idx+1}/{len(to_enrich)}] {item.get('title','')[:60]}: {len(content)} chars")
        else:
            logger.debug(f"[Enricher] [{idx+1}/{len(to_enrich)}] No content for {url[:60]}")

        if delay and idx < len(to_enrich) - 1:
            time.sleep(delay)

    enriched = sum(1 for i in to_enrich if i.get("content"))
    logger.info(f"[Enricher] Enriched {enriched}/{len(to_enrich)} items")
    return items


def main():
    parser = argparse.ArgumentParser(description="Enrich scraped items with full article content")
    parser.add_argument("--source", help="Source name to enrich (e.g. 'Hortidaily')")
    parser.add_argument("--limit", type=int, default=20, help="Max articles to enrich")
    args = parser.parse_args()

    from db.client import supabase
    from scrapers.html_scraper import scrape_html

    if args.source == "Hortidaily":
        source = {
            "name": "Hortidaily",
            "url": "https://www.hortidaily.com",
            "category_slug": "news",
            "language": "en",
        }
        items = scrape_html(source)[:args.limit]
        enriched = enrich_items(items, delay=0.5)
        print(f"\n{'='*70}")
        print(f"Hortidaily — {len(enriched)} articles with full content")
        print('='*70)
        for item in enriched[:5]:
            print(f"\nTitle:   {item['title']}")
            print(f"URL:     {item['url']}")
            print(f"Content: {item.get('content','(none)')[:300]}...")
    else:
        logger.error("Use --source Hortidaily (or extend for other sources)")


if __name__ == "__main__":
    main()
