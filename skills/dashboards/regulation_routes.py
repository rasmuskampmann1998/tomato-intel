from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from supabase_service.regulation_services import get_filtered_regulations, get_regulation_count

logger.add("app.log", level="INFO")

router = APIRouter(prefix="/regulations", tags=["Regulations"])

@router.get(
    "/all",
    summary="Filter regulations with pagination, by title, country, impact, status, and year",
)
def list_regulations(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(50, ge=1, description="Items per page"),
    title: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    impact: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
):
    """
    Paginated, filterable list of regulations.
    Returns a structured response with metadata.
    """
    logger.info(
        f"GET /regulations/all page={page}, limit={limit}, filters: "
        f"title={title}, country={country}, impact={impact}, status={status}, year={year}"
    )

    try:
        data = get_filtered_regulations(
            page, limit, title, country, impact, status, year
        )

        count = get_regulation_count()

        return {
            "success": True,
            "messages": "Regulations fetched successfully.",
            "payload": {
                "data": data,
                "count": count
            }
        }

    except Exception as e:
        logger.error(f"Error fetching regulations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
