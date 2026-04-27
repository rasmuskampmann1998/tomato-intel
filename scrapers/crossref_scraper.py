"""
Crossref API Scraper
Fetches academic paper metadata from the Crossref REST API.
Free, official, no scraping needed — works for any journal with an ISSN.

Replaces HTML/Playwright scraping for MDPI and Oxford Academic journals
which block all automated HTTP clients.

Usage (standalone):
    python scrapers/crossref_scraper.py --issn 2311-7524 --rows 20
"""
import httpx
import sys
from datetime import datetime
from pathlib import Path
from loguru import logger

CROSSREF_API = "https://api.crossref.org/works"
# Polite pool: include email so Crossref gives priority API access
CROSSREF_HEADERS = {
    "User-Agent": "TomatoIntelBot/1.0 (mailto:info@digi-tal.dk)"
}

# ISSN mapping — add journals here as needed
JOURNAL_ISSNS = {
    "MDPI Horticulturae":                     "2311-7524",
    "Oxford Academic — Horticulture Research": "2052-7276",
    "Horticulture Advances":                  "2516-6101",
    "MDPI Agronomy":                          "2073-4395",
}


def _parse_date(date_parts: list) -> str | None:
    """Convert Crossref date-parts [[year, month, day]] to ISO string."""
    try:
        parts = date_parts[0] if date_parts else []
        if len(parts) >= 3:
            return f"{parts[0]}-{parts[1]:02d}-{parts[2]:02d}T00:00:00+00:00"
        if len(parts) == 2:
            return f"{parts[0]}-{parts[1]:02d}-01T00:00:00+00:00"
        if len(parts) == 1:
            return f"{parts[0]}-01-01T00:00:00+00:00"
    except (IndexError, TypeError):
        pass
    return None


def scrape_crossref(source: dict, rows: int = 25) -> list[dict]:
    """
    Fetch recent papers from Crossref for a journal source.
    Source must have a name matching JOURNAL_ISSNS, or provide issn directly.
    Returns list of scraped item dicts.
    """
    name = source.get("name", "")
    issn = source.get("crossref_issn") or JOURNAL_ISSNS.get(name)

    if not issn:
        logger.debug(f"[Crossref] No ISSN configured for {name!r} — skipping")
        return []

    logger.info(f"[Crossref] Fetching {name} (ISSN {issn}), rows={rows}")

    try:
        resp = httpx.get(
            CROSSREF_API,
            params={
                "filter": f"issn:{issn}",
                "sort": "published",
                "order": "desc",
                "rows": rows,
                "select": "title,DOI,published,abstract,author,URL",
            },
            headers=CROSSREF_HEADERS,
            timeout=20,
        )
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"[Crossref] Request failed for {name}: {e}")
        return []

    data = resp.json()
    raw_items = data.get("message", {}).get("items", [])

    items = []
    for r in raw_items:
        title = (r.get("title") or [""])[0].strip()
        doi = r.get("DOI", "")
        url = r.get("URL") or (f"https://doi.org/{doi}" if doi else "")
        abstract = r.get("abstract", "") or ""
        # Strip JATS XML tags from abstract (e.g. <jats:p>)
        import re
        abstract = re.sub(r"<[^>]+>", " ", abstract).strip()
        abstract = " ".join(abstract.split())[:2000]

        pub_date = _parse_date(r.get("published", {}).get("date-parts", []))

        if not title or not url:
            continue

        items.append({
            "source_name": name,
            "category_slug": source.get("category_slug", "news"),
            "title": title,
            "url": url,
            "content": abstract,
            "language": source.get("language", "en"),
            "published_at": pub_date,
            "platform": None,
        })

    logger.info(f"[Crossref] {name}: {len(items)} papers")
    return items


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--issn", required=True, help="Journal ISSN e.g. 2311-7524")
    parser.add_argument("--rows", type=int, default=10)
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).parent.parent))
    source = {"name": "Test", "crossref_issn": args.issn, "category_slug": "news", "language": "en"}
    items = scrape_crossref(source, rows=args.rows)
    for item in items:
        print(f"\n{item['title'][:80]}")
        print(f"URL: {item['url']}")
        print(f"Date: {item['published_at']}")
        if item['content']:
            print(f"Abstract: {item['content'][:200]}...")
