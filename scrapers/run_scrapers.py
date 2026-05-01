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
from scrapers.playwright_scraper import scrape_playwright
from scrapers.zenrows_scraper import scrape_zenrows
from scrapers.apify_scraper import scrape_apify_web, scrape_apify_content_crawler
from scrapers.claude_scraper import scrape_claude
from scrapers.crossref_scraper import scrape_crossref, JOURNAL_ISSNS
from scrapers.crawl4ai_scraper import scrape_crawl4ai
from scrapers.article_direct_scraper import scrape_article_direct
from scrapers.article_enricher import enrich_items
from scrapers.patent_epo import search_epo
from scrapers.patent_uspto import search_uspto
from scrapers.patent_cnipa import search_cnipa, search_ip_india
from scrapers.social_scraper import run_social_scrape
from scrapers.serp_scraper import run_search_discovery_for_category, CATEGORY_DEFAULTS

CONFIG_PATH = Path(__file__).parent.parent / "config" / "sources.json"

# Sources that need full article body text fetched after link extraction
FETCH_CONTENT_SOURCES = {"Hortidaily", "Seed World", "Krishijagran (Indian Agriculture)"}

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


def load_global_search_profiles() -> list[dict]:
    """
    Load demo/global search profiles (user_id IS NULL) from Supabase.
    These are seeded by fix_rls_and_seed.sql and define per-category search terms + languages.
    Falls back to CATEGORY_DEFAULTS if DB returns nothing (e.g. RLS fix not yet applied).
    """
    try:
        resp = (
            supabase.table("search_profiles")
            .select("*, categories(slug)")
            .is_("user_id", "null")
            .execute()
        )
        profiles = resp.data or []
        if profiles:
            # Flatten category slug
            for p in profiles:
                if p.get("categories"):
                    p["category_slug"] = p["categories"]["slug"]
            return profiles
    except Exception as e:
        logger.warning(f"Could not load global search profiles ({e}), using defaults")
    return []


def run_search_discovery(categories_filter: list[str] = None, dry_run: bool = False) -> int:
    """
    Run SerpAPI Google News search discovery for all categories.
    Uses global search_profiles (user_id=NULL) from DB; falls back to CATEGORY_DEFAULTS.
    Runs in parallel with URL scraping — results saved to scraped_items with source_id=NULL.
    Returns total items saved.
    """
    profiles = load_global_search_profiles()
    total = 0

    # Build per-category (terms, languages) from DB profiles
    profile_map: dict[str, tuple[list, list]] = {}
    for p in profiles:
        slug = p.get("category_slug", "")
        if not slug:
            continue
        terms = p.get("search_terms", [])
        langs = p.get("languages", ["en"])
        if slug not in profile_map:
            profile_map[slug] = (terms, langs)
        else:
            # Merge terms/langs from multiple profiles per category
            existing_terms, existing_langs = profile_map[slug]
            merged_terms = list(dict.fromkeys(existing_terms + terms))
            merged_langs = list(dict.fromkeys(existing_langs + langs))
            profile_map[slug] = (merged_terms, merged_langs)

    # Fall back to hardcoded defaults for any category not in DB
    for slug, (default_terms, default_langs) in CATEGORY_DEFAULTS.items():
        if slug not in profile_map:
            profile_map[slug] = (default_terms, default_langs)

    # Apply category filter
    if categories_filter:
        profile_map = {k: v for k, v in profile_map.items() if k in categories_filter}

    logger.info(f"[SearchDiscovery] Running for {len(profile_map)} categories")

    for slug, (terms, langs) in profile_map.items():
        logger.info(f"[SearchDiscovery] {slug}: {len(terms)} terms × {len(langs)} languages")
        items = run_search_discovery_for_category(slug, terms, langs, dry_run=dry_run)
        if not dry_run:
            saved = save_items(items, dry_run)
            total += saved
            logger.info(f"[SearchDiscovery] {slug}: saved {saved} new items")
        else:
            total += len(items)

    return total


def run_category(category_slug: str, sources: list[dict], search_terms: list[str], dry_run: bool) -> int:
    """Run all scrapers for a category. Returns total items saved."""
    total = 0

    if category_slug == "social":
        # Pass languages from global search profile so Apify actors get non-English queries too
        social_profile = load_global_search_profiles()
        social_langs = next(
            (p.get("languages", ["en"]) for p in social_profile if p.get("category_slug") == "social"),
            CATEGORY_DEFAULTS.get("social", ([], ["en"]))[1],
        )
        items = run_social_scrape(search_terms, languages=social_langs)
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

        # Update scrape status for all patent sources
        patent_status = "ok" if total > 0 else "empty"
        for source in sources:
            if source.get("id"):
                update_source_status(source["id"], patent_status)

        return total

    # News / competitors / regulations / crops / genetics
    # 7-layer fallback: Crossref → RSS → HTML → Playwright → ZenRows → Claude → Apify
    for source in sources:
        source_id = source.get("id", "")
        scrape_type = source.get("scrape_type", "html")
        items = []

        try:
            # Layer 0: Crossref API (free, official) for academic journals with known ISSN
            # Runs before RSS/HTML — avoids wasting time on bot-blocked journal sites
            if source.get("name") in JOURNAL_ISSNS or source.get("crossref_issn"):
                items = scrape_crossref(source)
                if items:
                    logger.info(f"Crossref succeeded for {source['name']}: {len(items)} papers")

            # Layer 0.5: article_direct — source URL is the article itself (not a listing page)
            if not items and scrape_type == "article_direct":
                items = scrape_article_direct(source)

            # Layer 1: RSS
            if not items and scrape_type == "rss":
                items = scrape_rss(source)

            # Layer 2: httpx + BeautifulSoup (HTML)
            if not items and scrape_type in ("rss", "html"):
                if scrape_type == "rss":
                    logger.info(f"RSS→HTML fallback for {source['name']}")
                items = scrape_html(source)

            # Layer 3: Playwright (headless Chromium, free, handles JS rendering)
            if not items:
                logger.info(f"HTML→Playwright fallback for {source['name']}")
                items = scrape_playwright(source)

            # Layer 3.5: Crawl4AI (anti-bot headless, free, handles 403 + JS sites)
            if not items:
                logger.info(f"Playwright→Crawl4AI fallback for {source['name']}")
                items = scrape_crawl4ai(source)

            # Layer 4: ZenRows (anti-bot bypass + JS rendering, ~$0.001/req)
            if not items:
                logger.info(f"Crawl4AI→ZenRows fallback for {source['name']}")
                items = scrape_zenrows(source)

            is_required = source.get("is_required", False)

            # Layer 5: Claude Haiku AI scraper (~$0.0002/page)
            # Cheaper than Apify — run first for required non-apify sources
            if not items and is_required and scrape_type != "apify":
                logger.info(f"ZenRows→Claude fallback for {source['name']}")
                items = scrape_claude(source)

            # Layer 6a: Apify web-scraper (rotating proxies, ~$0.05/run)
            # For explicit apify-typed sources or required sources still returning 0
            if not items and scrape_type == "apify":
                items = scrape_apify_web(source)
            elif not items and is_required:
                logger.info(f"Claude→Apify fallback for {source['name']}")
                items = scrape_apify_web(source)

            # Layer 6b: Apify website-content-crawler (AI-powered, last resort, ~$0.10/run)
            # Only for required sources
            if not items and is_required:
                logger.info(f"Apify→ContentCrawler fallback for {source['name']}")
                items = scrape_apify_content_crawler(source)

            # Article content enrichment (fetch full body text for designated sources)
            if items and (source.get("fetch_content") or source.get("name") in FETCH_CONTENT_SOURCES):
                items = enrich_items(items, delay=0.3)

            # Stamp source_id on every item so the FK is saved to DB
            if items and source_id:
                for item in items:
                    item.setdefault("source_id", source_id)

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
    parser.add_argument("--no-search-discovery", action="store_true", help="Skip SerpAPI search discovery")
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

    # Phase 2: SerpAPI multi-language search discovery (runs after URL scraping)
    if not args.no_search_discovery:
        logger.info("--- Search Discovery (SerpAPI multi-language) ---")
        discovery_total = run_search_discovery(categories_filter, dry_run)
        grand_total += discovery_total
        logger.info(f"Search discovery: {discovery_total} items")

    trigger_profile_matching(dry_run)
    logger.info(f"Done. Total items saved: {grand_total}")


if __name__ == "__main__":
    main()
