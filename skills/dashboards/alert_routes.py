from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request
from core.settings import supabase
from supabase_service.alert_service import get_latest_alert, get_alert_by_id, get_alerts_id_date_list
from loguru import logger  # Importing Loguru for logging

logger.add("app.log", level="INFO") 

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/latest")
async def latest_alert(
    category: Optional[str] = Query(None, description="Category to filter by"),
    country: Optional[str] = Query(None, description="Country to filter by"),
    id: Optional[str] = Query(None, description="Alert ID to fetch (if not provided, fetch latest)")
):
    try:
        logger.info("Fetching latest alert..." if not id else f"Fetching alert by id: {id}")  # Log the API request
        if id:
            alert = get_alert_by_id(id)
        else:
            alert = get_latest_alert()  # Fetch the latest consolidated alert
        
        if alert is None:
            logger.warning("No alerts found.")  # Log a warning if no alerts found
            raise HTTPException(status_code=404, detail="No alerts found.")
        
        news_data = alert.get("news_data", [])
        
        # Initialize filtered_news with the entire news_data
        filtered_news = news_data
        
        if category:
            logger.info(f"Filtering by category: {category}")  # Log category filter
            filtered_news = [
                news
                for news in filtered_news
                if news.get("category", "").lower() == category.lower()
            ]
        
        if country:
            logger.info(f"Filtering by country: {country}")  # Log country filter
            filtered_news = [
                news
                for news in filtered_news
                if news.get("country", "").lower() == country.lower()
            ]
        
        # If no results after filtering, return an empty array with 200 OK
        if not filtered_news:
            logger.info("No matching results found after filtering. Returning empty array.")
            filtered_news = []

        # Return filtered data in same structure
        logger.info(f"Returning filtered alert details: {len(filtered_news)} news items found.")
        return {
            "id": alert["id"],
            "date": alert["date"],
            "news_data": filtered_news,
            "created_at": alert["created_at"],
        }
    
    except HTTPException:
        logger.error("HTTPException raised. Returning error.")  # Log if HTTPException is raised
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Error in fetching latest alert: {str(e)}")  # Log any errors
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_all_categories(id: Optional[str] = Query(None, description="Alert ID to fetch (if not provided, fetch latest)")):
    """Get all available categories from the specified alert data (by id or latest)"""
    try:
        logger.info("Fetching categories from the alert..." if not id else f"Fetching categories from alert id: {id}")
        alert = get_alert_by_id(id) if id else get_latest_alert()
        
        if alert is None:
            logger.warning("No alerts found for categories.")  # Log if no alert is found
            raise HTTPException(status_code=404, detail="No alerts found.")
        
        news_data = alert.get("news_data", [])
        
        # Extract unique categories
        categories = set()
        for news in news_data:
            category = news.get("category", "").strip()
            if category:  # Only add non-empty categories
                categories.add(category)
        
        logger.info(f"Returning categories: {sorted(list(categories))}")  # Log the categories being returned
        return {"categories": sorted(list(categories))}  # Return sorted list
    
    except HTTPException:
        logger.error("HTTPException raised while fetching categories.")  # Log if exception raised
        raise
    except Exception as e:
        logger.error(f"Error in fetching categories: {str(e)}")  # Log any errors
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/countries")
async def get_all_countries(id: Optional[str] = Query(None, description="Alert ID to fetch (if not provided, fetch latest)")):
    """Get all available countries from the specified alert data (by id or latest)"""
    try:
        logger.info("Fetching countries from the alert..." if not id else f"Fetching countries from alert id: {id}")
        alert = get_alert_by_id(id) if id else get_latest_alert()
        
        if alert is None:
            logger.warning("No alerts found for countries.")  # Log if no alert is found
            raise HTTPException(status_code=404, detail="No alerts found.")
        
        news_data = alert.get("news_data", [])
        
        # Extract unique countries
        countries = set()
        for news in news_data:
            country = news.get("country", "").strip()  # Assuming country data is stored under "country"
            if country:  # Only add non-empty countries
                countries.add(country)
        
        # List of countries to check
        important_countries = {"India", "China", "Russia", "Japan"}
        
        # Add important countries if they are not already in the list
        countries.update(important_countries)  # Add all important countries
        logger.info(f"Returning countries: {sorted(list(countries))}")  # Log the countries being returned
        
        return {"countries": sorted(list(countries))}  # Return sorted list
    
    except HTTPException:
        logger.error("HTTPException raised while fetching countries.")  # Log if exception raised
        raise
    except Exception as e:
        logger.error(f"Error in fetching countries: {str(e)}")  # Log any errors
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ids-dates")
async def get_alerts_ids_dates():
    """Get all alert ids and their corresponding dates as a list of arrays"""
    try:
        logger.info("Fetching all alert ids and dates...")
        id_date_list = get_alerts_id_date_list()
        return {"alerts": id_date_list}
    except Exception as e:
        logger.error(f"Error in fetching alert ids and dates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
