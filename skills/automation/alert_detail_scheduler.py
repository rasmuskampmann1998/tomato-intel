# from apscheduler.schedulers.background import BackgroundScheduler
# from supabase_service.alert_detail_service import store_alert_detail_data
# import asyncio

# def alert_detail_job():
#     """Scheduled job to generate and store the alert details."""
#     print("Generating and storing alert details...")
#     try:
#         # Await the asynchronous function
#         asyncio.run(store_alert_detail_data())
#         print("Alert details generated and stored successfully.")
#     except Exception as e:
#         print(f"Error while generating alert details: {e}")

# def start_alert_detail_scheduler():
#     """Start the alert details scheduler."""
#     scheduler = BackgroundScheduler()

#     # Schedule the job to run every day at 6:15 PM (adjust timing as needed)
#     scheduler.add_job(alert_detail_job, 'cron', hour=11, minute=36)
#     scheduler.start()
#     print("Scheduler started for alert details at 6:15 PM.")

from apscheduler.schedulers.background import BackgroundScheduler
from supabase_service.alert_detail_service import store_alert_detail_data
import asyncio
from loguru import logger
import pytz
from datetime import datetime

# Configure Loguru to write logs to app.log
logger.add("app.log", level="INFO")

def alert_detail_job():
    """
    Scheduled job to generate and store alert details.
    This job runs the `store_alert_detail_data()` async function via asyncio.
    """
    logger.info("Starting alert detail job...")

    try:
        asyncio.run(store_alert_detail_data())
        logger.success("Alert details generated and stored successfully.")
    except Exception as e:
        logger.error(f"Error while generating alert details: {e}")

def start_alert_detail_scheduler():
    """
    Start the alert details scheduler.
    Schedules `alert_detail_job` to run daily at 17:21 PM (adjustable).
    """
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))  # Set timezone to IST

    # Schedule the job to run daily at 17:21 PM
    scheduler.add_job(alert_detail_job, 'cron', hour=21, minute=15)

    scheduler.start()
    logger.info("Scheduler started for alert details — Daily at 21:15 PM IST.")
