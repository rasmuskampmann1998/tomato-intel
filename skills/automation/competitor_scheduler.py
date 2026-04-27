# from apscheduler.schedulers.background import BackgroundScheduler
# from supabase_service.competitor_service import store_competitor_data
# import asyncio

# def competitor_job():
#     print("Running competitor data scheduler...")
#     try:
#         asyncio.run(store_competitor_data())
#         print("Competitor data job complete.")
#     except Exception as e:
#         print(f"Competitor job failed: {e}")

# def start_competitor_scheduler():
#     scheduler = BackgroundScheduler()
#     scheduler.add_job(competitor_job, 'cron', hour=17, minute=9)  # Adjust time as needed
#     scheduler.start()
#     print("Competitor scheduler started.")

# competitor_scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from supabase_service.competitor_service import store_competitor_data
from loguru import logger
import asyncio
import pytz
from datetime import datetime

# Configure log file output
logger.add("app.log", level="INFO")


def competitor_job():
    """
    Scheduled job to fetch and store competitor data into Supabase.
    Runs the asynchronous `store_competitor_data()` function.
    """
    logger.info("Starting competitor data scheduler job...")
    try:
        asyncio.run(store_competitor_data())
        logger.success("Competitor data fetched and stored successfully.")
    except Exception as e:
        logger.error(f"Competitor job failed: {e}")


def start_competitor_scheduler():
    """
    Starts the competitor scheduler to run weekly on Saturdays at 11:45 AM.
    """
    # Set the timezone (for example, Asia/Kolkata)
    tz = pytz.timezone('Asia/Kolkata')  # Adjust to your desired timezone

    # Create the scheduler with the specified timezone
    scheduler = BackgroundScheduler(timezone=tz)

    # Schedule the job to run weekly on Saturday at 11:45 AM
    scheduler.add_job(
        competitor_job,
        trigger='cron',
        day_of_week='sun',  # Saturday
        hour=21,            # 11 AM
        minute=10,          # 45 minutes
        id="competitor_data_job"
    )

    scheduler.start()
    logger.info("Competitor scheduler started - Weekly on Sundays at 21:10 AM IST.")

    return scheduler
