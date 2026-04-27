from core.settings import supabase
from loguru import logger

logger.add("app.log", level="INFO") 

REGULATIONS_TABLE = "regulations"

def get_filtered_regulations(
    page: int,
    limit: int,
    title: str = None,
    country: str = None,
    impact: str = None,
    status: str = None,
    year: int = None,
):
    offset = (page - 1) * limit
    logger.info(
        f"Fetching regulations offset={offset}, limit={limit}, filters: "
        f"title={title}, country={country}, impact={impact}, status={status}, year={year}"
    )

    query = supabase.table(REGULATIONS_TABLE).select("*")

    if title:
        query = query.ilike("title", f"%{title.strip()}%")
    if country:
        query = query.ilike("country", f"%{country.strip()}%")
    if impact:
        query = query.ilike("impact", f"%{impact.strip()}%")
    if status:
        query = query.ilike("status", f"%{status.strip()}%")
    if year:
        query = query.eq("year", year)

    query = query.order("year", desc=True).range(offset, offset + limit - 1)

    response = query.execute()
    data = response.data or []
    logger.info(f"Returned {len(data)} rows from Supabase")
    return data

def get_regulation_count():
    logger.info("Fetching total regulation count from the database")
    try:
        response = (
            supabase.table(REGULATIONS_TABLE)
            .select("id", count="exact")  # 'id' or any column, 'count="exact"' returns total count
            .execute()
        )
        return response.count or 0
    except Exception as e:
        logger.error(f"Error fetching regulation count: {e}")
        return 0
