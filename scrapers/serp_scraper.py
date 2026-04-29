"""
SerpAPI Google News Scraper — Multi-Language Search Discovery
Queries Google News for (search_term, language) combos and returns
items shaped for the scraped_items table (source_id = NULL).

Usage:
    python -c "from scrapers.serp_scraper import search_google_news; \
               items = search_google_news('Tomato News', 'zh', 'news'); \
               [print(i['title'], i['language']) for i in items]"
"""
import os
import urllib.request
import urllib.parse
import json
from datetime import datetime, timezone
from loguru import logger

SERPAPI_KEY = os.environ.get("SERPAPI_API_KEY", "")
SERPAPI_BASE = "https://serpapi.com/search"

# Maps 2-letter language codes to SerpAPI hl/gl params
LANG_MAP = {
    "en": {"hl": "en", "gl": "us"},
    "zh": {"hl": "zh-CN", "gl": "cn"},
    "ja": {"hl": "ja", "gl": "jp"},
    "hi": {"hl": "hi", "gl": "in"},
    "es": {"hl": "es", "gl": "es"},
    "ar": {"hl": "ar", "gl": "sa"},
    "tr": {"hl": "tr", "gl": "tr"},
    "nl": {"hl": "nl", "gl": "nl"},
    "da": {"hl": "da", "gl": "dk"},
    "de": {"hl": "de", "gl": "de"},
    "fr": {"hl": "fr", "gl": "fr"},
}

# Per-category defaults — used when DB has no global search profiles yet
CATEGORY_DEFAULTS = {
    "news": (
        ["Tomato News", "Tomato Announcements", "Tomato Novelty"],
        ["en", "zh", "ja", "hi", "es", "ar", "tr"],
    ),
    "competitors": (
        ["Tomato Variety", "Tomato Seed Company", "Tomato Results"],
        ["en", "zh", "ja", "hi", "es", "ar", "tr"],
    ),
    "crops": (
        ["Tomato Seed Production", "Tomato Seed Quality", "Tomato Seed Disease"],
        ["en", "zh", "ja", "hi", "es", "ar", "tr"],
    ),
    "patents": (
        ["Tomato Patent", "Tomato Intellectual Property"],
        ["en", "zh", "hi", "es"],
    ),
    "regulations": (
        ["Tomato Seed Health", "Tomato quarantine pest", "Tomato seed certificate"],
        ["en", "zh", "ja", "hi", "es", "ar", "tr"],
    ),
    "genetics": (
        ["Tomato Trait", "Tomato Seed", "Tomato disease", "Tomato Genetic"],
        ["en", "zh", "ja", "hi", "es", "ar", "tr"],
    ),
    "social": (
        ["Tomato", "Tomato News", "Tomato Seed"],
        ["en", "zh", "ja", "hi", "es", "ar", "tr"],
    ),
}


def _parse_date(date_str: str | None) -> str | None:
    """Best-effort parse of SerpAPI date strings like '2 hours ago', '3 days ago', ISO dates."""
    if not date_str:
        return None
    try:
        # SerpAPI sometimes returns ISO format
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).isoformat()
    except (ValueError, AttributeError):
        pass
    # Relative dates: return current time as approximation
    now = datetime.now(timezone.utc).isoformat()
    return now


def search_google_news(
    query: str,
    lang: str,
    category_slug: str,
    num: int = 10,
) -> list[dict]:
    """
    Query SerpAPI Google News for one (query, language) combination.
    Returns items shaped for scraped_items (source_id omitted = NULL in DB).

    Args:
        query: Search query, e.g. "Tomato News"
        lang: 2-letter language code, e.g. "zh"
        category_slug: Category for scraped_items.category_slug
        num: Max results per query (SerpAPI default is 10)

    Returns:
        List of scraped_item dicts ready for save_items()
    """
    if not SERPAPI_KEY:
        logger.warning("[SerpAPI] No SERPAPI_API_KEY — skipping search discovery")
        return []

    lang_params = LANG_MAP.get(lang, LANG_MAP["en"])
    params = {
        "engine": "google_news",
        "q": query,
        "hl": lang_params["hl"],
        "gl": lang_params["gl"],
        "api_key": SERPAPI_KEY,
        "num": num,
    }

    url = f"{SERPAPI_BASE}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        # 429 = quota exceeded; don't crash the whole run
        err_str = str(e)
        if "429" in err_str or "quota" in err_str.lower():
            logger.warning(f"[SerpAPI] Quota exceeded — stopping search discovery for this run")
            raise _QuotaExceeded()
        logger.error(f"[SerpAPI] Request failed for '{query}' ({lang}): {e}")
        return []

    news_results = data.get("news_results", [])
    if not news_results:
        logger.debug(f"[SerpAPI] 0 results for '{query}' ({lang})")
        return []

    items = []
    for r in news_results:
        article_url = r.get("link", "")
        title = r.get("title", "")
        if not article_url or not title:
            continue

        source_info = r.get("source", {})
        snippet = r.get("snippet", "")

        items.append({
            "category_slug": category_slug,
            "title": title,
            "url": article_url,
            "content": snippet,
            "language": lang,
            "author": source_info.get("name", ""),
            "published_at": _parse_date(r.get("date")),
            # source_id intentionally omitted → NULL (search-discovered, not a tracked source)
        })

    logger.debug(f"[SerpAPI] '{query}' ({lang}): {len(items)} results")
    return items


class _QuotaExceeded(Exception):
    """Raised when SerpAPI returns a quota-exceeded error so the caller can bail early."""
    pass


def run_search_discovery_for_category(
    category_slug: str,
    search_terms: list[str],
    languages: list[str],
    dry_run: bool = False,
) -> list[dict]:
    """
    Run SerpAPI search for all (term × language) combos for one category.
    Prioritises English, then zh/es/hi, then remaining languages.
    Stops silently on quota exceeded.

    Returns list of items (not saved — caller calls save_items).
    """
    # Run English first, then high-priority languages, then the rest
    priority = ["en", "zh", "es", "hi", "ar", "ja", "tr", "nl", "de", "fr", "da"]
    ordered_langs = sorted(languages, key=lambda l: priority.index(l) if l in priority else 99)

    all_items = []
    for lang in ordered_langs:
        for term in search_terms:
            try:
                items = search_google_news(term, lang, category_slug)
                if dry_run:
                    for item in items[:3]:
                        logger.info(f"  [DRY RUN SerpAPI] [{lang}] {item.get('title', '')[:80]}")
                    logger.info(f"  [DRY RUN SerpAPI] {len(items)} items for '{term}' ({lang})")
                else:
                    all_items.extend(items)
            except _QuotaExceeded:
                logger.warning(f"[SerpAPI] Quota hit — stopping discovery for {category_slug}")
                return all_items

    return all_items
