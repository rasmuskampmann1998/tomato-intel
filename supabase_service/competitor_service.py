import asyncio
from datetime import datetime
from fastapi import HTTPException
from core.settings import supabase
from loguru import logger
from scrapers.competitor_data import Crawl4AICompetitorScraper
from utils.markdown_to_text import markdown_to_plaintext
from llm_services.competitor_data import generate_competitor_data_llm

logger.add("app.log", level="INFO") 

competitor_urls = {
    "https://www.syngenta.com/": "Syngenta",
    "https://rijkzwaan.com/en/home": "Rijk Zwaan",
    "https://www.bayer.com/en/agriculture-overview": "Bayer CropScience",
    "https://www.bejo.com/": "Bejo",
    "https://www.corteva.com/": "Corteva Agriscience",
    "https://www.kws.com/": "KWS Saat"
}

async def store_competitor_data():
    """
    Scrapes competitor websites, converts to text, processes with LLM,
    and stores structured competitor data in Supabase.
    """
    try:
        logger.info("Starting competitor scraping and storage process")
        scraper = Crawl4AICompetitorScraper()
        all_raw_texts = []

        for url, name in competitor_urls.items():
            logger.info(f"Scraping {name} - {url}")
            markdown = await scraper.scrape(url)
            if not markdown.strip():
                logger.warning(f"No content for {name}")
                continue

            plain_text = markdown_to_plaintext(markdown)
            all_raw_texts.append({
                "url": url,
                "name": name,
                "text": plain_text
            })

        if not all_raw_texts:
            raise Exception("No valid content was scraped from any competitor.")

        # Send ALL plain texts to the LLM for structured extraction
        llm_response = await generate_competitor_data_llm(all_raw_texts)

        if not llm_response or not llm_response.get("competitor_data"):
            raise Exception("LLM did not return valid competitor data")

        payload = {
            "date": str(datetime.now().date()),
            "competitor_data": llm_response["competitor_data"]
        }

        response = supabase.table("competitor_data").insert(payload).execute()
        if not response.data:
            raise Exception("Failed to store competitor data in Supabase.")

        logger.info("Competitor data stored successfully.")
        return response.data

    except Exception as e:
        logger.error(f"Error in store_competitor_data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def get_latest_competitor_data():
    """
    Fetch the latest competitor data from the Supabase database.
    
    Returns:
    - dict: The latest competitor data stored in the database.
    
    Raises:
    - HTTPException: If no competitor data is found.
    """
    try:
        # Query the "competitor_data" table to get the latest entry, ordered by "created_at"
        response = supabase.table("competitor_data").select("*").order("created_at", desc=True).limit(1).execute()
        
        # If no data is returned, handle the case where no data is found
        if not response.data:
            logger.warning("No competitor data found.")
            return None  # Return None or handle as appropriate for your application

        # Return the latest competitor data (first row)
        return response.data[0]
    
    except Exception as e:
        logger.error(f"Error fetching latest competitor data: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching competitor data.")
