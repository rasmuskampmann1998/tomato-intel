import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from apify_client import ApifyClient
from loguru import logger

# Load environment variables
load_dotenv()

# Configure logging
logger.add("app.log", level="INFO")

# Environment credentials
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

def _sync_instagram_scrape():
    """
    Synchronous Instagram scraping using Apify client for agriculture hashtag
    """
    try:
        # Initialize the ApifyClient with your API token
        client = ApifyClient(APIFY_API_TOKEN)
        
        # Prepare the Actor input for hashtag search
        run_input = {
            "searchType": "hashtag",
            "search": "tomato agriculture",
            "searchLimit": 1,
            "resultsType": "posts",
            "onlyPostsNewerThan": "1 day",
            "resultsLimit": 20,  # Increased limit to get more posts
            "addParentData": False
        }
        
        logger.info("Starting Instagram posts scraping using Apify...")
        logger.info("Searching for #agriculture hashtag posts")
        
        # Run the Actor and wait for it to finish
        run = client.actor("apify/instagram-scraper").call(run_input=run_input)
        
        # Fetch the results
        results = [item for item in client.dataset(run["defaultDatasetId"]).iterate_items()]
        
        # Format the data to extract required fields
        formatted_data = {}
        
        # Process the results
        if results:
            # The API returns hashtag data directly at root level, not nested
            hashtag_data = results[0] if results else {}
            
            # Extract basic hashtag information
            formatted_data = {
                "hashtag_name": hashtag_data.get("name", "agriculture"),  # Changed from "hashtag" to "name"
                "posts_count": hashtag_data.get("postsCount", 0),
                "posts_per_day": hashtag_data.get("postsPerDay", 0),
                "top_posts": [],
                "latest_posts": []
            }
            
            # Process top posts
            top_posts = hashtag_data.get("topPosts", [])
            for post in top_posts:
                try:
                    formatted_post = {
                        "full_name": post.get("ownerFullName", ""),  # Direct access, not nested under owner
                        "username": post.get("ownerUsername", ""),   # Direct access, not nested under owner
                        "post_url": post.get("url", ""),
                        "caption": post.get("caption", ""),
                        "type": post.get("type", ""),
                        "hashtags": post.get("hashtags", []),
                        "mentions": post.get("mentions", []),
                        "comments_count": post.get("commentsCount", 0),
                        "likes_count": post.get("likesCount", 0),
                        "timestamp": post.get("timestamp", ""),
                        "is_sponsored": post.get("isSponsored", False)
                    }
                    formatted_data["top_posts"].append(formatted_post)
                except Exception as e:
                    logger.warning(f"Failed to format top post: {e}")
                    continue
            
            # Process latest posts
            latest_posts = hashtag_data.get("latestPosts", [])
            for post in latest_posts:
                try:
                    formatted_post = {
                        "full_name": post.get("ownerFullName", ""),  # Direct access, not nested under owner
                        "username": post.get("ownerUsername", ""),   # Direct access, not nested under owner
                        "post_url":  post.get("url", ""),
                        "caption": post.get("caption", ""),
                        "type": post.get("type", ""),
                        "mentions": post.get("mentions", []),
                        "hashtags": post.get("hashtags", []),
                        "comments_count": post.get("commentsCount", 0),
                        "likes_count": post.get("likesCount", 0),
                        "video_play_count": post.get("videoPlayCount", 0),
                        "video_view_count": post.get("videoViewCount", 0),
                        "timestamp": post.get("timestamp", ""),
                        "is_sponsored": post.get("isSponsored", False)
                    }
                    formatted_data["latest_posts"].append(formatted_post)
                except Exception as e:
                    logger.warning(f"Failed to format latest post: {e}")
                    continue
        
        logger.info(f"Instagram data processed - Hashtag: {formatted_data.get('hashtag_name')}")
        logger.info(f"Posts count: {formatted_data.get('posts_count')}, Posts per day: {formatted_data.get('posts_per_day')}")
        logger.info(f"Top posts: {len(formatted_data.get('top_posts', []))}, Latest posts: {len(formatted_data.get('latest_posts', []))}")
        return formatted_data
        
    except Exception as e:
        logger.error(f"Instagram scraping failed: {e}")
        return {}

async def get_latest_instagram_data():
    """
    Run the Instagram scraping safely in async environments using a thread.
    """
    return await asyncio.to_thread(_sync_instagram_scrape)