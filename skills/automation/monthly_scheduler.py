from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from supabase_service.monthly_service import generate_and_store_monthly_data
from loguru import logger
import pytz
from datetime import datetime

# Ensure logger is initialized
logger.add("app.log", level="INFO")

async def monthly_data_ingestion_job():
    """
    Scheduled job to generate monthly data report and store in Supabase.
    """
    try:
        await generate_and_store_monthly_data()
        logger.success("Monthly data report successfully generated and stored.")
    except Exception as e:
        logger.error(f"Monthly data ingestion job failed: {e}")

def start_monthly_data_scheduler():
    """
    Start the Monthly Data Ingestion Scheduler
    """
    tz = pytz.timezone('Asia/Kolkata')
    scheduler = AsyncIOScheduler(timezone=tz)

    # Schedule to run every 30th day of the month at 16:05 IST
    scheduler.add_job(
        monthly_data_ingestion_job,
        trigger=CronTrigger(day=12, hour=12, minute=20, timezone=tz),
        name="monthly_data_ingestion_job"
    )

    scheduler.start()
    logger.info("Monthly data scheduler started — will run on the 30th of every month at 16:05 IST.")
