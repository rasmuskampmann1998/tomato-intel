"""
Standalone social media scraper — runs every 3 days via GitHub Actions.
Scrapes both keyword search AND specific watched accounts.

Usage:
    python scrapers/run_social_only.py
    python scrapers/run_social_only.py --mode accounts    # accounts only
    python scrapers/run_social_only.py --mode keywords    # keywords only
    python scrapers/run_social_only.py --platforms twitter,linkedin
    python scrapers/run_social_only.py --dry-run
"""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from scrapers.social_scraper import run_social_scrape
from scrapers.run_scrapers import (
    save_items, trigger_profile_matching, load_global_search_profiles,
    DEFAULT_SEARCH_TERMS, CATEGORY_DEFAULTS,
)


def main():
    parser = argparse.ArgumentParser(description="Social media scraper — runs every 3 days")
    parser.add_argument("--mode", default="both",
                        choices=["keywords", "accounts", "both"],
                        help="keywords=search terms only, accounts=watched profiles only, both=all")
    parser.add_argument("--platforms", help="Comma-separated platforms (twitter,reddit,linkedin,instagram,facebook,tiktok)")
    parser.add_argument("--dry-run", action="store_true", help="Print items, don't save to DB")
    args = parser.parse_args()

    platforms = [p.strip() for p in args.platforms.split(",")] if args.platforms else None
    dry_run = args.dry_run

    # Load search terms + languages from global search profile for "social" category
    search_terms = DEFAULT_SEARCH_TERMS
    languages = ["en"]

    profiles = load_global_search_profiles()
    social_profile = next(
        (p for p in profiles if p.get("category_slug") == "social"), None
    )
    if social_profile:
        search_terms = social_profile.get("search_terms") or search_terms
        languages = social_profile.get("languages") or languages
    else:
        # fall back to CATEGORY_DEFAULTS
        default = CATEGORY_DEFAULTS.get("social")
        if default:
            search_terms, languages = default

    logger.info(f"[SocialRun] mode={args.mode} | terms={len(search_terms)} | langs={languages} | dry_run={dry_run}")

    items = run_social_scrape(
        search_terms=search_terms,
        languages=languages,
        platforms=platforms,
        time_filter="week",
        mode=args.mode,
    )

    saved = save_items(items, dry_run=dry_run)
    logger.info(f"[SocialRun] Saved {saved} new items")

    if not dry_run:
        trigger_profile_matching()

    logger.info("[SocialRun] Done")


if __name__ == "__main__":
    main()
