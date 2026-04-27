import json

from fastapi import HTTPException
from core.settings import supabase
from datetime import date, datetime

from llm_services.breeding_recommendation import generate_breeding_recommendations_llm
from loguru import logger

logger.add("app.log", level="INFO") 

async def generate_and_store_breeding_recommendation():
    """Generate and store the breeding recommendation."""
    
    # Step 1: Generate the breeding recommendation using the LLM service
    breeding_data = await generate_breeding_recommendations_llm()
    
    if breeding_data is None:
        print("❌ Failed to generate breeding recommendations")
        raise HTTPException(status_code=500, detail="Failed to generate breeding recommendations")

    # Step 2: Check your table schema first and only include existing columns
    # Option A: If you want to include global_market_overview, add it to your table first
    breeding_recommendation_data = {
        "date": str(datetime.now().date()),  # today's date
        "breeding_recommendation": breeding_data.get("breeding_recommendation", []),  # Extract just the array
    }
    

    try:

        response = supabase.table("breeding_recommendations").insert(breeding_recommendation_data).execute()

        if response.data:
            logger.info("Breeding recommendation stored successfully.")
            print("✅ Breeding recommendation stored successfully.")
        else:
            logger.warning("Failed to store breeding recommendation.")
            print("⚠️ Failed to store breeding recommendation - no data returned")

        return response.data

    except Exception as e:
        logger.error(f"Error while storing breeding recommendation: {str(e)}")
        print(f"❌ Error while storing breeding recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error while storing breeding recommendation: {str(e)}")


def get_latest_breeding_recommendation():
    """Get the latest breeding recommendation from the database."""
    response = supabase.table("breeding_recommendations").select("*").order("created_at", desc=True).limit(1).execute()
    
    # Check if there is any data returned, handle the case where no data is found
    if not response.data:
        logger.warning("No breeding recommendations found in the database.")
        return None  # Return None or handle as appropriate for your application

    return response.data[0]  # Return the first (latest) recommendation
