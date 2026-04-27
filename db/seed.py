"""
Seed Supabase categories and sources from config/sources.json.

Usage:
    python db/seed.py              # insert if not exists
    python db/seed.py --reset      # delete all sources + categories first
"""
import argparse
import json
import sys
from pathlib import Path
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))
from db.client import supabase

CONFIG_PATH = Path(__file__).parent.parent / "config" / "sources.json"

# Category metadata not stored in sources.json — defined here to match schema.sql
CATEGORY_META = {
    "news":        {"name": "News & Updates",       "description": "Latest horticulture and agriculture news worldwide", "frequency": "daily"},
    "competitors": {"name": "Competitors",           "description": "Competitor activity, product launches, funding",    "frequency": "weekly"},
    "crops":       {"name": "Crop Recommendations",  "description": "Breeding advice, growing conditions, yield tips",   "frequency": "weekly"},
    "patents":     {"name": "Tomato Patents",         "description": "Patent filings across EPO, USPTO, CNIPA, IP India", "frequency": "monthly"},
    "regulations": {"name": "Regulations",            "description": "Regulatory changes across 27 countries",            "frequency": "monthly"},
    "genetics":    {"name": "Genetics",               "description": "Genetic traits, variety data, molecular markers",   "frequency": "monthly"},
    "social":      {"name": "Social Media",           "description": "Reddit, Twitter/X, Instagram, LinkedIn signals",    "frequency": "daily"},
}


def seed(reset: bool = False):
    config = json.loads(CONFIG_PATH.read_text())

    if reset:
        logger.warning("Resetting sources and categories...")
        supabase.table("sources").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("categories").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    categories = config.get("categories", {})

    for slug, cat_data in categories.items():
        meta = CATEGORY_META.get(slug, {"name": slug, "description": "", "frequency": "weekly"})
        # Upsert category
        cat_row = {
            "name": meta["name"],
            "slug": slug,
            "description": meta["description"],
            "default_frequency": meta["frequency"],
        }
        resp = supabase.table("categories").upsert(cat_row, on_conflict="slug").execute()
        cat_id = resp.data[0]["id"] if resp.data else None

        if not cat_id:
            # fetch existing
            resp2 = supabase.table("categories").select("id").eq("slug", slug).single().execute()
            cat_id = resp2.data["id"] if resp2.data else None

        if not cat_id:
            logger.error(f"Could not get category id for {slug}")
            continue

        logger.info(f"Category '{slug}' -> {cat_id}")

        sources = cat_data.get("sources", [])
        for source in sources:
            row = {
                "category_id": cat_id,
                "name": source["name"],
                "url": source["url"],
                "rss_url": source.get("rss_url"),
                "scrape_type": source.get("scrape_type", "html"),
                "apify_actor": source.get("apify_actor"),
                "css_selector": source.get("css_selector"),
                "language": source.get("language", "en"),
                "is_required": source.get("is_required", False),
                "active": True,
            }
            try:
                supabase.table("sources").insert(row).execute()
                logger.info(f"  + {source['name']}")
            except Exception as e:
                msg = str(e)
                if "duplicate" in msg.lower() or "23505" in msg:
                    logger.debug(f"  = {source['name']} (already exists)")
                else:
                    logger.warning(f"  ! Failed to seed {source['name']}: {e}")

    logger.info("Seed complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Delete existing data before seeding")
    args = parser.parse_args()
    seed(reset=args.reset)
