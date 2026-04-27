from fastapi import APIRouter, HTTPException
from supabase_service.breeding_service import get_latest_breeding_recommendation
from loguru import logger  # Importing Loguru for logging

# Set up logger
logger.add("app.log", level="INFO")  # Log to a file with level INFO

router = APIRouter(prefix="/breeding", tags=["Breeding Recommendations"])

@router.get("/recommendation")
async def get_latest_breeding_recommendation_endpoint():
    """
    Fetch the latest breeding recommendation.
    
    This endpoint retrieves the latest available breeding recommendation
    by calling the breeding service. If no recommendation is found, an
    HTTPException is raised with a 404 status code.
    
    Returns:
    - dict: The latest breeding recommendation.

    Raises:
    - HTTPException: If no breeding recommendation is found.
    """
    logger.info("Fetching the latest breeding recommendation.")  # Log info

    try:
        # Fetch the latest breeding recommendation
        recommendation = get_latest_breeding_recommendation()
        
        if not recommendation:
            logger.warning("No breeding recommendation found.")  # Log warning if no data
            raise HTTPException(status_code=404, detail="No breeding recommendation found.")
        
        logger.info("Breeding recommendation fetched successfully.")  # Log success
        return recommendation

    except Exception as e:
        # Log any errors that occur
        logger.error(f"Error fetching breeding recommendation: {e}")  # Log error
        raise HTTPException(status_code=500, detail=str(e))
