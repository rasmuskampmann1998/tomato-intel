# social_media_processor.py

import json
import random
from datetime import datetime, timedelta
from loguru import logger
from typing import List, Dict, Any


def process_facebook_posts_last_7_days(rows):
    """
    Given a list of Facebook rows (from Supabase), flatten all posts from the latest 7 rows and return the top 5 posts with the most likes in the format {"facebook": [ ... ]}. No duplicates allowed.
    """
    all_posts = []
    seen_facebook_ids = set()
    
    logger.info(f"Processing {len(rows)} Facebook rows")
    
    for row in rows:
        posts = row.get("data", [])
        if isinstance(posts, list):
            for post in posts:
                if not isinstance(post, dict):
                    continue
                    
                # Use facebook_id as unique identifier
                facebook_id = post.get("facebook_id")
                if not facebook_id or facebook_id in seen_facebook_ids:
                    continue
                    
                seen_facebook_ids.add(facebook_id)
                
                # Create a clean post object
                clean_post = {
                    "facebook_id": facebook_id,
                    "title": post.get("title", "Untitled"),
                    "likes": post.get("likes", 0),
                    "comments": post.get("comments", 0),
                    "followers": post.get("followers", 0),
                    "categories": post.get("categories", []),
                    "address": post.get("address", ""),
                    "phone_number": post.get("phone_number", ""),
                    "page_url": post.get("page_url", ""),
                    "id": row.get("id"),
                    "source": "facebook",
                    "date": row.get("date")
                }
                all_posts.append(clean_post)
    
    logger.info(f"Facebook: Found {len(all_posts)} unique posts, selecting top 5 by likes")
    
    # Get the top 5 posts with most likes
    top_posts = sorted(all_posts, key=lambda x: x.get("likes", 0), reverse=True)[:5]
    return {"facebook": top_posts}


def process_reddit_posts_last_7_days(rows):
    """
    Given a list of Reddit rows (from Supabase), flatten all posts from the latest 7 rows and return 5 random posts in the format {"reddit": [ ... ]}. No duplicates allowed.
    """
    all_posts = []
    seen_reddit_ids = set()
    
    logger.info(f"Processing {len(rows)} Reddit rows")
    
    for row in rows:
        posts = row.get("data", [])
        if isinstance(posts, list):
            for post in posts:
                if not isinstance(post, dict):
                    continue
                    
                # Use url as unique identifier for Reddit
                url = post.get("url")
                if not url or url in seen_reddit_ids:
                    continue
                    
                seen_reddit_ids.add(url)
                
                # Create a clean post object
                clean_post = {
                    "url": url,
                    "title": post.get("title", "Untitled"),
                    "body": post.get("body", ""),
                    "user": post.get("user", "Unknown"),
                    "subreddit": post.get("subreddit", "Unknown"),
                    "id": row.get("id"),
                    "source": "reddit",
                    "date": row.get("date")
                }
                all_posts.append(clean_post)
    
    logger.info(f"Reddit: Found {len(all_posts)} unique posts, selecting 5 random")
    
    # Pick 5 random posts (or all if less than 5)
    if len(all_posts) <= 5:
        random_posts = all_posts
    else:
        random_posts = random.sample(all_posts, 5)
    
    return {"reddit": random_posts}


def process_linkedin_posts_last_7_days(rows):
    """
    Given a list of LinkedIn rows (from Supabase), flatten all posts from the latest 7 rows and return the top 5 posts with the most total_reactions in the format {"linkedin": [ ... ]}. No duplicates allowed.
    """
    all_posts = []
    seen_activity_ids = set()
    
    logger.info(f"Processing {len(rows)} LinkedIn rows")
    
    for row in rows:
        posts = row.get("data", [])
        if isinstance(posts, list):
            for post in posts:
                if not isinstance(post, dict):
                    continue
                    
                # Use activity_id as unique identifier
                activity_id = post.get("activity_id")
                if not activity_id or activity_id in seen_activity_ids:
                    continue
                    
                seen_activity_ids.add(activity_id)
                
                # Create a clean post object
                clean_post = {
                    "activity_id": activity_id,
                    "text": post.get("text", ""),
                    "author_name": post.get("author_name", "Unknown"),
                    "posted_date": post.get("posted_date", ""),
                    "total_reactions": post.get("total_reactions", 0),
                    "comments": post.get("comments", 0),
                    "shares": post.get("shares", 0),
                    "hashtags": post.get("hashtags", []),
                    "post_url": post.get("post_url", ""),
                    "author_profile_url": post.get("author_profile_url", ""),
                    "id": row.get("id"),
                    "source": "linkedin",
                    "date": row.get("date")
                }
                all_posts.append(clean_post)
    
    logger.info(f"LinkedIn: Found {len(all_posts)} unique posts, selecting top 5 by total_reactions")
    
    # Get the top 5 posts with most total_reactions
    top_posts = sorted(all_posts, key=lambda x: x.get("total_reactions", 0), reverse=True)[:5]
    return {"linkedin": top_posts}


def process_instagram_posts_last_7_days(rows):
    """
    Given a list of Instagram rows (from Supabase), where each row's data is a dict with 'top_posts' key (array of posts), flatten all posts and return the top 5 by likes_count. No duplicates allowed.
    """
    all_posts = []
    seen_post_urls = set()
    
    logger.info(f"Processing {len(rows)} Instagram rows")
    
    for row in rows:
        data = row.get("data", {})
        if isinstance(data, dict):
            top_posts = data.get("top_posts", [])
            if isinstance(top_posts, list):
                for post in top_posts:
                    if not isinstance(post, dict):
                        continue
                        
                    # Use post_url as unique identifier
                    post_url = post.get("post_url")
                    if not post_url or post_url in seen_post_urls:
                        continue
                        
                    seen_post_urls.add(post_url)
                    
                    # Create a clean post object
                    clean_post = {
                        "post_url": post_url,
                        "username": post.get("username", "Unknown"),
                        "full_name": post.get("full_name", "Unknown"),
                        "caption": post.get("caption", ""),
                        "timestamp": post.get("timestamp", ""),
                        "likes_count": post.get("likes_count", 0),
                        "comments_count": post.get("comments_count", 0),
                        "type": post.get("type", "Unknown"),
                        "hashtags": post.get("hashtags", []),
                        "mentions": post.get("mentions", []),
                        "is_sponsored": post.get("is_sponsored", False),
                        "id": row.get("id"),
                        "source": "instagram",
                        "date": row.get("date")
                    }
                    all_posts.append(clean_post)
    
    logger.info(f"Instagram: Found {len(all_posts)} unique posts, selecting top 5 by likes_count")
    
    # Get the top 5 posts with most likes_count
    top_posts = sorted(all_posts, key=lambda x: x.get("likes_count", 0), reverse=True)[:5]
    return {"instagram": top_posts}


def process_twitter_posts_last_7_days(rows):
    """
    Given a list of Twitter rows (from Supabase), where each row's data is a list of tweet objects, flatten all tweets and return the top 5 by view_count. No duplicates allowed.
    """
    all_posts = []
    seen_tweet_ids = set()
    
    logger.info(f"Processing {len(rows)} Twitter rows")
    
    for row in rows:
        tweets = row.get("data", [])
        if isinstance(tweets, list):
            for tweet in tweets:
                if not isinstance(tweet, dict):
                    continue
                    
                # Use tweet_id as unique identifier
                tweet_id = tweet.get("tweet_id")
                if not tweet_id or tweet_id in seen_tweet_ids:
                    continue
                    
                seen_tweet_ids.add(tweet_id)
                
                # Create a clean post object
                clean_post = {
                    "tweet_id": tweet_id,
                    "text": tweet.get("text", ""),
                    "user_name": tweet.get("user_name", "Unknown"),
                    "location": tweet.get("location", ""),
                    "followers": tweet.get("followers", 0),
                    "following": tweet.get("following", 0),
                    "created_at": tweet.get("created_at", ""),
                    "like_count": tweet.get("like_count", 0),
                    "retweet_count": tweet.get("retweet_count", 0),
                    "reply_count": tweet.get("reply_count", 0),
                    "view_count": tweet.get("view_count", 0),
                    "lang": tweet.get("lang", ""),
                    "is_blue_verified": tweet.get("is_blue_verified", False),
                    "url": tweet.get("url", ""),
                    "twitter_profile_url": tweet.get("twitter_profile_url", ""),
                    "id": row.get("id"),
                    "source": "twitter",
                    "date": row.get("date")
                }
                all_posts.append(clean_post)
    
    logger.info(f"Twitter: Found {len(all_posts)} unique posts, selecting top 5 by view_count")
    
    # Get the top 5 posts with most view_count
    top_posts = sorted(all_posts, key=lambda x: x.get("view_count", 0), reverse=True)[:5]
    return {"twitter": top_posts}
