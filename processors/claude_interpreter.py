"""
Claude Interpreter — Batch-process uninterpreted scraped items.
Model: claude-haiku-4-5-20251001 (cheap + fast)
Batch size: 20 items per API call
Prompt reuses structure from llm_services/alert.py, ported to Anthropic SDK.

Usage:
    python processors/claude_interpreter.py           # process all unprocessed
    python processors/claude_interpreter.py --test    # process 3 items, print output
    python processors/claude_interpreter.py --limit 50
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
BATCH_SIZE = 10


def get_unprocessed(limit: int = 100) -> list[dict]:
    """Fetch scraped items that haven't been interpreted yet."""
    try:
        resp = (
            supabase.table("scraped_items")
            .select("id,title,content,language,category_slug,url,platform,source_id")
            .eq("is_processed", False)
            .order("scraped_at", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        logger.error(f"Failed to fetch unprocessed items: {e}")
        return []


def build_prompt(items: list[dict]) -> str:
    return f"""You are an expert analyst for a tomato seed intelligence platform.

Process these {len(items)} scraped items and return structured JSON analysis.

For each item:
1. Translate title to English (if not already)
2. Write a 2-sentence summary in English
3. Score relevance to tomato/seed industry (1=unrelated, 10=highly relevant)
4. Assign up to 5 tags from: disease_resistance, ToBRFV, TYLCV, breeding, genetics, patent, yield, fungal_resistance, virus_resistance, insect_resistance, shelf_life, molecular_markers, competitor, regulation, market, pricing, technology, climate, seed_varieties
5. Identify original language (ISO 639-1 code: en, nl, da, de, es, zh, hi, etc.)
6. Identify most relevant country

INPUT ITEMS:
{json.dumps([{"id": i["id"], "title": i.get("title",""), "content": (i.get("content") or "")[:400], "language": i.get("language","en"), "category": i.get("category_slug","")} for i in items], ensure_ascii=False, indent=2)}

OUTPUT: Return ONLY a JSON array, no markdown, no extra text:
[
  {{
    "id": "uuid-from-input",
    "title_en": "English title",
    "summary_en": "Two sentence summary in English.",
    "relevance_score": 7,
    "tags": ["breeding", "disease_resistance"],
    "language": "en",
    "country": "Netherlands",
    "category_slug": "news"
  }},
  ...
]"""


def interpret_batch(items: list[dict], client: anthropic.Anthropic) -> list[dict]:
    """Send a batch to Claude and parse the JSON response."""
    prompt = build_prompt(items)
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        output = response.content[0].text.strip()

        # Strip markdown code fences if present
        if output.startswith("```"):
            output = output.split("```")[1]
            if output.startswith("json"):
                output = output[4:]
            output = output.strip()

        return json.loads(output)

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error in Claude response: {e}")
        return []
    except Exception as e:
        logger.error(f"Claude API call failed: {e}")
        return []


def save_interpretations(interpretations: list[dict], source_items: list[dict], dry_run: bool = False) -> int:
    """Upsert into interpreted_items and mark scraped_items as processed."""
    if not interpretations:
        return 0

    if dry_run:
        for item in interpretations[:3]:
            logger.info(f"  [DRY RUN] {item.get('title_en','')[:80]}")
            logger.info(f"            Score:{item.get('relevance_score')} Tags:{item.get('tags')}")
        return len(interpretations)

    saved = 0
    item_ids_to_mark = []

    for interp in interpretations:
        scraped_id = interp.get("id")
        if not scraped_id:
            continue

        source_item = next((i for i in source_items if i["id"] == scraped_id), {})
        original_language = source_item.get("language") or interp.get("language") or "en"

        row = {
            "scraped_item_id": scraped_id,
            "title_en": interp.get("title_en", ""),
            "summary_en": interp.get("summary_en", ""),
            "relevance_score": interp.get("relevance_score", 5),
            "tags": interp.get("tags", []),
            "category_slug": interp.get("category_slug", ""),
        }

        try:
            supabase.table("interpreted_items").upsert(
                row, on_conflict="scraped_item_id"
            ).execute()
            item_ids_to_mark.append(scraped_id)
            saved += 1
        except Exception as e:
            logger.warning(f"Failed to save interpretation for {scraped_id}: {e}")

    # Mark items as processed
    if item_ids_to_mark:
        try:
            supabase.table("scraped_items").update({"is_processed": True}).in_(
                "id", item_ids_to_mark
            ).execute()
        except Exception as e:
            logger.warning(f"Failed to mark items processed: {e}")

    return saved


def main():
    parser = argparse.ArgumentParser(description="Claude interpreter for scraped items")
    parser.add_argument("--test", action="store_true", help="Test mode: process 3 items only")
    parser.add_argument("--dry-run", action="store_true", help="Print output, don't save")
    parser.add_argument("--limit", type=int, default=200, help="Max items to process")
    args = parser.parse_args()

    if not CLAUDE_API_KEY:
        logger.error("CLAUDE_API_KEY not set")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    limit = 3 if args.test else args.limit
    dry_run = args.dry_run or args.test

    logger.info(f"Fetching up to {limit} unprocessed items...")
    items = get_unprocessed(limit)
    logger.info(f"Found {len(items)} unprocessed items")

    if not items:
        logger.info("Nothing to process")
        return

    total_saved = 0
    for i in range(0, len(items), BATCH_SIZE):
        batch = items[i:i + BATCH_SIZE]
        logger.info(f"Processing batch {i//BATCH_SIZE + 1}: {len(batch)} items")
        interpretations = interpret_batch(batch, client)
        saved = save_interpretations(interpretations, batch, dry_run)
        total_saved += saved
        logger.info(f"Batch done: {saved}/{len(batch)} saved")

    logger.info(f"Interpreter complete. Total saved: {total_saved}/{len(items)}")


if __name__ == "__main__":
    main()
