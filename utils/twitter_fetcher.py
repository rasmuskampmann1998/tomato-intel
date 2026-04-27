import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from apify_client import ApifyClient
from loguru import logger

# Load environment variables
load_dotenv()

# Configure logging
logger.add("app.log", level="INFO")

# Environment credentials
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

def get_24_hour_time_range():
    """
    Calculate the time range for the last 24 hours in UTC
    Returns tuple of (since, until) in the required format
    """
    # Get current UTC time
    now_utc = datetime.utcnow()
    
    # Calculate 48 hours ago
    hours_24_ago = now_utc - timedelta(hours=24)
    
    # Format in the required format: YYYY-MM-DD_HH:MM:SS_UTC
    since = hours_24_ago.strftime("%Y-%m-%d_%H:%M:%S_UTC")
    until = now_utc.strftime("%Y-%m-%d_%H:%M:%S_UTC")
    
    logger.info(f"Time range - Since: {since}, Until: {until}")
    
    return since, until

def _sync_twitter_scrape():
    """
    Synchronous Twitter scraping using Apify client with 24-hour time filter
    """
    try:
        # Initialize the ApifyClient with your API token
        client = ApifyClient(APIFY_API_TOKEN)
        
        # Get the 24-hour time range
        since, until = get_24_hour_time_range()
        
        # Prepare the Actor input
        run_input = {
            "searchTerms": [
                "tomato agriculture news",
                "tomato farming technology", 
                "tomato climate agriculture",
                "tomato crop yields",
                "tomato global agriculture trends",
                "tomato sustainable farming",
                "tomato innovation",
                "tomato disease research"
            ],
            "tweetLanguage": "en",  # English language
            "sort": "Latest",       # Latest tweets
            "maxItems": 50,         # Limit to 50 tweets
            "minimumRetweets": 30,   # Filter for meaningful tweets
            "minimumFavorites": 10,
            "minimumReplies": 30,
            "since": since,         # Start of 24-hour window
            "until": until,         # End of 24-hour window (now)
            "queryType": "Latest",
            "min_faves": 10,
            "min_replies": 30,
            "min_retweets": 30,
            "-min_replies": 30,
            "customMapFunction": "(object) => { return {...object} }"
        }
        
        logger.info("Starting Twitter posts scraping using Apify...")
        logger.info(f"Filtering tweets from last 24 hours: {since} to {until}")
        
        # Run the Actor and wait for it to finish
        run = client.actor("CJdippxWmn9uRfooo").call(run_input=run_input)
        
        # Fetch the results
        results = [item for item in client.dataset(run["defaultDatasetId"]).iterate_items()]
        
        # Format the data to keep only required fields
        formatted_tweets = []
        for item in results:
            try:
                # Extract author information
                author = item.get("author", {})
                
                formatted_tweet = {
                    "user_name": author.get("userName", ""),
                    "twitter_profile_url": author.get("twitterUrl", ""),
                    "text": item.get("text", ""),
                    "url": item.get("url", ""),
                    "view_count": item.get("viewCount", 0),
                    "retweet_count": item.get("retweetCount", 0),
                    "like_count": item.get("likeCount", 0),
                    "reply_count": item.get("replyCount", 0),
                    "lang": item.get("lang", ""),
                    "is_blue_verified": author.get("isBlueVerified", False),
                    "profile_picture": author.get("profilePicture", ""),
                    "cover_picture": author.get("coverPicture", ""),
                    "location": author.get("location", ""),
                    "followers": author.get("followers", 0),
                    "following": author.get("following", 0),
                    "created_at": item.get("createdAt", ""),
                    "tweet_id": item.get("id", ""),
                }
                formatted_tweets.append(formatted_tweet)
            except Exception as e:
                logger.warning(f"Failed to format Twitter tweet: {e}")
                continue
        
        logger.info(f"Total Twitter tweets fetched from last 24 hours: {len(formatted_tweets)}")
        return formatted_tweets
        
    except Exception as e:
        logger.error(f"Twitter scraping failed: {e}")
        return []

async def get_latest_twitter_data():
    """
    Run the Twitter scraping safely in async environments using a thread.
    """
    return await asyncio.to_thread(_sync_twitter_scrape)