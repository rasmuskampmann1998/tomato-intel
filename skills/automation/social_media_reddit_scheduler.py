from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.reddit_fetcher import get_latest_reddit_data
from supabase_service.social_media_service import store_reddit_data
from loguru import logger
import asyncio
import pytz
from datetime import datetime

# Ensure logger is initialized
logger.add("app.log", level="INFO")

async def reddit_ingestion_job():
    """
    Scheduled job to fetch latest Reddit posts and store them.
    """
    try:
        raw = await get_latest_reddit_data()  # Await the async coroutine
        logger.info(f"Total raw posts fetched: {len(raw)}")

        await store_reddit_data(raw)  # Assume this is also async
        logger.success("Reddit posts successfully stored in Supabase.")
    except Exception as e:
        logger.error(f"Reddit ingestion job failed: {e}")

def start_reddit_scheduler():
    """
    Start the Reddit data ingestion scheduler
    """
    # Set the timezone (for example, Asia/Kolkata)
    tz = pytz.timezone('Asia/Kolkata')  # Adjust to your desired timezone

    # Create the scheduler with the specified timezone
    scheduler = AsyncIOScheduler(timezone=tz)

    # Schedule the job to run daily at 20:40 PM (IST)
    scheduler.add_job(
        reddit_ingestion_job,
        trigger=CronTrigger(hour=20, minute=40,timezone=tz),  # Daily at 20:40 PM IST
        name="reddit_ingestion_job"
    )

    scheduler.start()
    logger.info("Reddit scheduler started — Daily at 20:40 PM IST")

