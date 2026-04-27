import os
from loguru import logger
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from utils.genetic_scraper_pipeline import run_genetic_scraper_pipeline



def run_genetic_scraper_job():
    logger.info("Triggering genetic scraper pipeline...")
    run_genetic_scraper_pipeline()


def start_genetic_scraper_scheduler():
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))
    scheduler.add_job(run_genetic_scraper_pipeline, 'cron', day_of_week='mon', hour=9, minute=30,)
    scheduler.start()
    logger.info("Genetic scraper scheduler started.")
