from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from supabase_service.genetic_service import get_filtered_genetics, get_genetic_count

logger.add("app.log", level="INFO")

router = APIRouter(prefix="/genetics", tags=["Genetics"])

@router.get(
    "/all",
    summary="Get genetics with filters and pagination",
)
def list_genetics(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1),
    variety_name: Optional[str] = Query(None),
    country_of_origin: Optional[str] = Query(None),
    genus: Optional[str] = Query(None),
    crop_name: Optional[str] = Query(None),
    collection_start_date: Optional[str] = Query(None),
    collection_end_date: Optional[str] = Query(None),
):
    """
    Paginated, filterable list of genetics based on multiple criteria.
    Returns a structured response with metadata.
    """
    logger.info(
        f"GET /genetics/all page={page}, limit={limit}, filters: "
        f"variety_name={variety_name}, country_of_origin={country_of_origin}, "
        f"genus={genus}, crop_name={crop_name}, "
        f"collection_start_date={collection_start_date}, collection_end_date={collection_end_date}"
    )
    try:
        genetics = get_filtered_genetics(
            page, limit, variety_name, country_of_origin, genus, crop_name, collection_start_date, collection_end_date
        )
        count = get_genetic_count()

        logger.info(f"Returned {len(genetics)} genetics records.")

        return {
            "success": True,
            "messages": "Genetics fetched successfully.",
            "payload": {
                "data": genetics,
                "count": count
            }
        }

    except Exception as e:
        logger.error(f"Error fetching genetics data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
