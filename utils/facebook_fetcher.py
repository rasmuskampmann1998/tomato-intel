import os
import asyncio
from dotenv import load_dotenv
from apify_client import ApifyClient
from loguru import logger

# Load environment variables
load_dotenv()

# Configure logging
logger.add("app.log", level="INFO")

# Environment credentials
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

def _sync_facebook_scrape():
    """
    Synchronous Facebook scraping using Apify client
    """
    try:
        # Initialize the ApifyClient with your API token
        client = ApifyClient(APIFY_API_TOKEN)
        
        # Prepare the Actor input for Facebook agriculture/tomato search
        run_input = {
            "categories": [
                "tomato agriculture", 
                "tomato farming", 
                "tomato horticulture",
                "tomato organic farming",
                "tomato vegetable farming"
            ],
            "locations": [
                "India",
                "Denmark",
                "Asia",
                "Global",
                "Russia",
                "Japan",
                "USA",
                "China",
                "Africa"
            ],
            "resultsLimit": 25,
        }
        
        logger.info("Starting Facebook page scraping using Apify...")
        
        # Run the Actor and wait for it to finish
        run = client.actor("Us34x9p7VgjCz99H6").call(run_input=run_input)
        
        # Fetch the results
        results = [item for item in client.dataset(run["defaultDatasetId"]).iterate_items()]
        
        # Format the data to keep only required fields
        formatted_posts = []
        for item in results:
            try:
                formatted_post = {
                    "title": item.get("title", ""),
                    "likes": item.get("likes", 0),
                    "page_url": item.get("pageUrl", ""),
                    "categories": item.get("categories", []),
                    "followers": item.get("followers", 0),
                    "address": item.get("address", ""),
                    "phone_number": item.get("formatted_phone_number", ""),
                    "facebook_id": item.get("facebookId", ""),
                }
                formatted_posts.append(formatted_post)
            except Exception as e:
                logger.warning(f"Failed to format Facebook post: {e}")
                continue
        
        logger.info(f"Total Facebook pages fetched: {len(formatted_posts)}")
        return formatted_posts
        
    except Exception as e:
        logger.error(f"Facebook scraping failed: {e}")
        return []

async def get_latest_facebook_data():
    """
    Run the Facebook scraping safely in async environments using a thread.
    """
    return await asyncio.to_thread(_sync_facebook_scrape)