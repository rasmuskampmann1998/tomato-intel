"""
Profile Scorer — Re-score matched items against each profile's intelligence brief.

For each search profile that has an intelligence_brief, fetches recently matched
scraped items and asks Claude Haiku to score how relevant they are to the brief.
Stores the score in profile_items.profile_relevance_score.

Usage:
    python processors/profile_scorer.py                # score all profiles with briefs
    python processors/profile_scorer.py --hours 48     # look back 48 hours (default 24)
    python processors/profile_scorer.py --test         # dry run, print scores only
"""
import argparse
import json
import os
import sys
from pathlib import Path
import anthropic
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))
from db.client import supabase

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
MODEL = "claude-haiku-4-5-20251001"
BATCH_SIZE = 15


def get_profiles_with_briefs() -> list[dict]:
    resp = (
        supabase.table("search_profiles")
        .select("id, name, search_terms, intelligence_brief")
        .not_.is_("intelligence_brief", "null")
        .neq("intelligence_brief", "")
        .execute()
    )
    return resp.data or []


def get_unscored_items(profile_id: str, hours: int = 24) -> list[dict]:
    """Fetch profile_items that don't yet have a profile_relevance_score."""
    resp = (
        supabase.table("profile_items")
        .select("id, scraped_item_id, scraped_items(title, content, url)")
        .eq("search_profile_id", profile_id)
        .is_("profile_relevance_score", "null")
        .order("matched_at", desc=True)
        .limit(100)
        .execute()
    )
    return resp.data or []


def build_scoring_prompt(brief: str, profile_name: str, items: list[dict]) -> str:
    items_list = []
    for item in items:
        si = item.get("scraped_items") or {}
        items_list.append({
            "id": item["id"],
            "title": si.get("title", ""),
            "content": (si.get("content") or "")[:300],
        })

    return f"""You are an intelligence analyst. A user has described their focus area below.

INTELLIGENCE BRIEF for "{profile_name}":
---
{brief}
---

Score each item 1-10 for how relevant it is to THIS specific brief.
1 = not relevant at all to the brief's focus
10 = directly addresses the brief's key topics, companies, or challenges

INPUT ITEMS:
{json.dumps(items_list, ensure_ascii=False, indent=2)}

Return ONLY a JSON array, no markdown:
[
  {{"id": "profile_item_uuid", "score": 7, "reason": "one sentence"}},
  ...
]"""


def score_batch(items: list[dict], brief: str, profile_name: str, client: anthropic.Anthropic) -> list[dict]:
    prompt = build_scoring_prompt(brief, profile_name, items)
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        output = response.content[0].text.strip()
        if output.startswith("```"):
            output = output.split("```")[1]
            if output.startswith("json"):
                output = output[4:]
            output = output.strip()
        return json.loads(output)
    except Exception as e:
        logger.error(f"Claude scoring failed: {e}")
        return []


def save_scores(scores: list[dict], dry_run: bool = False) -> int:
    saved = 0
    for s in scores:
        profile_item_id = s.get("id")
        score = s.get("score")
        if not profile_item_id or score is None:
            continue
        if dry_run:
            logger.info(f"  [DRY RUN] {profile_item_id} → score {score}: {s.get('reason', '')}")
            saved += 1
            continue
        try:
            supabase.table("profile_items").update(
                {"profile_relevance_score": int(score)}
            ).eq("id", profile_item_id).execute()
            saved += 1
        except Exception as e:
            logger.warning(f"Failed to save score for {profile_item_id}: {e}")
    return saved


def main():
    parser = argparse.ArgumentParser(description="Score profile items against intelligence briefs")
    parser.add_argument("--hours", type=int, default=24, help="Look back N hours")
    parser.add_argument("--test", action="store_true", help="Dry run")
    args = parser.parse_args()

    if not CLAUDE_API_KEY:
        logger.error("CLAUDE_API_KEY not set")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    profiles = get_profiles_with_briefs()
    logger.info(f"Found {len(profiles)} profiles with intelligence briefs")

    total_scored = 0
    for profile in profiles:
        pid = profile["id"]
        name = profile.get("name") or ", ".join(profile["search_terms"])
        brief = profile["intelligence_brief"]

        items = get_unscored_items(pid, args.hours)
        if not items:
            logger.info(f"Profile '{name}': no unscored items")
            continue

        logger.info(f"Profile '{name}': scoring {len(items)} items")

        for i in range(0, len(items), BATCH_SIZE):
            batch = items[i:i + BATCH_SIZE]
            scores = score_batch(batch, brief, name, client)
            saved = save_scores(scores, dry_run=args.test)
            total_scored += saved
            logger.info(f"  Batch {i // BATCH_SIZE + 1}: {saved}/{len(batch)} scored")

    logger.info(f"Profile scorer complete. Total scored: {total_scored}")


if __name__ == "__main__":
    main()
