"""
Scraper Orchestrator
Loads sources from config/sources.json, runs the right scraper per source,
saves results to Supabase scraped_items, updates source scrape_status.

Usage:
    python scrapers/run_scrapers.py                         # all categories
    python scrapers/run_scrapers.py --categories news       # specific categories
    python scrapers/run_scrapers.py --dry-run               # print items, don't save
"""
import argparse
import json
import os
import sys
from pathlib import Path
from loguru import logger

# Add parent dir to path so we can import db/
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.client import supabase
from scrapers.rss_scraper import scrape_rss
from scrapers.html_scraper import scrape_html
from scrapers.apify_scraper import scrape_apify_web
from scrapers.patent_epo import search_epo
from scrapers.patent_uspto import search_uspto
from scrapers.patent_cnipa import search_cnipa, search_ip_india
from scrapers.social_scraper import run_social_scrape

CONFIG_PATH = Path(__file__).parent.parent / "config" / "sources.json"

# Default tomato search terms used for patent/social scraping
DEFAULT_SEARCH_TERMS = [
    "tomato", "tomato ToBRFV", "tomato TYLCV", "tomato breeding",
    "tomato seed", "tomato patent", "tomato disease resistance"
]


def load_sources_from_config(categories_filter: list[str] = None) -> dict:
    """Load sources from config/sources.json, optionally filtered by category."""
    with open(CONFIG_PATH) as f:
        config = json.load(f)

    sources = config.get("categories", {})
    if categories_filter:
        sources = {k: v for k, v in sources.items() if k in categories_filter}
    return sources


def load_sources_from_db(categories_filter: list[str] = None) -> list[dict]:
    """Load active sources from Supabase (preferred over config after initial seed)."""
    try:
        query = supabase.table("sources").select("*, categories(slug)").eq("active", True)
        if categories_filter:
            # Filter by category slug via join
            cat_resp = supabase.table("categories").select("id,slug").execute()
            cat_ids = [c["id"] for c in cat_resp.data if c["slug"] in categories_filter]
            if cat_ids:
                query = query.in_("category_id", cat_ids)
        resp = query.execute()
        sources = resp.data or []
        # Attach category_slug to each source
        for s in sources:
            if s.get("categories"):
                s["category_slug"] = s["categories"]["slug"]
        return sources
    except Exception as e:
        logger.warning(f"Could not load sources from DB ({e}), falling back to config")
        return []


def save_items(items: list[dict], dry_run: bool = False) -> int:
    """Upsert scraped items into Supabase. Returns count saved."""
    if not items:
        return 0

    if dry_run:
        for item in items[:5]:
            logger.info(f"  [DRY RUN] {item.get('title', '')[:80]} — {item.get('url', '')[:60]}")
        logger.info(f"  [DRY RUN] {len(items)} total items (not saved)")
        return len(items)

    # Strip internal-only fields before upserting
    rows = []
    for item in items:
        row = {k: v for k, v in item.items() if k != "source_name"}
        rows.append(row)

    try:
        # Upsert with url as conflict key (dedup)
        resp = supabase.table("scraped_items").upsert(
            rows, on_conflict="url", ignore_duplicates=True
        ).execute()
        saved = len(resp.data) if resp.data else 0
        logger.info(f"Saved {saved} new items (of {len(rows)} total)")
        return saved
    except Exception as e:
        logger.error(f"Failed to save items: {e}")
        return 0


def update_source_status(source_id: str, status: str):
    """Update sources.scrape_status and last_scraped_at."""
    try:
        supabase.table("sources").update({
            "scrape_status": status,
            "last_scraped_at": "now()",
        }).eq("id", source_id).execute()
    except Exception as e:
        logger.warning(f"Could not update source status: {e}")


def run_category(category_slug: str, sources: list[dict], search_terms: list[str], dry_run: bool) -> int:
    """Run all scrapers for a category. Returns total items saved."""
    total = 0

    if category_slug == "social":
        items = run_social_scrape(search_terms)
        total += save_items(items, dry_run)
        return total

    if category_slug == "patents":
        # USPTO (free, always)
        items = search_uspto(search_terms)
        total += save_items(items, dry_run)

        # EPO (if credentials set)
        items = search_epo(search_terms)
        total += save_items(items, dry_run)

        # CNIPA + IP India via Apify
        items = search_cnipa(search_terms)
        total += save_items(items, dry_run)
        items = search_ip_india(search_terms)
        total += save_items(items, dry_run)

        return total

    # News / competitors / regulations / crops / genetics — use layered scrapers
    for source in sources:
        source_id = source.get("id", "")
        scrape_type = source.get("scrape_type", "html")
        items = []

        try:
            if scrape_type == "rss":
                items = scrape_rss(source)
                if not items:
                    logger.info(f"RSS empty for {source['name']}, trying HTML fallback")
                    items = scrape_html(source)
                if not items:
                    logger.info(f"HTML empty for {source['name']}, trying Apify fallback")
                    items = scrape_apify_web(source)

            elif scrape_type == "html":
                items = scrape_html(source)
                if not items:
                    logger.info(f"HTML empty for {source['name']}, trying Apify fallback")
                    items = scrape_apify_web(source)

            elif scrape_type == "apify":
                items = scrape_apify_web(source)

            status = "ok" if items else "empty"
        except Exception as e:
            logger.error(f"Scraper failed for {source.get('name')}: {e}")
            status = "failed"
            items = []

        if source_id:
            update_source_status(source_id, status)

        saved = save_items(items, dry_run)
        total += saved

    return total


def trigger_profile_matching(dry_run: bool = False):
    """Call the Supabase match_items_to_profiles() function after scraping."""
    if dry_run:
        logger.info("[DRY RUN] Skipping profile matching")
        return
    try:
        supabase.rpc("match_items_to_profiles").execute()
        logger.info("Profile matching complete")
    except Exception as e:
        logger.warning(f"Profile matching failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Run tomato intel scrapers")
    parser.add_argument("--categories", help="Comma-separated category slugs (e.g. news,patents)")
    parser.add_argument("--dry-run", action="store_true", help="Print items, don't save to DB")
    parser.add_argument("--search-terms", help="Override default search terms (comma-separated)")
    args = parser.parse_args()

    categories_filter = [c.strip() for c in args.categories.split(",")] if args.categories else None
    dry_run = args.dry_run
    search_terms = [t.strip() for t in args.search_terms.split(",")] if args.search_terms else DEFAULT_SEARCH_TERMS

    logger.info(f"Starting scrape | categories={categories_filter or 'all'} | dry_run={dry_run}")

    # Try DB first, fall back to config
    db_sources = load_sources_from_db(categories_filter)
    config_sources = load_sources_from_config(categories_filter)

    # Build dict: category_slug → list of sources
    if db_sources:
        sources_by_category: dict[str, list] = {}
        for s in db_sources:
            slug = s.get("category_slug", "news")
            sources_by_category.setdefault(slug, []).append(s)
    else:
        sources_by_category = {slug: data.get("sources", []) for slug, data in config_sources.items()}

    grand_total = 0
    for slug, sources in sources_by_category.items():
        logger.info(f"--- Category: {slug} ({len(sources)} sources) ---")
        total = run_category(slug, sources, search_terms, dry_run)
        grand_total += total
        logger.info(f"Category {slug}: {total} items")

    trigger_profile_matching(dry_run)
    logger.info(f"Done. Total items saved: {grand_total}")


if __name__ == "__main__":
    main()
