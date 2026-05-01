"""
Trend detector — finds topics spiking across 3+ sources in 48h.
Uses interpreted_items.tags[] grouped by frequency.
Run after claude_interpreter.py in GitHub Actions.
"""
import sys
import argparse
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from db.client import supabase


def detect_trends(hours: int = 48, min_sources: int = 3, dry_run: bool = False):
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    print(f"[trend_detector] Loading interpreted items from last {hours}h...")
    resp = supabase.table("interpreted_items").select(
        "id, tags, category_slug, scraped_item_id, "
        "scraped_items(source_id, published_at)"
    ).gte("interpreted_at", since).execute()

    items = resp.data or []
    print(f"[trend_detector] {len(items)} items loaded")

    if not items:
        print("[trend_detector] Nothing to process.")
        return

    # Build: tag → {source_ids, item_ids, category_slugs}
    tag_data = defaultdict(lambda: {"source_ids": set(), "item_ids": [], "categories": defaultdict(int)})

    for item in items:
        tags = item.get("tags") or []
        source_id = (item.get("scraped_items") or {}).get("source_id")
        for tag in tags:
            tag = tag.strip().lower()
            if not tag or len(tag) < 3:
                continue
            tag_data[tag]["item_ids"].append(item["id"])
            tag_data[tag]["categories"][item.get("category_slug", "unknown")] += 1
            if source_id:
                tag_data[tag]["source_ids"].add(source_id)

    # Filter to tags with >= min_sources distinct sources
    trending = {
        tag: data
        for tag, data in tag_data.items()
        if len(data["source_ids"]) >= min_sources
    }

    print(f"[trend_detector] {len(trending)} trending topics found (threshold: {min_sources}+ sources)")

    if not trending:
        # Deactivate old alerts
        if not dry_run:
            supabase.table("trend_alerts").update({"active": False}).eq("active", True).execute()
        return

    now_iso = datetime.now(timezone.utc).isoformat()

    # Load existing active alerts to upsert
    existing_resp = supabase.table("trend_alerts").select("id, topic").eq("active", True).execute()
    existing = {row["topic"]: row["id"] for row in (existing_resp.data or [])}

    upserted = 0
    for tag, data in trending.items():
        top_category = max(data["categories"], key=data["categories"].get)
        source_count = len(data["source_ids"])
        item_ids = data["item_ids"][:50]  # cap array size

        print(f"  📈 {tag!r} — {source_count} sources, {len(item_ids)} items, cat={top_category}")

        if dry_run:
            continue

        if tag in existing:
            supabase.table("trend_alerts").update({
                "item_ids": item_ids,
                "source_count": source_count,
                "last_seen": now_iso,
                "active": True,
            }).eq("id", existing[tag]).execute()
        else:
            supabase.table("trend_alerts").insert({
                "topic": tag,
                "item_ids": item_ids,
                "source_count": source_count,
                "category_slug": top_category,
                "active": True,
                "first_seen": now_iso,
                "last_seen": now_iso,
            }).execute()
        upserted += 1

    # Deactivate topics that are no longer trending
    stale_topics = set(existing.keys()) - set(trending.keys())
    if stale_topics and not dry_run:
        supabase.table("trend_alerts").update({"active": False}).in_("topic", list(stale_topics)).execute()
        print(f"[trend_detector] Deactivated {len(stale_topics)} stale trends")

    if not dry_run:
        print(f"[trend_detector] Done — {upserted} trends upserted")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=int, default=48)
    parser.add_argument("--min-sources", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    detect_trends(hours=args.hours, min_sources=args.min_sources, dry_run=args.dry_run)
