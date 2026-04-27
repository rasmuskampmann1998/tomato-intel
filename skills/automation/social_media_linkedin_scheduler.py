from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.linkedin_fetcher import get_latest_linkedin_data
from supabase_service.social_media_service import store_linkedin_data
from loguru import logger
import pytz
from datetime import datetime

# Ensure logger is initialized
logger.add("app.log", level="INFO")

async def linkedin_ingestion_job():
    """
    Scheduled job to fetch latest LinkedIn posts, process them, and store them.
    """
    try:
        # Step 1: Fetch raw LinkedIn data
        raw_posts = await get_latest_linkedin_data()
        logger.info(f"Total raw LinkedIn posts fetched: {len(raw_posts)}")
        
        if not raw_posts:
            logger.warning("No LinkedIn posts to process.")
            return

        # Step 2: Store filtered data in Supabase
        await store_linkedin_data(raw_posts)
        logger.success("LinkedIn posts successfully processed and stored in Supabase.")
        
    except Exception as e:
        logger.error(f"LinkedIn ingestion job failed: {e}")

def start_linkedin_scheduler():
    """
    Start the LinkedIn data ingestion scheduler
    """
    # Set the timezone (for example, Asia/Kolkata)
    tz = pytz.timezone('Asia/Kolkata')  # Adjust to your desired timezone

    # Create the scheduler with the specified timezone
    scheduler = AsyncIOScheduler(timezone=tz)

    # Schedule the job to run daily at 20:30 PM (IST)
    scheduler.add_job(
        linkedin_ingestion_job,
        trigger=CronTrigger(hour=20, minute=30,timezone=tz),  # Daily at 20:30 PM IST
        name="linkedin_ingestion_job"
    )
    
    scheduler.start()
    logger.info("LinkedIn scheduler started — Daily at 20:30 PM IST")

