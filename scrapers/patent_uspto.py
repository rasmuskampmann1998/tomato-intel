"""
USPTO Patents — dual endpoint:
  Primary:  Google Patents JSON (no API key, works from Railway)
  Fallback: PatentsView API v2 (https://search.patentsview.org)
"""
import httpx
import json
import urllib.parse
from loguru import logger

GOOGLE_PATENTS_URL = "https://patents.google.com/xhr/query"
PATENTSVIEW_URL = "https://search.patentsview.org/api/v1/patent/"

HEADERS_GPATENTS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://patents.google.com/",
}


def _search_google_patents(term: str, date_str: str, seen: set) -> list[dict]:
    """Query Google Patents JSON endpoint. Returns [] on any failure."""
    query = f"({term}) assignee:(seed OR breeding OR vegetable OR tomato)"
    url_param = urllib.parse.quote(f"q={query}&after=priority:{date_str}")
    try:
        resp = httpx.get(
            GOOGLE_PATENTS_URL,
            params={"url": url_param, "exp": "", "download": "false"},
            headers=HEADERS_GPATENTS,
            timeout=30,
            follow_redirects=True,
        )
        if resp.status_code != 200:
            logger.warning(f"[USPTO/GPatents] HTTP {resp.status_code} for '{term}'")
            return []

        data = resp.json()
        items = []
        for cluster in data.get("results", {}).get("cluster", []):
            for result in cluster.get("result", []):
                pat = result.get("patent", {})
                pub_num = pat.get("publication_number", "")
                if not pub_num or pub_num in seen:
                    continue
                seen.add(pub_num)
                title = pat.get("title", pub_num)
                if not title:
                    continue
                assignees = [a.get("name", "") for a in pat.get("assignee", [])]
                assignee = assignees[0] if assignees else ""
                filing_date = pat.get("filing_date", "") or pat.get("priority_date", "")
                pub_date = None
                if filing_date and len(filing_date) >= 8:
                    d = filing_date[:8]
                    pub_date = f"{d[:4]}-{d[4:6]}-{d[6:8]}T00:00:00Z"
                items.append({
                    "source_name": "USPTO — Google Patents",
                    "category_slug": "patents",
                    "title": title,
                    "url": f"https://patents.google.com/patent/{pub_num}",
                    "content": f"Assignee: {assignee}",
                    "language": "en",
                    "published_at": pub_date,
                    "platform": None,
                    "author": assignee,
                })
        return items
    except Exception as e:
        logger.warning(f"[USPTO/GPatents] Failed for '{term}': {e}")
        return []


def _search_patentsview(term: str, date_from: str, seen: set) -> list[dict]:
    """Query PatentsView v2 API. Returns [] on any failure."""
    try:
        query = {
            "_and": [
                {"_text_any": {"patent_title": term}},
                {"_gte": {"patent_date": date_from}},
            ]
        }
        params = {
            "q": json.dumps(query),
            "f": json.dumps(["patent_number", "patent_title", "patent_abstract", "patent_date"]),
            "o": json.dumps({"per_page": 25}),
            "s": json.dumps([{"patent_date": "desc"}]),
        }
        resp = httpx.get(PATENTSVIEW_URL, params=params, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        patents = resp.json().get("patents") or []
        items = []
        for p in patents:
            num = p.get("patent_number", "")
            if not num or num in seen:
                continue
            seen.add(num)
            title = p.get("patent_title", "")
            if not title:
                continue
            date = p.get("patent_date")
            items.append({
                "source_name": "USPTO — PatentsView",
                "category_slug": "patents",
                "title": title,
                "url": f"https://patents.google.com/patent/US{num}",
                "content": p.get("patent_abstract", ""),
                "language": "en",
                "published_at": f"{date}T00:00:00Z" if date else None,
                "platform": None,
                "author": "",
            })
        return items
    except Exception as e:
        logger.warning(f"[USPTO/PView] Failed for '{term}': {e}")
        return []


def search_uspto(search_terms: list[str], date_from: str = "2022-01-01") -> list[dict]:
    """
    Search USPTO patents. Tries Google Patents first, falls back to PatentsView.
    Returns list of item dicts for scraped_items table.
    """
    all_items: list[dict] = []
    seen: set[str] = set()
    date_str = date_from.replace("-", "")

    for term in search_terms:
        logger.info(f"[USPTO] Searching: {term}")

        items = _search_google_patents(term, date_str, seen)
        if not items:
            logger.info(f"[USPTO] Google Patents returned 0, trying PatentsView for '{term}'")
            items = _search_patentsview(term, date_from, seen)

        all_items.extend(items)
        logger.info(f"[USPTO] '{term}': {len(items)} patents")

    return all_items
