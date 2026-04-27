import json
from datetime import datetime
from core.settings import supabase
from llm_services.monthly_data_generator import generate_monthly_news_summary, generate_monthly_technical_data_summary, generate_monthly_breeding_recommendations
from loguru import logger
import random

WEEKLY_TABLE = "weekly_data_reports"
MONTHLY_TABLE = "monthly_data_reports"

async def fetch_last_4_weekly_reports():
    result = supabase.table(WEEKLY_TABLE) \
        .select("*") \
        .order("date", desc=True) \
        .limit(4) \
        .execute()
    return result.data if result.data else []

async def aggregate_news_data(weekly_reports):
    """
    Aggregate news data from last 4 weekly reports.
    """
    logger.info(f"Aggregating news data from {len(weekly_reports)} weekly reports")
    all_news = []
    for report in weekly_reports:
        news = report.get("news_data", [])
        if isinstance(news, list):
            all_news.extend(news)
    
    logger.info(f"Collected {len(all_news)} total news items for monthly aggregation")
    return all_news

async def aggregate_technical_data(weekly_reports):
    """
    Aggregate technical data from last 4 weekly reports.
    """
    logger.info(f"Aggregating technical data from {len(weekly_reports)} weekly reports")
    patents, regulations, genetic_resources = [], [], []
    for report in weekly_reports:
        tech = report.get("technical_data", {})
        patents.extend(tech.get("patents", []))
        regulations.extend(tech.get("regulations", []))
        genetic_resources.extend(tech.get("genetic_resources", []))
    
    logger.info(f"Collected technical data: {len(patents)} patents, {len(regulations)} regulations, {len(genetic_resources)} genetic resources")
    return {
        "patents": patents,
        "regulations": regulations,
        "genetic_resources": genetic_resources
    }

def aggregate_social_media_data(weekly_reports):
    """
    Aggregate social media data from last 4 weekly reports with proper deduplication.
    Each platform uses its unique identifier to prevent duplicates.
    """
    logger.info("Starting monthly social media data aggregation...")
    
    # Gather all posts for each platform from last 4 weekly reports
    platforms = ["reddit", "facebook", "instagram", "twitter", "linkedin"]
    all_posts = {platform: [] for platform in platforms}
    
    for report in weekly_reports:
        sm = report.get("social_media_data", {})
        if isinstance(sm, dict):
            for platform in platforms:
                posts = sm.get(platform, [])
                if isinstance(posts, list):
                    all_posts[platform].extend(posts)
    
    logger.info(f"Collected posts: Reddit={len(all_posts['reddit'])}, Facebook={len(all_posts['facebook'])}, Instagram={len(all_posts['instagram'])}, Twitter={len(all_posts['twitter'])}, LinkedIn={len(all_posts['linkedin'])}")
    
    # Deduplicate and select top posts for each platform
    result = {}
    
    # Reddit: random 6 unique posts
    reddit_posts = all_posts["reddit"]
    seen_reddit_urls = set()
    unique_reddit = []
    for post in reddit_posts:
        url = post.get("url")
        if url and url not in seen_reddit_urls:
            seen_reddit_urls.add(url)
            unique_reddit.append(post)
    
    if len(unique_reddit) > 6:
        reddit_selected = random.sample(unique_reddit, 6)
    else:
        reddit_selected = unique_reddit
    result["reddit"] = reddit_selected
    logger.info(f"Reddit: {len(unique_reddit)} unique posts, selected {len(reddit_selected)} random")
    
    # Facebook: top 5 by likes (unique by facebook_id)
    facebook_posts = all_posts["facebook"]
    seen_facebook_ids = set()
    unique_facebook = []
    for post in facebook_posts:
        facebook_id = post.get("facebook_id")
        if facebook_id and facebook_id not in seen_facebook_ids:
            seen_facebook_ids.add(facebook_id)
            unique_facebook.append(post)
    
    facebook_selected = sorted(unique_facebook, key=lambda x: x.get("likes", 0), reverse=True)[:5]
    result["facebook"] = facebook_selected
    logger.info(f"Facebook: {len(unique_facebook)} unique posts, selected top {len(facebook_selected)} by likes")
    
    # Instagram: top 5 by likes_count (unique by post_url)
    instagram_posts = all_posts["instagram"]
    seen_instagram_urls = set()
    unique_instagram = []
    for post in instagram_posts:
        post_url = post.get("post_url")
        if post_url and post_url not in seen_instagram_urls:
            seen_instagram_urls.add(post_url)
            unique_instagram.append(post)
    
    instagram_selected = sorted(unique_instagram, key=lambda x: x.get("likes_count", 0), reverse=True)[:5]
    result["instagram"] = instagram_selected
    logger.info(f"Instagram: {len(unique_instagram)} unique posts, selected top {len(instagram_selected)} by likes_count")
    
    # Twitter: top 5 by view_count (unique by tweet_id)
    twitter_posts = all_posts["twitter"]
    seen_twitter_ids = set()
    unique_twitter = []
    for post in twitter_posts:
        tweet_id = post.get("tweet_id")
        if tweet_id and tweet_id not in seen_twitter_ids:
            seen_twitter_ids.add(tweet_id)
            unique_twitter.append(post)
    
    twitter_selected = sorted(unique_twitter, key=lambda x: x.get("view_count", 0), reverse=True)[:5]
    result["twitter"] = twitter_selected
    logger.info(f"Twitter: {len(unique_twitter)} unique posts, selected top {len(twitter_selected)} by view_count")
    
    # LinkedIn: top 5 by total_reactions (unique by activity_id)
    linkedin_posts = all_posts["linkedin"]
    seen_linkedin_ids = set()
    unique_linkedin = []
    for post in linkedin_posts:
        activity_id = post.get("activity_id")
        if activity_id and activity_id not in seen_linkedin_ids:
            seen_linkedin_ids.add(activity_id)
            unique_linkedin.append(post)
    
    linkedin_selected = sorted(unique_linkedin, key=lambda x: x.get("total_reactions", 0), reverse=True)[:5]
    result["linkedin"] = linkedin_selected
    logger.info(f"LinkedIn: {len(unique_linkedin)} unique posts, selected top {len(linkedin_selected)} by total_reactions")
    
    total_selected = sum([len(result[platform]) for platform in platforms])
    logger.info(f"Monthly social media aggregation complete. Total posts selected: {total_selected}")
    
    return result

async def generate_and_store_monthly_data():
    """
    1. Fetch last 4 weekly reports.
    2. Aggregate news, technical, and social media data.
    3. Generate monthly news summary (top 5) using LLM.
    4. Generate deduplicated technical data summary using monthly LLM function.
    5. Store in monthly_data_reports (with social_media_data).
    """
    try:
        logger.info("Starting monthly data generation process...")
        
        weekly_reports = await fetch_last_4_weekly_reports()
        if not weekly_reports:
            logger.warning("No weekly reports found for monthly aggregation.")
            return False

        logger.info(f"Fetched {len(weekly_reports)} weekly reports for monthly aggregation")

        # Aggregate news data
        all_news = await aggregate_news_data(weekly_reports)
        monthly_news_summary = await generate_monthly_news_summary(all_news)
        if isinstance(monthly_news_summary, list):
            monthly_news_summary = monthly_news_summary[:5]
        
        logger.info(f"Generated monthly news summary with {len(monthly_news_summary)} items")

        # Aggregate technical data (raw)
        technical_data_raw = await aggregate_technical_data(weekly_reports)
        technical_data = await generate_monthly_technical_data_summary(
            technical_data_raw["patents"],
            technical_data_raw["regulations"],
            technical_data_raw["genetic_resources"]
        )
        
        logger.info(f"Generated monthly technical data summary")

        # Aggregate social media data
        social_media_data = aggregate_social_media_data(weekly_reports)
        
        logger.info(f"Generated monthly social media data summary")

        # Generate breeding recommendations using all data
        breeding_recommendations = await generate_monthly_breeding_recommendations(monthly_news_summary, technical_data, social_media_data)
        
        logger.info(f"Generated {len(breeding_recommendations)} breeding recommendations")

        insert_resp = supabase.table(MONTHLY_TABLE).insert({
            "date": datetime.utcnow().date().isoformat(),
            "news_data": monthly_news_summary,
            "technical_data": technical_data,
            "social_media_data": social_media_data,
            "breeding_recommendation": breeding_recommendations
        }).execute()

        logger.success("Monthly data report (news + technical + social_media + breeding recommendation) successfully saved to Supabase.")
        return True
    except Exception as e:
        logger.error(f"Failed to generate/store monthly data report: {e}")
        return False

def get_latest_monthly_data():
    """
    Fetch the latest entry from monthly_data_reports.
    """
    try:
        result = supabase.table(MONTHLY_TABLE).select("*").order("created_at", desc=True).limit(1).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error fetching latest monthly data: {e}")
        return None

def get_monthly_report_by_id(report_id: str):
    """
    Fetch a monthly report by its id and return all columns as a dict, or None if not found.
    """
    try:
        result = supabase.table(MONTHLY_TABLE).select("*").eq("id", report_id).limit(1).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error fetching monthly report by id: {e}")
        return None 