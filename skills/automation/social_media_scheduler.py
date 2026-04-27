from schedulers.social_media_reddit_scheduler import start_reddit_scheduler
from schedulers.social_media_facebook_scheduler import start_facebook_scheduler
from schedulers.social_media_linkedin_scheduler import start_linkedin_scheduler
from schedulers.social_media_twitter_shceduler import start_twitter_scheduler
from schedulers.social_media_instagram_scheduler import start_instagram_scheduler
from loguru import logger

logger.add("app.log", level="INFO") 

def start_social_media_scheduler():
    """
    Launch all social media scraping + processing jobs
    (extendable: Facebook, Instagram, etc.)
    """
    logger.info("Starting Social Media schedulers...")
    start_reddit_scheduler()
    start_facebook_scheduler()
    start_linkedin_scheduler()
    start_twitter_scheduler()
    start_instagram_scheduler()
    logger.success("All Social Media jobs scheduled.")
