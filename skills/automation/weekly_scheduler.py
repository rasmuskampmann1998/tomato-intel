from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from supabase_service.weekly_service import generate_and_store_weekly_data
from loguru import logger
import pytz

# Ensure logger is initialized
logger.add("app.log", level="INFO")

async def weekly_data_ingestion_job():
    """
    Scheduled job to generate weekly data report and store in Supabase.
    """
    try:
        await generate_and_store_weekly_data()
        logger.success("Weekly data report successfully generated and stored.")
    except Exception as e:
        logger.error(f"Weekly data ingestion job failed: {e}")

def start_weekly_data_scheduler():
    """
    Start the Weekly Data Ingestion Scheduler
    """
    tz = pytz.timezone('Asia/Kolkata')
    scheduler = AsyncIOScheduler(timezone=tz)

    scheduler.add_job(
        weekly_data_ingestion_job,
        trigger=CronTrigger(day_of_week='sat', hour=12, minute=10, timezone=tz),  # Every Monday at 10:10 IST
        name="weekly_data_ingestion_job"
    )

    scheduler.start()
    logger.info("Weekly data scheduler started — Every saturday at 11:59 AM IST")
