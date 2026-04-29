"""
Search Discovery Scheduler — Daily multi-language SerpAPI news scraping.
Runs run_search_discovery() from scrapers/run_scrapers.py every day at 06:17.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger
import pytz

logger.add("app.log", level="INFO")


def search_discovery_job():
    logger.info("[SearchDiscovery] Starting scheduled multi-language search discovery...")
    try:
        from scrapers.run_scrapers import run_search_discovery, trigger_profile_matching
        saved = run_search_discovery()
        trigger_profile_matching()
        logger.success(f"[SearchDiscovery] Done — {saved} new items saved")
    except Exception as e:
        logger.error(f"[SearchDiscovery] Job failed: {e}")


def start_search_scraper_scheduler():
    scheduler = BackgroundScheduler()
    tz = pytz.timezone("Asia/Kolkata")

    scheduler.add_job(
        search_discovery_job,
        "cron",
        hour=6,
        minute=17,
        timezone=tz,
    )

    scheduler.start()
    logger.info("[SearchDiscovery] Scheduler started — daily at 06:17 IST")
    return scheduler
