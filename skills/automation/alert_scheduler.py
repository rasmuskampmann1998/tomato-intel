# from apscheduler.schedulers.background import BackgroundScheduler
# from supabase_service.alert_service import consolidate_and_store_alert_data
# import asyncio

# def alert_job():
#     """Scheduled job to consolidate and store alert data from alert_details and alerts tables."""
#     print(" Consolidating and storing alert data...")
#     try:
#         asyncio.run(consolidate_and_store_alert_data())
#         print(" Alert data consolidated and stored successfully.")
#     except Exception as e:
#         print(f" Error while consolidating alert data: {e}")

# def start_alert_scheduler():
#     """Start the scheduler for alert consolidation."""
#     scheduler = BackgroundScheduler()

#     # Schedule job to run daily at 6:40 PM
#     scheduler.add_job(alert_job, 'cron', hour=14, minute=24)

#     scheduler.start()
#     print(" Scheduler started to consolidate alerts at 6:40 PM.")



from apscheduler.schedulers.background import BackgroundScheduler
from supabase_service.alert_service import consolidate_and_store_alert_data
import asyncio
from datetime import datetime
from loguru import logger
import pytz

# Configure loguru to log into file
logger.add("app.log", level="INFO")

def alert_job():
    logger.info("Starting alert data consolidation job...")
    try:
        asyncio.run(consolidate_and_store_alert_data())
        logger.success("Alert data consolidated and stored successfully.")
    except Exception as e:
        logger.error(f"Error while consolidating alert data: {e}")

def start_alert_scheduler():
    scheduler = BackgroundScheduler()
    tz = pytz.timezone("Asia/Kolkata")  # Adjust timezone as needed

    # Schedule job at 15:33 on every Monday (0) and Thursday (3)
    scheduler.add_job(
        alert_job,
        'cron',
        day_of_week='mon,thu',
        hour=10,
        minute=37,
        timezone=tz
    )

    scheduler.start()
    logger.info("Scheduler started to consolidate alerts every Monday and Thursday at 15:33.")

    return scheduler
