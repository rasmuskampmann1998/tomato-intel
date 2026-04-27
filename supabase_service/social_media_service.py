from core.settings import supabase
from loguru import logger
from datetime import datetime

logger.add("app.log", level="INFO") 

SOCIAL_MEDIA_TABLE = "social_media"

async def store_reddit_data(filtered_posts: list):
    """
    Save all filtered Reddit posts as a single JSON array in one Supabase row
    """
    if not filtered_posts:
        logger.warning("No filtered Reddit posts to store.")
        return

    try:
        supabase.table(SOCIAL_MEDIA_TABLE).insert({
            "source": "reddit",
            "date": datetime.utcnow().isoformat(),
            "data": filtered_posts  # store the entire array in one row
        }).execute()
        logger.info(f"Stored {len(filtered_posts)} Reddit posts in one Supabase row.")
    except Exception as e:
        logger.error(f"Failed to store Reddit posts: {e}")

async def fetch_latest_reddit_posts():
    """
    Fetch latest Reddit posts from Supabase.

    Args:
        limit (int): Number of posts to fetch.

    Returns:
        List of Reddit posts or raises Exception
    """
    try:
        response = supabase.table(SOCIAL_MEDIA_TABLE) \
            .select("*") \
            .eq("source", "reddit") \
            .order("date", desc=True) \
            .limit(1) \
            .execute()

        logger.info(f" Fetched {len(response.data)} Reddit posts from Supabase.")
        return response.data
    except Exception as e:
        logger.error(f" Error fetching Reddit posts: {e}")
        raise



async def store_facebook_data(filtered_posts: list):
    """
    Save all filtered Facebook posts as a single JSON array in one Supabase row
    """
    if not filtered_posts:
        logger.warning("No filtered Facebook posts to store.")
        return

    try:
        supabase.table(SOCIAL_MEDIA_TABLE).insert({
            "source": "facebook",
            "date": datetime.utcnow().isoformat(),
            "data": filtered_posts  # store the entire array in one row
        }).execute()
        logger.info(f"Stored {len(filtered_posts)} Facebook posts in one Supabase row.")
    except Exception as e:
        logger.error(f"Failed to store Facebook posts: {e}")


async def store_facebook_data(filtered_pages: list):
    """
    Save all filtered Facebook pages as a single JSON array in one Supabase row
    """
    if not filtered_pages:
        logger.warning("No filtered Facebook pages to store.")
        return

    try:
        supabase.table(SOCIAL_MEDIA_TABLE).insert({
            "source": "facebook",
            "date": datetime.utcnow().isoformat(),
            "data": filtered_pages  # store the entire array in one row
        }).execute()
        logger.info(f"Stored {len(filtered_pages)} Facebook pages in one Supabase row.")
    except Exception as e:
        logger.error(f"Failed to store Facebook pages: {e}")

async def fetch_latest_facebook_posts():
    """
    Fetch latest Facebook pages from Supabase.

    Returns:
        List of Facebook pages or raises Exception
    """
    try:
        response = supabase.table(SOCIAL_MEDIA_TABLE) \
            .select("*") \
            .eq("source", "facebook") \
            .order("date", desc=True) \
            .limit(1) \
            .execute()

        logger.info(f"Fetched {len(response.data)} Facebook records from Supabase.")
        return response.data
    except Exception as e:
        logger.error(f"Error fetching Facebook pages: {e}")
        raise


async def store_linkedin_data(filtered_posts: list):
    """
    Save all filtered LinkedIn posts as a single JSON array in one Supabase row
    """
    if not filtered_posts:
        logger.warning("No filtered LinkedIn posts to store.")
        return

    try:
        supabase.table(SOCIAL_MEDIA_TABLE).insert({
            "source": "linkedin",
            "date": datetime.utcnow().isoformat(),
            "data": filtered_posts  # store the entire array in one row
        }).execute()
        logger.info(f"Stored {len(filtered_posts)} LinkedIn posts in one Supabase row.")
    except Exception as e:
        logger.error(f"Failed to store LinkedIn posts: {e}")

async def fetch_latest_linkedin_posts():
    """
    Fetch latest LinkedIn posts from Supabase.

    Returns:
        List of LinkedIn posts or raises Exception
    """
    try:
        response = supabase.table(SOCIAL_MEDIA_TABLE) \
            .select("*") \
            .eq("source", "linkedin") \
            .order("date", desc=True) \
            .limit(1) \
            .execute()

        logger.info(f"Fetched {len(response.data)} LinkedIn records from Supabase.")
        return response.data
    except Exception as e:
        logger.error(f"Error fetching LinkedIn posts: {e}")
        raise


async def store_twitter_data(filtered_tweets: list):
    """
    Save all filtered Twitter tweets as a single JSON array in one Supabase row
    """
    if not filtered_tweets:
        logger.warning("No filtered Twitter tweets to store.")
        return

    try:
        supabase.table(SOCIAL_MEDIA_TABLE).insert({
            "source": "twitter",
            "date": datetime.utcnow().isoformat(),
            "data": filtered_tweets  # store the entire array in one row
        }).execute()
        logger.info(f"Stored {len(filtered_tweets)} Twitter tweets in one Supabase row.")
    except Exception as e:
        logger.error(f"Failed to store Twitter tweets: {e}")

async def fetch_latest_twitter_posts():
    """
    Fetch latest Twitter posts from Supabase.

    Returns:
        List of Twitter posts or raises Exception
    """
    try:
        response = supabase.table(SOCIAL_MEDIA_TABLE) \
            .select("*") \
            .eq("source", "twitter") \
            .order("date", desc=True) \
            .limit(1) \
            .execute()

        logger.info(f"Fetched {len(response.data)} Twitter records from Supabase.")
        return response.data
    except Exception as e:
        logger.error(f"Error fetching Twitter posts: {e}")
        raise



async def store_instagram_data(instagram_data: dict):
    """
    Save Instagram hashtag data as a single JSON object in one Supabase row
    """
    if not instagram_data:
        logger.warning("No Instagram data to store.")
        return

    try:
        supabase.table(SOCIAL_MEDIA_TABLE).insert({
            "source": "instagram",
            "date": datetime.utcnow().isoformat(),
            "data": instagram_data  # store the entire hashtag data object in one row
        }).execute()
        
        top_posts_count = len(instagram_data.get("top_posts", []))
        latest_posts_count = len(instagram_data.get("latest_posts", []))
        
        logger.info(f"Stored Instagram data for #{instagram_data.get('hashtag_name', 'agriculture')} - Top posts: {top_posts_count}, Latest posts: {latest_posts_count}")
    except Exception as e:
        logger.error(f"Failed to store Instagram data: {e}")

async def fetch_latest_instagram_posts():
    """
    Fetch latest Instagram posts from Supabase.

    Returns:
        List of Instagram posts or raises Exception
    """
    try:
        response = supabase.table(SOCIAL_MEDIA_TABLE) \
            .select("*") \
            .eq("source", "instagram") \
            .order("date", desc=True) \
            .limit(1) \
            .execute()

        logger.info(f"Fetched {len(response.data)} Instagram records from Supabase.")
        return response.data
    except Exception as e:
        logger.error(f"Error fetching Instagram posts: {e}")
        raise