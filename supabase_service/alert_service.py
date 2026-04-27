import asyncio
from datetime import datetime, timedelta
import traceback
from fastapi import HTTPException
from core.settings import supabase
from loguru import logger
from llm_services.alert import generate_alerts_llm
from utils.search_url import search_article_url

logger.add("app.log", level="INFO") 
class AlertConsolidationError(Exception):
    """Custom exception for alert consolidation errors"""
    pass

async def consolidate_and_store_alert_data():
    """
    Fetch last 3 alert_details records, consolidate using LLM, find sources using summary_en, 
    and store in alerts table. Remove any alerts that do not have a source URL.
    """
    try:
        logger.info("Starting simplified alert data consolidation...")

        # Fetch last 3 alert_details records
        try:
            logger.info("Fetching last 3 alert details...")
            detail_response = supabase.table("alert_details") \
                .select("news_data, created_at") \
                .order("created_at", desc=True) \
                .limit(3) \
                .execute()
            
            if not detail_response.data:
                logger.info("No data found in alert_details table")
                return {"status": "success", "message": "No data to process"}
            
            detail_data = detail_response.data
            logger.info(f"Retrieved {len(detail_data)} alert detail records")

        except Exception as e:
            raise AlertConsolidationError(f"Failed to fetch alert details: {str(e)}")

        # Flatten all news_data from the last 3 records
        all_alerts = []
        for record in detail_data:
            news_data = record.get("news_data", [])
            if isinstance(news_data, list):
                for alert in news_data:
                    if isinstance(alert, dict) and alert.get("summary_en"):
                        all_alerts.append(alert)
            else:
                logger.warning(f"Invalid news_data format in record: {record}")

        logger.info(f"Found {len(all_alerts)} total alerts from last 3 records")

        if not all_alerts:
            logger.info("No alert data found. Exiting consolidation.")
            return {"status": "success", "message": "No alerts to process"}

        # Call LLM to consolidate and deduplicate all alerts
        try:
            logger.info("Calling LLM for alert consolidation...")
            consolidated_alerts = await generate_alerts_llm(all_alerts)
            
            if not isinstance(consolidated_alerts, list):
                raise AlertConsolidationError("LLM returned invalid format (expected list)")

            logger.info(f"LLM consolidated to {len(consolidated_alerts)} unique alerts")

        except Exception as e:
            raise AlertConsolidationError(f"LLM consolidation failed: {str(e)}")

        if not consolidated_alerts:
            logger.info("No alerts after consolidation. Skipping DB insert.")
            return {"status": "success", "message": "No unique alerts to store"}

        # Process alerts to get source URLs with rate limiting
        logger.info("Processing alerts to get source URLs...")
        processed_alerts = []

        for i, alert in enumerate(consolidated_alerts):
            try:
                if alert.get("summary_en"):
                    if i > 0:
                        await asyncio.sleep(1)  # 1 second delay between requests

                    logger.info(f"Searching URL for alert {i+1}/{len(consolidated_alerts)}: {alert['summary_en']}...")
                    article_url = await search_article_url(alert["summary_en"])
                    if article_url:
                        alert["source"] = article_url
                        logger.info(f"✓ Found source URL for alert {i+1}: {article_url}")
                    else:
                        logger.warning(f"✗ No URL found for alert {i+1}: {alert['summary_en']}")
                        alert["source"] = ""  # Adding empty source for missing URLs

                # Only append alerts that have a valid source
                if alert.get("source"):
                    processed_alerts.append(alert)
                else:
                    logger.warning(f"Alert {i+1} skipped due to missing source URL.")

            except Exception as e:
                logger.error(f"Error processing alert {i+1}: {str(e)}")
                alert["source"] = ""
                processed_alerts.append(alert)

        # Final validation before storing
        if not processed_alerts:
            logger.info("No alerts to store after processing.")
            return {"status": "success", "message": "No alerts to store"}

        # Insert consolidated alerts into the alerts table
        try:
            logger.info("Storing consolidated alerts in database...")
            payload = {
                "date": str(datetime.now().date()),
                "news_data": processed_alerts
            }

            response = supabase.table("alerts").insert(payload).execute()
            
            if not response.data:
                raise AlertConsolidationError("Database insert returned no data")

            logger.info(f"Successfully stored {len(processed_alerts)} consolidated alerts")
            
            # Log each stored alert
            for alert in processed_alerts:
                logger.info(f"Stored: {alert['summary_en']}...")

            return {
                "status": "success",
                "message": f"Stored {len(processed_alerts)} consolidated unique alerts",
                "data": response.data
            }

        except Exception as e:
            raise AlertConsolidationError(f"Failed to store alerts in database: {str(e)}")

    except AlertConsolidationError as e:
        logger.error(f"Alert consolidation error: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Alert consolidation failed: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error in consolidate_and_store_alert_data: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


def get_latest_alert():
    """
    Retrieve the most recent entry from the 'alerts' table.
    """
    try:
        response = supabase.table("alerts").select("*").order("created_at", desc=True).limit(1).execute()
        if not response.data:
            logger.warning(" No alert found in 'alerts' table.")
            return None

        return response.data[0]

    except Exception as e:
        logger.error(f" Error fetching latest alert: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching latest alert.")


def get_alert_by_id(alert_id: str):
    """
    Retrieve a single alert by its id from the 'alerts' table.
    """
    try:
        response = supabase.table("alerts").select("*").eq("id", alert_id).limit(1).execute()
        if not response.data:
            logger.warning(f"No alert found with id: {alert_id}")
            return None
        return response.data[0]
    except Exception as e:
        logger.error(f"Error fetching alert by id {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching alert by id.")


def get_alerts_id_date_list():
    """
    Retrieve all alerts' ids and dates as a list of dicts/arrays, ordered by created_at desc.
    """
    try:
        response = supabase.table("alerts").select("id, date").order("date", desc=True).execute()
        if not response.data:
            logger.warning("No alerts found in 'alerts' table for id-date list.")
            return []
        # Return as list of dicts with id and date
        return [{"id": row["id"], "date": row["date"]} for row in response.data]
    except Exception as e:
        logger.error(f"Error fetching alerts id-date list: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching alerts id-date list.")
