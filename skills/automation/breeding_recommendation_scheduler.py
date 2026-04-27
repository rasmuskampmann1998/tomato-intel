# from apscheduler.schedulers.background import BackgroundScheduler
# from supabase_service.breeding_service import generate_and_store_breeding_recommendation
# import asyncio

# def breeding_recommendation_job():
#     """Scheduled job to generate and store the breeding recommendation."""
#     print("Generating and storing breeding recommendation...")
#     try:
#         # Await the asynchronous function
#         asyncio.run(generate_and_store_breeding_recommendation())
#         print("Breeding recommendation generated and stored successfully.")
#     except Exception as e:
#         print(f"Error while generating recommendation: {e}")

# def start_breeding_recommendation_scheduler():
#     """Start the breeding recommendation scheduler."""
#     scheduler = BackgroundScheduler()

#     # Schedule the job to run every day at 6:40 PM
#     scheduler.add_job(breeding_recommendation_job, 'cron', hour=15, minute=31)
#     scheduler.start()
#     print("Scheduler started for breeding recommendations at 6:40 PM.")
from apscheduler.schedulers.background import BackgroundScheduler
from supabase_service.breeding_service import generate_and_store_breeding_recommendation
import asyncio
from loguru import logger
import pytz
from datetime import datetime

# Configure logger to write logs into a file
logger.add("app.log", level="INFO")

def breeding_recommendation_job():
    """
    Scheduled job to generate and store breeding recommendations.
    It uses asyncio to run the asynchronous function.
    """
    logger.info("🌱 Starting breeding recommendation generation job...")
    try:
        asyncio.run(generate_and_store_breeding_recommendation())
        logger.success("Breeding recommendations generated and stored successfully.")
    except Exception as e:
        logger.error(f"Error while generating breeding recommendation: {e}")

def start_breeding_recommendation_scheduler():
    """
    Start the APScheduler job to run every Wednesday at 20:50 PM.
    """
    # Set the timezone (for example, Asia/Kolkata)
    tz = pytz.timezone('Asia/Kolkata')  # Adjust to your desired timezone

    # Create the scheduler with the specified timezone
    scheduler = BackgroundScheduler(timezone=tz)

    # Schedule the job every Wednesday at 20:50 PM
    scheduler.add_job(
        breeding_recommendation_job,
        'cron',
        day_of_week='sat',  # Specify Wednesday
        hour=10,             # Hour 20 (8:00 PM)
        minute=50            # Minute 50 (8:50 PM)
    )

    scheduler.start()
    logger.info("Scheduler started for breeding recommendations - Weekly on saturday at 10:50 AM IST.")

    return scheduler
