from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from supabase_service.patent_service import get_patent_count, get_filtered_patents

# Set up logger
logger.add("app.log", level="INFO")

router = APIRouter(prefix="/patents", tags=["Patents"])

@router.get("/all", summary="Get patents with filters and pagination")
def list_patents(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1),
    translated_title: Optional[str] = Query(None),
    assignee: Optional[str] = Query(None),
    inventor: Optional[str] = Query(None),

    publication_start_date: Optional[str] = Query(None),
    publication_end_date: Optional[str] = Query(None),

    filing_start_date: Optional[str] = Query(None),
    filing_end_date: Optional[str] = Query(None),

    grant_start_date: Optional[str] = Query(None),
    grant_end_date: Optional[str] = Query(None),

    priority_start_date: Optional[str] = Query(None),
    priority_end_date: Optional[str] = Query(None),
):
    """
    Paginated, filterable list of patents based on multiple criteria.
    Returns response in structured format with metadata.
    """
    logger.info(
        f"GET /patents/all page={page}, limit={limit}, filters: "
        f"translated_title={translated_title}, assignee={assignee}, inventor={inventor}, "
        f"publication_start_date={publication_start_date}, publication_end_date={publication_end_date}, "
        f"filing_start_date={filing_start_date}, filing_end_date={filing_end_date}, "
        f"grant_start_date={grant_start_date}, grant_end_date={grant_end_date}, "
        f"priority_start_date={priority_start_date}, priority_end_date={priority_end_date}"
    )

    try:
        # Fetch filtered data
        filtered_result = get_filtered_patents(
            page=page,
            limit=limit,
            translated_title=translated_title,
            assignee=assignee,
            inventor=inventor,
            publication_start_date=publication_start_date,
            publication_end_date=publication_end_date,
            filing_start_date=filing_start_date,
            filing_end_date=filing_end_date,
            grant_start_date=grant_start_date,
            grant_end_date=grant_end_date,
            priority_start_date=priority_start_date,
            priority_end_date=priority_end_date,
        )
        data = filtered_result["data"]
        filtered_count = filtered_result["filtered_count"]

        # Fetch total patent count from DB
        count_info = get_patent_count()
        total_count = count_info.get("total_patents", 0)

        logger.info(f"Returned {len(data)} patent records.")

        return {
            "success": True,
            "messages": "Patents fetched successfully.",
            "payload": {
                "data": data,
                "count": total_count,
                "filtered_count": filtered_count
            }
        }

    except Exception as e:
        logger.error(f"GET /patents/all failed: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
