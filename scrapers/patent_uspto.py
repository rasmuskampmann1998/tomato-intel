"""
USPTO PatentsView API — free, no API key required.
Docs: https://search.patentsview.org/docs/
"""
import httpx
import json
from loguru import logger

PATENTSVIEW_URL = "https://search.patentsview.org/api/v1/patent/"


def search_uspto(search_terms: list[str], date_from: str = "2020-01-01") -> list[dict]:
    """
    Search USPTO patents for given terms.
    Returns list of item dicts for scraped_items table.
    """
    all_items = []

    for term in search_terms:
        logger.info(f"[USPTO] Searching for: {term}")
        try:
            query = {
                "_and": [
                    {"_text_any": {"patent_title": term}},
                    {"_gte": {"patent_date": date_from}}
                ]
            }
            params = {
                "q": json.dumps(query),
                "f": '["patent_number","patent_title","patent_abstract","patent_date","inventor_last_name","assignee_organization"]',
                "o": '{"page":1,"per_page":25}',
                "s": '[{"patent_date":"desc"}]',
            }

            with httpx.Client(timeout=30) as client:
                resp = client.get(PATENTSVIEW_URL, params=params)
                resp.raise_for_status()

            data = resp.json()
            patents = data.get("patents") or []

            for p in patents:
                patent_num = p.get("patent_number", "")
                title = p.get("patent_title", "")
                abstract = p.get("patent_abstract", "")
                date = p.get("patent_date")
                assignee = ""
                if p.get("assignees"):
                    assignee = p["assignees"][0].get("assignee_organization", "")

                url = f"https://patents.google.com/patent/US{patent_num}"

                all_items.append({
                    "source_name": "USPTO — PatentsView",
                    "category_slug": "patents",
                    "title": title,
                    "url": url,
                    "content": f"Assignee: {assignee}\n\n{abstract}",
                    "language": "en",
                    "published_at": f"{date}T00:00:00Z" if date else None,
                    "platform": None,
                    "author": assignee,
                })

            logger.info(f"[USPTO] '{term}': {len(patents)} patents")

        except Exception as e:
            logger.error(f"[USPTO] Failed for '{term}': {e}")

    return all_items
