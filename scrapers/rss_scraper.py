"""
RSS Scraper — Layer 1
Fetches articles from RSS/Atom feeds using feedparser.
Falls back to reporting 'empty' so the orchestrator can escalate to html_scraper.
"""
import feedparser
import httpx
from datetime import datetime, timezone
from typing import Optional
from loguru import logger
from dateutil import parser as dateparser


def _parse_date(entry: dict) -> Optional[datetime]:
    for field in ("published", "updated", "created"):
        raw = entry.get(field)
        if raw:
            try:
                return dateparser.parse(raw).replace(tzinfo=timezone.utc)
            except Exception:
                continue
    return None


def _clean_text(text: str) -> str:
    if not text:
        return ""
    # Strip basic HTML tags from summaries
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())[:2000]


def scrape_rss(source: dict) -> list[dict]:
    """
    Scrape a single RSS source.
    Returns list of item dicts ready for scraped_items table.
    """
    rss_url = source.get("rss_url")
    if not rss_url:
        logger.warning(f"No RSS URL for {source['name']} — skipping")
        return []

    logger.info(f"[RSS] Fetching {source['name']} from {rss_url}")

    try:
        # feedparser handles redirects and encoding automatically
        feed = feedparser.parse(rss_url, request_headers={"User-Agent": "TomatoIntelBot/1.0"})
    except Exception as e:
        logger.error(f"[RSS] Failed to fetch {rss_url}: {e}")
        return []

    if feed.bozo and not feed.entries:
        logger.warning(f"[RSS] Malformed feed or no entries from {rss_url}")
        return []

    items = []
    for entry in feed.entries:
        url = entry.get("link") or entry.get("id")
        if not url:
            continue

        title = entry.get("title", "").strip()
        summary = _clean_text(
            entry.get("summary") or entry.get("description") or ""
        )
        published_at = _parse_date(entry)

        items.append({
            "source_name": source["name"],
            "category_slug": source.get("category_slug", "news"),
            "title": title,
            "url": url,
            "content": summary,
            "language": source.get("language", "en"),
            "published_at": published_at.isoformat() if published_at else None,
            "platform": None,
        })

    logger.info(f"[RSS] {source['name']}: {len(items)} items")
    return items


def scrape_all_rss(sources: list[dict]) -> list[dict]:
    """Scrape all RSS sources in the provided list."""
    all_items = []
    for source in sources:
        if source.get("scrape_type") != "rss":
            continue
        items = scrape_rss(source)
        all_items.extend(items)
    return all_items
