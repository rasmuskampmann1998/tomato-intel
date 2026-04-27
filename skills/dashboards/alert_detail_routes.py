from fastapi import APIRouter, HTTPException
from core.settings import supabase
from supabase_service.alert_detail_service import get_latest_alert_details
from loguru import logger  # Importing Loguru for logging

logger.add("app.log", level="INFO") 

router = APIRouter(prefix="/alert-details", tags=["Alert details"])

@router.get("/latest")
async def latest_alert_details():
    try:
        logger.info("Fetching latest alert details...")  # Log the request to fetch the latest alert details
        alert_details = get_latest_alert_details()  # Fetch latest alert details
        
        if alert_details is None:
            logger.warning("No alert details found.")  # Log a warning if no alert details are found
            raise HTTPException(status_code=404, detail="No alert details found.")
        
        logger.info(f"Successfully fetched latest alert details: {alert_details}")  # Log successful fetching of details
        return alert_details  # Return the latest alert details

    except Exception as e:
        logger.error(f"Error fetching latest alert details: {e}")  # Log the error in case of failure
        raise HTTPException(status_code=500, detail=str(e))
