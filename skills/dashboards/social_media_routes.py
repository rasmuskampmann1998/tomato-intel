from typing import Optional
from fastapi import APIRouter, Query
from supabase import create_client
from core.settings import supabase
from loguru import logger

from supabase_service.social_media_service import fetch_latest_facebook_posts, fetch_latest_instagram_posts, fetch_latest_linkedin_posts, fetch_latest_reddit_posts, fetch_latest_twitter_posts

router = APIRouter(prefix="/social", tags=["Social Media"])

logger.add("app.log", level="INFO") 


@router.get("/reddit/fetch")
async def fetch_reddit_posts(
    page: int = Query(1),
    offset: int = Query(10),
    subreddit: Optional[str] = None,
    title: Optional[str] = None,
    user: Optional[str] = None,
):
    """
    Fetch paginated and filtered Reddit post data.
    Supports filtering by `subreddit`, `title`, `user`.
    """
    try:
        response = await fetch_latest_reddit_posts()
        latest_record = response[0] if response else None

        if not latest_record:
            return []

        full_data = latest_record.get("data", [])

        # Apply filters
        filtered_data = [
            post for post in full_data
            if (not subreddit or subreddit.lower() in post.get("subreddit", "").lower())
            and (not title or title.lower() in post.get("title", "").lower())
            and (not user or user.lower() in post.get("user", "").lower())
        ]

        # Pagination
        if page < 1: page = 1
        if offset < 1: offset = 10
        start = (page - 1) * offset
        end = start + offset
        paginated_data = filtered_data[start:end]

        result = {
            "id": latest_record["id"],
            "source": latest_record["source"],
            "date": latest_record["date"],
            "data": paginated_data,
            "count": len(full_data),
            "success": True
        }

        return result

    except Exception as e:
        logger.error(f"Failed to fetch Reddit posts: {e}")
        return []


@router.get("/facebook/fetch")
async def fetch_facebook_pages(
page: int = Query(1, description="Page number for pagination"), 
offset: int = Query(10, description="Number of items per page"), 
title: Optional[str] = Query(None, description="Filter by page title"), 
category: Optional[str] = Query(None, description="Filter by category"), 
min_followers: Optional[int] = Query(None, description="Minimum number of followers")
):
    """
    Fetch paginated and filtered Facebook page data.
    Supports filtering by `title`, `category`, `min_followers`.
    """
    try:
        response = await fetch_latest_facebook_posts()
        latest_record = response[0] if response else None

        if not latest_record:
            return []

        full_data = latest_record.get("data", [])

        # Apply filters
        filtered_data = []
        for page_item in full_data:  # Renamed to avoid confusion with 'page' parameter
            # Title filter
            if title and title.lower() not in page_item.get("title", "").lower():
                continue
            
            # Category filter
            if category:
                page_categories = page_item.get("categories", [])
                if not any(category.lower() in cat.lower() for cat in page_categories):
                    continue
            
            # Minimum followers filter
            if min_followers is not None:  # Check for None explicitly
                try:
                    followers = page_item.get("followers", 0)
                    
                    # Convert followers to integer, handling various data types
                    if isinstance(followers, dict):
                        # If it's a dict, try to extract a numeric value or default to 0
                        followers = followers.get("count", 0) if "count" in followers else 0
                    elif isinstance(followers, str):
                        # Try to parse string to int
                        followers = int(followers.replace(",", "")) if followers.replace(",", "").isdigit() else 0
                    elif not isinstance(followers, (int, float)):
                        followers = 0
                    
                    # Ensure it's an integer for comparison
                    followers = int(followers) if isinstance(followers, (int, float)) else 0
                    
                    if followers < min_followers:
                        continue
                        
                except (TypeError, ValueError, AttributeError) as e:
                    # Log the specific error and skip this item
                    logger.warning(f"Error processing followers data for page: {e}")
                    continue
            
            filtered_data.append(page_item)

        # Pagination
        if page < 1: 
            page = 1
        if offset < 1: 
            offset = 10
            
        start = (page - 1) * offset
        end = start + offset
        paginated_data = filtered_data[start:end]

        result = {
            "id": latest_record["id"],
            "source": latest_record["source"],
            "date": latest_record["date"],
            "data": paginated_data,
            "count": len(full_data),
            "success": True
        }

        return result

    except Exception as e:
        logger.error(f"Failed to fetch Facebook pages: {e}")
        return {"error": str(e), "success": False}  # Return more informative error


@router.get("/linkedin/fetch")
async def fetch_linkedin_posts(
    page: int = Query(1, description="Page number for pagination"), 
    offset: int = Query(10, description="Number of items per page"), 
    author_name: Optional[str] = Query(None, description="Filter by author name"), 
    hashtag: Optional[str] = Query(None, description="Filter by hashtag"), 
    min_reactions: Optional[int] = Query(None, description="Minimum number of reactions")
):
    """
    Fetch paginated and filtered LinkedIn post data.
    Supports filtering by `author_name`, `hashtag`, `min_reactions`.
    """
    try:
        response = await fetch_latest_linkedin_posts()
        latest_record = response[0] if response else None

        if not latest_record:
            return []

        full_data = latest_record.get("data", [])

        # Apply filters
        filtered_data = []
        for post_item in full_data:
            # Author name filter
            if author_name and author_name.lower() not in post_item.get("author_name", "").lower():
                continue
            
            # Hashtag filter
            if hashtag:
                post_hashtags = post_item.get("hashtags", [])
                if not any(hashtag.lower() in tag.lower() for tag in post_hashtags):
                    continue
            
            # Minimum reactions filter
            if min_reactions is not None:
                try:
                    reactions = post_item.get("total_reactions", 0)
                    
                    # Convert reactions to integer, handling various data types
                    if isinstance(reactions, str):
                        reactions = int(reactions.replace(",", "")) if reactions.replace(",", "").isdigit() else 0
                    elif not isinstance(reactions, (int, float)):
                        reactions = 0
                    
                    # Ensure it's an integer for comparison
                    reactions = int(reactions) if isinstance(reactions, (int, float)) else 0
                    
                    if reactions < min_reactions:
                        continue
                        
                except (TypeError, ValueError, AttributeError) as e:
                    logger.warning(f"Error processing reactions data for post: {e}")
                    continue
            
            filtered_data.append(post_item)

        # Pagination
        if page < 1: 
            page = 1
        if offset < 1: 
            offset = 10
            
        start = (page - 1) * offset
        end = start + offset
        paginated_data = filtered_data[start:end]

        result = {
            "id": latest_record["id"],
            "source": latest_record["source"],
            "date": latest_record["date"],
            "data": paginated_data,
            "count": len(full_data),
            "success": True
        }

        return result

    except Exception as e:
        logger.error(f"Failed to fetch LinkedIn posts: {e}")
        return {"error": str(e), "success": False}
    


@router.get("/twitter/fetch")
async def fetch_twitter_posts(
    page: int = Query(1, description="Page number for pagination"), 
    offset: int = Query(10, description="Number of items per page"), 
    user_name: Optional[str] = Query(None, description="Filter by username"), 
    lang: Optional[str] = Query(None, description="Filter by language"), 
    min_views: Optional[int] = Query(None, description="Minimum number of views"),
    min_followers: Optional[int] = Query(None, description="Minimum number of followers"),
    is_verified: Optional[bool] = Query(None, description="Filter by verified users only")
):
    """
    Fetch paginated and filtered Twitter post data.
    Supports filtering by `user_name`, `lang`, `min_views`, `min_followers`, `is_verified`.
    """
    try:
        response = await fetch_latest_twitter_posts()
        latest_record = response[0] if response else None

        if not latest_record:
            return []

        full_data = latest_record.get("data", [])

        # Apply filters
        filtered_data = []
        for tweet_item in full_data:
            # Username filter
            if user_name and user_name.lower() not in tweet_item.get("user_name", "").lower():
                continue
            
            # Language filter
            if lang and lang.lower() != tweet_item.get("lang", "").lower():
                continue
            
            # Minimum views filter
            if min_views is not None:
                try:
                    views = tweet_item.get("view_count", 0)
                    
                    # Convert views to integer, handling various data types
                    if isinstance(views, str):
                        views = int(views.replace(",", "")) if views.replace(",", "").isdigit() else 0
                    elif not isinstance(views, (int, float)):
                        views = 0
                    
                    views = int(views) if isinstance(views, (int, float)) else 0
                    
                    if views < min_views:
                        continue
                        
                except (TypeError, ValueError, AttributeError) as e:
                    logger.warning(f"Error processing views data for tweet: {e}")
                    continue
            
            # Minimum followers filter
            if min_followers is not None:
                try:
                    followers = tweet_item.get("followers", 0)
                    
                    # Convert followers to integer, handling various data types
                    if isinstance(followers, str):
                        followers = int(followers.replace(",", "")) if followers.replace(",", "").isdigit() else 0
                    elif not isinstance(followers, (int, float)):
                        followers = 0
                    
                    followers = int(followers) if isinstance(followers, (int, float)) else 0
                    
                    if followers < min_followers:
                        continue
                        
                except (TypeError, ValueError, AttributeError) as e:
                    logger.warning(f"Error processing followers data for tweet: {e}")
                    continue
            
            # Verified users filter
            if is_verified is not None:
                if tweet_item.get("is_blue_verified", False) != is_verified:
                    continue
            
            filtered_data.append(tweet_item)

        # Pagination
        if page < 1: 
            page = 1
        if offset < 1: 
            offset = 10
            
        start = (page - 1) * offset
        end = start + offset
        paginated_data = filtered_data[start:end]

        result = {
            "id": latest_record["id"],
            "source": latest_record["source"],
            "date": latest_record["date"],
            "data": paginated_data,
            "count": len(full_data),
            "filtered_count": len(filtered_data),
            "success": True
        }

        return result

    except Exception as e:
        logger.error(f"Failed to fetch Twitter posts: {e}")
        return {"error": str(e), "success": False}
    
@router.get("/instagram/fetch")
async def fetch_instagram_posts(
    page: int = Query(1, description="Page number for pagination"),
    offset: int = Query(10, description="Number of items per page"),
    min_likes: Optional[int] = Query(None, description="Minimum number of likes"),
    min_comments: Optional[int] = Query(None, description="Minimum number of comments"),
    username: Optional[str] = Query(None, description="Filter by username"),
    has_hashtags: Optional[bool] = Query(None, description="Filter posts that have hashtags"),
    is_sponsored: Optional[bool] = Query(None, description="Filter by sponsored posts")
):
    """
    Fetch paginated and filtered Instagram post data.
    Supports filtering by `min_likes`, `min_comments`, `username`, `has_hashtags`, `is_sponsored`.
    """
    try:
        response = await fetch_latest_instagram_posts()
        latest_record = response[0] if response else None

        if not latest_record:
            return []

        full_data = latest_record.get("data", {})
        
        # Combine all posts from both top and latest
        top_posts = full_data.get("top_posts", [])
        latest_posts = full_data.get("latest_posts", [])
        
        # Add source indicator to differentiate origin
        for post in top_posts:
            post["source_type"] = "top"
        for post in latest_posts:
            post["source_type"] = "latest"
            
        all_posts = top_posts + latest_posts

        # Apply filters
        filtered_data = []
        for post in all_posts:
            # Username filter
            if username and username.lower() not in post.get("username", "").lower():
                continue
            
            # Minimum likes filter
            if min_likes is not None:
                try:
                    likes = post.get("likes_count", 0)
                    if isinstance(likes, str):
                        likes = int(likes.replace(",", "")) if likes.replace(",", "").isdigit() else 0
                    elif not isinstance(likes, (int, float)):
                        likes = 0
                    
                    likes = int(likes) if isinstance(likes, (int, float)) else 0
                    
                    if likes < min_likes:
                        continue
                        
                except (TypeError, ValueError, AttributeError) as e:
                    logger.warning(f"Error processing likes data for Instagram post: {e}")
                    continue
            
            # Minimum comments filter
            if min_comments is not None:
                try:
                    comments = post.get("comments_count", 0)
                    if isinstance(comments, str):
                        comments = int(comments.replace(",", "")) if comments.replace(",", "").isdigit() else 0
                    elif not isinstance(comments, (int, float)):
                        comments = 0
                    
                    comments = int(comments) if isinstance(comments, (int, float)) else 0
                    
                    if comments < min_comments:
                        continue
                        
                except (TypeError, ValueError, AttributeError) as e:
                    logger.warning(f"Error processing comments data for Instagram post: {e}")
                    continue
            
            # Has hashtags filter
            if has_hashtags is not None:
                hashtags = post.get("hashtags", [])
                has_tags = bool(hashtags and len(hashtags) > 0)
                if has_tags != has_hashtags:
                    continue
            
            # Sponsored posts filter
            if is_sponsored is not None:
                if post.get("is_sponsored", False) != is_sponsored:
                    continue
            
            filtered_data.append(post)

        # Pagination
        if page < 1: 
            page = 1
        if offset < 1: 
            offset = 10
            
        start = (page - 1) * offset
        end = start + offset
        paginated_data = filtered_data[start:end]

        result = {
            "id": latest_record["id"],
            "source": latest_record["source"],
            "date": latest_record["date"],
            "hashtag_info": {
                "hashtag_name": full_data.get("hashtag_name", ""),
                "posts_count": full_data.get("posts_count", 0),
                "posts_per_day": full_data.get("posts_per_day", 0)
            },
            "data": paginated_data,
            "total_top_posts": len(full_data.get("top_posts", [])),
            "total_latest_posts": len(full_data.get("latest_posts", [])),
            "filtered_count": len(filtered_data),
            "success": True
        }

        return result

    except Exception as e:
        logger.error(f"Failed to fetch Instagram posts: {e}")
        return {"error": str(e), "success": False}