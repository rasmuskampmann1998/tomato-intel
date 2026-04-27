from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.instagram_fetcher import get_latest_instagram_data
from supabase_service.social_media_service import store_instagram_data
from loguru import logger
import pytz
from datetime import datetime

# Ensure logger is initialized
logger.add("app.log", level="INFO")

async def instagram_ingestion_job():
    """
    Scheduled job to fetch latest Instagram posts, process them, and store them.
    """
    try:
        # Step 1: Fetch raw Instagram data
        instagram_data = await get_latest_instagram_data()
        
        if not instagram_data:
            logger.warning("No Instagram data to process.")
            return

        top_posts_count = len(instagram_data.get("top_posts", []))
        latest_posts_count = len(instagram_data.get("latest_posts", []))
        
        logger.info(f"Instagram data fetched - Hashtag: #{instagram_data.get('hashtag_name', 'agriculture')}, Top posts: {top_posts_count}, Latest posts: {latest_posts_count}")

        # Step 2: Store data in Supabase
        await store_instagram_data(instagram_data)
        logger.success("Instagram data successfully processed and stored in Supabase.")
        
    except Exception as e:
        logger.error(f"Instagram ingestion job failed: {e}")

def start_instagram_scheduler():
    """
    Start the Instagram data ingestion scheduler
    """
    # Set the timezone (for example, Asia/Kolkata)
    tz = pytz.timezone('Asia/Kolkata')  # Adjust to your desired timezone

    # Create the scheduler with the specified timezone
    scheduler = AsyncIOScheduler(timezone=tz)

    # Schedule the job to run daily at 20:40 PM (IST)
    scheduler.add_job(
        instagram_ingestion_job,
        trigger=CronTrigger(hour=20, minute=10,timezone=tz),  # Daily at 20:40 PM IST
        name="instagram_ingestion_job"
    )
    
    scheduler.start()
    logger.info("Instagram scheduler started — Daily at 20:10 PM IST")

