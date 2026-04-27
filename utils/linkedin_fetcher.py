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

def _sync_linkedin_scrape():
    """
    Synchronous LinkedIn scraping using Apify client
    """
    try:
        # Initialize the ApifyClient with your API token
        client = ApifyClient(APIFY_API_TOKEN)
        
        # Prepare the Actor input to fetch agriculture-related content
        run_input = {
            "keyword": "tomato innovation, tomato farming, tomato technology, tomato patents, tomato research, tomato crop, tomato trends, heirloom tomatoes, tomato disease, tomato pests, tomato care",
            "sort_type": "relevance",      # Sort by relevance
            "page_number": 1,              # Start from page 1
            "date_filter": "",    # Empty string for no date filter
            "limit": 50,                   # Limit to 50 items
        }
        
        logger.info("Starting LinkedIn posts scraping using Apify...")
        
        # Run the Actor and wait for it to finish
        run = client.actor("apimaestro/linkedin-posts-search-scraper-no-cookies").call(run_input=run_input)
        
        # Fetch the results
        results = [item for item in client.dataset(run["defaultDatasetId"]).iterate_items()]
        
        # Format the data to keep only required fields
        formatted_posts = []
        for item in results:
            try:
                # Extract author information
                author = item.get("author", {})
                stats = item.get("stats", {})
                posted_at = item.get("posted_at", {})
                
                formatted_post = {
                    "author_name": author.get("name", ""),
                    "author_profile_url": author.get("profile_url", ""),
                    "text": item.get("text", ""),
                    "post_url": item.get("post_url", ""),
                    "hashtags": item.get("hashtags", []),
                    "total_reactions": stats.get("total_reactions", 0),
                    "comments": stats.get("comments", 0),
                    "shares": stats.get("shares", 0),
                    "posted_date": posted_at.get("date", ""),
                    "activity_id": item.get("activity_id", ""),
                }
                formatted_posts.append(formatted_post)
            except Exception as e:
                logger.warning(f"Failed to format LinkedIn post: {e}")
                continue
        
        logger.info(f"Total LinkedIn posts fetched: {len(formatted_posts)}")
        return formatted_posts
        
    except Exception as e:
        logger.error(f"LinkedIn scraping failed: {e}")
        return []

async def get_latest_linkedin_data():
    """
    Run the LinkedIn scraping safely in async environments using a thread.
    """
    return await asyncio.to_thread(_sync_linkedin_scrape)