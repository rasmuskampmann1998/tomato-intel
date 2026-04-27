from fastapi import APIRouter, HTTPException
from supabase_service.competitor_service import get_latest_competitor_data
from loguru import logger  # Importing Loguru for logging

# Set up logger
logger.add("app.log", level="INFO")  # Log to a file with level INFO

# Create the APIRouter for competitor data
router = APIRouter(prefix="/competitor", tags=["Competitor Data"])

@router.get("/latest")
async def fetch_latest_competitor_data():
    """
    Fetch the latest competitor data from the Supabase database.
    
    Returns:
    - dict: The latest competitor data stored in the database.
    
    Raises:
    - HTTPException: If no competitor data is found.
    """
    logger.info("Fetching latest competitor data from the database.")  # Log info when data fetch starts

    try:
        # Fetch the latest competitor data
        competitor_data = get_latest_competitor_data()

        # If no data is found, raise a 404 exception
        if not competitor_data:
            logger.warning("No competitor data found.")  # Log warning if no data is found
            raise HTTPException(status_code=404, detail="No competitor data found.")

        logger.info("Successfully fetched competitor data.")  # Log success after fetching data
        return competitor_data

    except Exception as e:
        # Log any unexpected errors
        logger.error(f"Error fetching competitor data: {e}")  # Log error
        raise HTTPException(status_code=500, detail=str(e))
