from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.twitter_fetcher import get_latest_twitter_data
from supabase_service.social_media_service import store_twitter_data
from loguru import logger
import pytz
from datetime import datetime

# Ensure logger is initialized
logger.add("app.log", level="INFO")

async def twitter_ingestion_job():
    """
    Scheduled job to fetch latest Twitter posts, process them, and store them.
    """
    try:
        # Step 1: Fetch raw Twitter data
        raw_tweets = await get_latest_twitter_data()
        logger.info(f"Total raw Twitter tweets fetched: {len(raw_tweets)}")
        
        if not raw_tweets:
            logger.warning("No Twitter tweets to process.")
            return

        # Step 2: Store filtered data in Supabase
        await store_twitter_data(raw_tweets)
        logger.success("Twitter tweets successfully processed and stored in Supabase.")
        
    except Exception as e:
        logger.error(f"Twitter ingestion job failed: {e}")

def start_twitter_scheduler():
    """
    Start the Twitter data ingestion scheduler
    """
    # Set the timezone (for example, Asia/Kolkata)
    tz = pytz.timezone('Asia/Kolkata')  # Adjust to your desired timezone

    # Create the scheduler with the specified timezone
    scheduler = AsyncIOScheduler(timezone=tz)

    # Schedule the job to run daily at 20:50 PM (IST)
    scheduler.add_job(
        twitter_ingestion_job,
        trigger=CronTrigger(hour=20, minute=50,timezone=tz),  # Daily at 20:50 PM IST
        name="twitter_ingestion_job"
    )

    scheduler.start()
    logger.info("Twitter scheduler started — Daily at 20:50 PM IST")

