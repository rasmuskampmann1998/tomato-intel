# supabase_service/weekly_service.py

import json
from datetime import datetime, timedelta
from core.settings import supabase
from llm_services.weekly_data_generator import generate_news_summary, generate_technical_data_summary, generate_breeding_recommendations
from utils.social_media_processor import process_facebook_posts_last_7_days, process_reddit_posts_last_7_days, process_linkedin_posts_last_7_days, process_instagram_posts_last_7_days, process_twitter_posts_last_7_days
from loguru import logger

ALERTS_TABLE = "alerts"
PATENTS_TABLE = "patents"
REGULATIONS_TABLE = "regulations"
GENETIC_RESOURCES_TABLE = "genetics"
SOCIAL_MEDIA_TABLE = "social_media"
WEEKLY_TABLE = "weekly_data_reports"

# Modular social media fetch/processing
async def fetch_facebook_posts_last_7_days():
    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    result = supabase.table(SOCIAL_MEDIA_TABLE) \
        .select("*") \
        .eq("source", "facebook") \
        .gte("date", seven_days_ago) \
        .order("date", desc=True) \
        .limit(20) \
        .execute()
    return result.data if result.data else []

async def fetch_reddit_posts_last_7_days():
    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    result = supabase.table(SOCIAL_MEDIA_TABLE) \
        .select("*") \
        .eq("source", "reddit") \
        .gte("date", seven_days_ago) \
        .order("date", desc=True) \
        .limit(20) \
        .execute()
    return result.data if result.data else []

async def fetch_linkedin_posts_last_7_days():
    # Fetch the latest 7 LinkedIn rows by created_at (assumes daily ingestion)
    result = supabase.table(SOCIAL_MEDIA_TABLE) \
        .select("*") \
        .eq("source", "linkedin") \
        .order("date", desc=True) \
        .limit(7) \
        .execute()
    return result.data if result.data else []

async def fetch_instagram_posts_last_7_days():
    result = supabase.table(SOCIAL_MEDIA_TABLE) \
        .select("*") \
        .eq("source", "instagram") \
        .order("date", desc=True) \
        .limit(7) \
        .execute()
    return result.data if result.data else []

async def fetch_twitter_posts_last_7_days():
    result = supabase.table(SOCIAL_MEDIA_TABLE) \
        .select("*") \
        .eq("source", "twitter") \
        .order("date", desc=True) \
        .limit(7) \
        .execute()
    return result.data if result.data else []


async def get_social_media_summary():
    # Modular: add other sources here later
    logger.info("Starting social media data processing...")
    
    instagram_rows = await fetch_instagram_posts_last_7_days()
    logger.info(f"Fetched {len(instagram_rows)} Instagram rows from database")
    instagram_summary = process_instagram_posts_last_7_days(instagram_rows)
    logger.info(f"Instagram processing complete: {len(instagram_summary.get('instagram', []))} posts selected")
    
    reddit_rows = await fetch_reddit_posts_last_7_days()
    logger.info(f"Fetched {len(reddit_rows)} Reddit rows from database")
    reddit_summary = process_reddit_posts_last_7_days(reddit_rows)
    logger.info(f"Reddit processing complete: {len(reddit_summary.get('reddit', []))} posts selected")
    
    facebook_rows = await fetch_facebook_posts_last_7_days()
    logger.info(f"Fetched {len(facebook_rows)} Facebook rows from database")
    facebook_summary = process_facebook_posts_last_7_days(facebook_rows)
    logger.info(f"Facebook processing complete: {len(facebook_summary.get('facebook', []))} posts selected")
    
    linkedin_rows = await fetch_linkedin_posts_last_7_days()
    logger.info(f"Fetched {len(linkedin_rows)} LinkedIn rows from database")
    linkedin_summary = process_linkedin_posts_last_7_days(linkedin_rows)
    logger.info(f"LinkedIn processing complete: {len(linkedin_summary.get('linkedin', []))} posts selected")
    
    twitter_rows = await fetch_twitter_posts_last_7_days()
    logger.info(f"Fetched {len(twitter_rows)} Twitter rows from database")
    twitter_summary = process_twitter_posts_last_7_days(twitter_rows)
    logger.info(f"Twitter processing complete: {len(twitter_summary.get('twitter', []))} posts selected")
    
    # Merge all dicts into one, in the order: instagram, reddit, facebook, linkedin, twitter
    social_media_data = {}
    social_media_data.update(instagram_summary)
    social_media_data.update(reddit_summary)
    social_media_data.update(facebook_summary)
    social_media_data.update(linkedin_summary)
    social_media_data.update(twitter_summary)
    
    total_posts = sum([
        len(social_media_data.get('instagram', [])),
        len(social_media_data.get('reddit', [])),
        len(social_media_data.get('facebook', [])),
        len(social_media_data.get('linkedin', [])),
        len(social_media_data.get('twitter', []))
    ])
    
    logger.info(f"Social media processing complete. Total posts selected: {total_posts}")
    logger.info(f"Breakdown: Instagram={len(social_media_data.get('instagram', []))}, Reddit={len(social_media_data.get('reddit', []))}, Facebook={len(social_media_data.get('facebook', []))}, LinkedIn={len(social_media_data.get('linkedin', []))}, Twitter={len(social_media_data.get('twitter', []))}")
    
    return social_media_data


async def generate_and_store_weekly_data():
    """
    1. Fetch last 2 alerts from Supabase.
    2. Fetch latest 3 patents, 3 regulations, and 3 genetic resources.
    3. Fetch and process social media data (modular, Facebook only for now).
    4. Send news and technical data to LLM for summary.
    5. Store all data in weekly_data_reports.
    """
    try:
        # Step 1: Fetch alerts data
        alerts_result = supabase.table(ALERTS_TABLE).select("*").order("created_at", desc=True).limit(2).execute()
        last_two_alerts = alerts_result.data if alerts_result.data else []

        if not last_two_alerts:
            logger.warning("No recent alerts found in Supabase.")
            news_summary = []
        else:
            logger.info(f"Fetched {len(last_two_alerts)} latest alerts.")
            news_summary = await generate_news_summary(last_two_alerts)

        # Step 2: Fetch technical data
        patents_result = supabase.table(PATENTS_TABLE).select("*").order("publication_date", desc=True).limit(3).execute()
        latest_patents = patents_result.data if patents_result.data else []

        regulations_result = supabase.table(REGULATIONS_TABLE).select("*").order("year", desc=True).limit(3).execute()
        latest_regulations = regulations_result.data if regulations_result.data else []

        genetics_result = supabase.table(GENETIC_RESOURCES_TABLE).select("*").order("collection_date", desc=True).limit(3).execute()
        latest_genetics = genetics_result.data if genetics_result.data else []

        logger.info(f"Fetched {len(latest_patents)} patents, {len(latest_regulations)} regulations, {len(latest_genetics)} genetic resources.")

        # Step 3: Generate technical data summary
        technical_summary = await generate_technical_data_summary(latest_patents, latest_regulations, latest_genetics)

        # Step 4: Fetch and process social media data (modular)
        social_media_summary = await get_social_media_summary()
        logger.info(f"Processed social media summary: {social_media_summary}")

        # Step 5: Generate breeding recommendations using all data
        breeding_recommendations = await generate_breeding_recommendations(news_summary, technical_summary, social_media_summary)

        # Step 6: Store combined data in weekly_data_reports
        insert_resp = supabase.table(WEEKLY_TABLE).insert({
            "date": datetime.utcnow().date().isoformat(),
            "news_data": news_summary,
            "technical_data": technical_summary,
            "social_media_data": social_media_summary,
            "breeding_recommendation": breeding_recommendations
        }).execute()

        logger.success("Weekly data report (news + technical + social media + breeding recommendation) successfully saved to Supabase.")
        return True

    except Exception as e:
        logger.error(f"Failed to generate/store weekly data report: {e}")
        return False


async def fetch_last_4_weekly_reports():
    result = supabase.table(WEEKLY_TABLE) \
        .select("*") \
        .order("date", desc=True) \
        .limit(4) \
        .execute()
    return result.data if result.data else []

async def get_monthly_news_data():
    """
    Fetch last 4 weekly reports, combine all news_data, and return the combined list.
    """
    weekly_reports = await fetch_last_4_weekly_reports()
    all_news = []
    for report in weekly_reports:
        news = report.get("news_data", [])
        if isinstance(news, list):
            all_news.extend(news)
    return all_news


def get_latest_weekly_data():
    """
    Fetch the latest entry from weekly_data_reports.
    """
    try:
        result = supabase.table(WEEKLY_TABLE).select("*").order("created_at", desc=True).limit(1).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error fetching latest weekly data: {e}")
        return None

def get_weekly_report_by_id(report_id: str):
    """
    Fetch a weekly report by its id and return all columns as a dict, or None if not found.
    """
    try:
        result = supabase.table(WEEKLY_TABLE).select("*").eq("id", report_id).limit(1).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error fetching weekly report by id: {e}")
        return None