from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.facebook_fetcher import get_latest_facebook_data
from supabase_service.social_media_service import store_facebook_data
from loguru import logger
import pytz
from datetime import datetime

# Ensure logger is initialized
logger.add("app.log", level="INFO")

async def facebook_ingestion_job():
    """
    Scheduled job to fetch latest Facebook pages, process them, and store them.
    """
    try:
        # Step 1: Fetch raw Facebook data
        raw_pages = await get_latest_facebook_data()
        logger.info(f"Total raw Facebook pages fetched: {len(raw_pages)}")
        
        if not raw_pages:
            logger.warning("No Facebook pages to process.")
            return

        # Step 2: Store filtered data in Supabase
        await store_facebook_data(raw_pages)
        logger.success("Facebook pages successfully processed and stored in Supabase.")
        
    except Exception as e:
        logger.error(f"Facebook ingestion job failed: {e}")

def start_facebook_scheduler():
    """
    Start the Facebook data ingestion scheduler
    """
    # Set the timezone (for example, Asia/Kolkata)
    tz = pytz.timezone('Asia/Kolkata')  # Adjust to your desired timezone

    # Create the scheduler with the specified timezone
    scheduler = AsyncIOScheduler(timezone=tz)

    # Schedule the job to run daily at 17:15 PM (IST)
    scheduler.add_job(
        facebook_ingestion_job,
        trigger=CronTrigger(hour=20, minute=00,timezone=tz),  # Daily at 17:15 PM IST
        name="facebook_ingestion_job"
    )
    
    scheduler.start()
    logger.info("Facebook scheduler started — Daily at 20:00 PM IST")

