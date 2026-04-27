from datetime import datetime
from fastapi import HTTPException
from core.settings import supabase
from loguru import logger
from scrapers.alerts_detail_scraper import Crawl4AINewsScraper
from utils.markdown_to_text import markdown_to_plaintext
from llm_services.alert_detail import generate_alert_detail_llm

logger.add("app.log", level="INFO") 

# Updated alert_detail_urls with additional sources
alert_detail_urls = [
    # Tomato-specific
    "https://www.tomatonews.com/en/",
    "https://www.tomatonews.com/en/trade_46.html",
    "https://www.tomatoland.com/crops/",
    "https://vegetablegrowersnews.com/category/vegetables/tomatoespeppers/",

    # Top Horticulture & Agriculture Sources
    "https://www.hortidaily.com/",
    "https://www.mdpi.com/journal/horticulturae",
    "https://academic.oup.com/hr",
    "https://apnews.com/hub/agriculture",
    "https://www.icar.org.in/",
    "https://krishijagran.com/",
    "https://www.agrinews.in/",
    "https://www.apsaseed.org/",
    "https://www.jircas.go.jp/en",
    "https://www.cimmyt.org/",
    "https://agritech.tnau.ac.in/",
    "https://www.chinadaily.com.cn/",
    "https://www.nikkei.com/",
    "https://www.caas.cn/en/",
    "https://www.fao.org/india",
    "https://veggiesfrommexico.com/",
    "https://www.seedworld.com/",
    "https://www.hortweek.com/",
    "https://www.farminguk.com/news/",
    
    # New additional sources
    "https://www.gartner.com/en/newsroom",
    "https://www.gardenerworldmagazine.co.uk/",
    "https://hortiadvisor.com/",
    "https://www.gfmt.com/",
    "https://www.greentech.nl/",
    "https://www.horti-news.com/",
    "https://www.rkmp.co.in/",
    "https://www.biospectrumasia.com/",
    "https://www.urbanagriculture.in/"
]

# Helper function to scrape and convert a batch of URLs to plain text
async def scrape_and_process_batch(urls: list) -> str:
    scraper = Crawl4AINewsScraper()
    batch_plain_text = []

    for url in urls:
        try:
            logger.info(f"Scraping alert detail from {url}")
            markdown = await scraper.scrape(url)
            if not markdown.strip():
                logger.warning(f"No content found at {url}")
                continue

            plain_text = markdown_to_plaintext(markdown)
            batch_plain_text.append(plain_text)

        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")

    return "\n\n".join(batch_plain_text)

# Function to scrape and store alert details
async def store_alert_detail_data():
    """
    Scrapes news websites in three batches, processes with LLM, and stores the tomato-related insights in Supabase.
    """
    try:
        logger.info("Starting alert detail scraping and storage process")

        # Divide the URLs into three batches
        third = len(alert_detail_urls) // 3
        batch1_urls = alert_detail_urls[:third]
        batch2_urls = alert_detail_urls[third:2*third]
        batch3_urls = alert_detail_urls[2*third:]

        # Process each batch
        logger.info("Processing Batch 1")
        text1 = await scrape_and_process_batch(batch1_urls)

        logger.info("Processing Batch 2")
        text2 = await scrape_and_process_batch(batch2_urls)

        logger.info("Processing Batch 3")
        text3 = await scrape_and_process_batch(batch3_urls)

        if not text1 and not text2 and not text3:
            raise Exception("No valid content scraped from any URL.")

        # Send each batch to the LLM separately
        alerts_batch1 = await generate_alert_detail_llm(text1) if text1 else []
        alerts_batch2 = await generate_alert_detail_llm(text2) if text2 else []
        alerts_batch3 = await generate_alert_detail_llm(text3) if text3 else []

        # Combine all the alert sets with deduplication
        all_alerts = []
        seen_titles = set()
        
        # Process each batch with deduplication
        for batch_name, batch_alerts in [("Batch 1", alerts_batch1), ("Batch 2", alerts_batch2), ("Batch 3", alerts_batch3)]:
            logger.info(f"Processing {batch_name} with {len(batch_alerts)} alerts")
            for alert in batch_alerts:
                # Use title_translated as unique identifier for deduplication
                title = alert.get("title_translated", "").strip()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_alerts.append(alert)
                elif not title:
                    # If no title_translated, use summary_en as fallback
                    summary = alert.get("summary_en", "").strip()
                    if summary and summary not in seen_titles:
                        seen_titles.add(summary)
                        all_alerts.append(alert)
                    elif not summary:
                        # If no title or summary, add with a warning
                        logger.warning(f"Alert without title or summary found: {alert}")
                        all_alerts.append(alert)
        
        logger.info(f"Combined {len(all_alerts)} unique alerts after deduplication (from {len(alerts_batch1) + len(alerts_batch2) + len(alerts_batch3)} total)")

        if not all_alerts:
            raise HTTPException(status_code=500, detail="LLM returned empty alert results.")

        # Prepare final payload
        payload = {
            "date": str(datetime.now().date()),
            "news_data": all_alerts
        }

        # Store to Supabase
        response = supabase.table("alert_details").upsert(payload).execute()
        if not response.data:
            raise Exception("Failed to store alert details in Supabase.")

        logger.info("Alert details stored successfully.")
        return response.data

    except Exception as e:
        logger.error(f"Error in store_alert_detail_data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def get_latest_alert_details():
    """
    Fetch the latest alert details from the Supabase database.
    
    Returns:
    - dict: The latest alert details stored in the database.
    
    Raises:
    - HTTPException: If no alert details are found.
    """
    try:
        # Query the "alert_details" table to get the latest entry, ordered by "created_at"
        response = supabase.table("alert_details").select("*").order("created_at", desc=True).limit(1).execute()
        
        # If no data is returned, handle the case where no data is found
        if not response.data:
            logger.warning("No alert details found.")
            return None  # Return None or handle as appropriate for your application

        # Return the latest alert details (first row)
        return response.data[0]
    
    except Exception as e:
        logger.error(f"Error fetching latest alert details: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching alert details.")
