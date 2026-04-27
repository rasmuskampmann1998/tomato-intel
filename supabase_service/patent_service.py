from core.settings import supabase
from loguru import logger

logger.add("app.log", level="INFO") 

PATENT_TABLE = "patents"

def get_filtered_patents(
    page: int,
    limit: int,
    translated_title: str = None,  # accept translated_title for compatibility
    assignee: str = None,
    inventor: str = None,
    publication_start_date: str = None,
    publication_end_date: str = None,
    filing_start_date: str = None,
    filing_end_date: str = None,
    grant_start_date: str = None,
    grant_end_date: str = None,
    priority_start_date: str = None,
    priority_end_date: str = None,
):
    offset = (page - 1) * limit
    logger.info(f"Fetching patents with page={page}, limit={limit}, offset={offset}")

    # Fetch paginated data from Supabase
    response = (
        supabase.table(PATENT_TABLE)
        .select("*")
        .order("publication_date", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    rows = response.data or []

    def in_range(value, start, end):
        return (not start or value >= start) and (not end or value <= end)

    def fuzzy_match(value, keyword):
        return keyword.lower() in (value or "").lower()

    def matches(p):
        search_match = (
            not translated_title or
            fuzzy_match(p.get("title"), translated_title) or
            fuzzy_match(p.get("abstract"), translated_title)
        )
        return all([
            search_match,
            not assignee or fuzzy_match(p.get("assignee"), assignee),
            not inventor or fuzzy_match(p.get("inventor"), inventor),
            in_range(p.get("publication_date"), publication_start_date, publication_end_date),
            in_range(p.get("filing_date"), filing_start_date, filing_end_date),
            in_range(p.get("grant_date"), grant_start_date, grant_end_date),
            in_range(p.get("priority_date"), priority_start_date, priority_end_date),
        ])

    filtered_rows = [p for p in rows if matches(p)]
    logger.info(f"Returned {len(filtered_rows)} filtered results.")
    return {"data": filtered_rows, "filtered_count": len(filtered_rows)}

def get_patent_count():
    logger.info("Fetching total patent count from the database")
    
    try:
        response = (
            supabase.table(PATENT_TABLE)
            .select("id", count="exact")  # 'id' can be any column, 'count="exact"' tells Supabase to return the total count
            .execute()
        )
        
        total_count = response.count or 0
        logger.info(f"Total patents count: {total_count}")
        return {"total_patents": total_count}

    except Exception as e:
        logger.error(f"Error fetching patent count: {e}")
        return {"total_patents": 0}
