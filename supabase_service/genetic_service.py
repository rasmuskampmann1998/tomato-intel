from core.settings import supabase
from loguru import logger
from datetime import datetime
import re

logger.add("app.log", level="INFO") 

GENETICS_TABLE = "genetics"

def get_filtered_genetics(
    page: int,
    limit: int,
    variety_name: str = None,
    country_of_origin: str = None,
    genus: str = None,
    crop_name: str = None,
    collection_start_date: str = None,
    collection_end_date: str = None,
):
    offset = (page - 1) * limit
    logger.info(f"Fetching genetics with page={page}, limit={limit}, offset={offset}")

    query = supabase.table(GENETICS_TABLE).select("*").range(offset, offset + limit - 1).order('collection_date', desc=True)

    if variety_name:
        query = query.ilike("variety_name", f"%{variety_name.strip()}%")
    if country_of_origin:
        query = query.ilike("country_of_origin", f"%{country_of_origin.strip()}%")
    if genus:
        query = query.ilike("genus", f"%{genus.strip()}%")
    if crop_name:
        query = query.ilike("crop_name", f"%{crop_name.strip()}%")

    if collection_start_date and collection_end_date:
        query = query.gte("collection_date", collection_start_date).lte("collection_date", collection_end_date)
    elif collection_start_date:
        query = query.gte("collection_date", collection_start_date)
    elif collection_end_date:
        query = query.lte("collection_date", collection_end_date)

    response = query.execute()
    rows = response.data or []

    logger.info(f"Returned {len(rows)} filtered results.")
    return rows

def get_genetic_count():
    logger.info("Fetching total genetic count from the database")
    try:
        response = (
            supabase.table(GENETICS_TABLE)
            .select("id", count="exact")
            .execute()
        )
        return response.count or 0
    except Exception as e:
        logger.error(f"Error fetching genetic count: {e}")
        return 0

def format_date(date_str):
    """
    Format date string to YYYY-MM-DD format
    Handles various date formats including ISO dates
    """
    if not date_str:
        return None
    
    try:
        # If it's already in the correct format, return as is
        if re.match(r'^\d{4}-\d{2}-\d{2}$', str(date_str)):
            return str(date_str)
        
        # Try to parse various date formats
        date_formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%d-%m-%Y',
            '%m-%d-%Y'
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(str(date_str), fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # If no format matches, log warning and return original
        logger.warning(f"Could not parse date format: {date_str}")
        return str(date_str)
        
    except Exception as e:
        logger.error(f"Error formatting date {date_str}: {e}")
        return None

def clean_record(record):
    """
    Clean the record by removing id and formatting dates
    """
    if not isinstance(record, dict):
        logger.error(f"Record is not a dictionary: {record}")
        return None
    
    # Create a copy to avoid modifying the original
    clean_record = record.copy()
    
    # Remove id if present
    if "id" in clean_record:
        removed_id = clean_record.pop("id")
        logger.info(f"Removed ID {removed_id} from record before insertion")
    
    # Format collection_date if present
    if "collection_date" in clean_record and clean_record["collection_date"]:
        original_date = clean_record["collection_date"]
        clean_record["collection_date"] = format_date(original_date)
        if clean_record["collection_date"] != original_date:
            logger.info(f"Formatted date from {original_date} to {clean_record['collection_date']}")
    
    # Clean up empty strings and None values for optional fields
    for key, value in clean_record.items():
        if value == "" or value is None:
            if key in ["variety_name", "country_of_origin"]:
                clean_record[key] = None
            elif key == "country_of_origin" and (value == "" or value is None):
                clean_record[key] = "Unknown"
    
    return clean_record

def insert_genetic_record(record):
    """
    Insert a genetic record after cleaning it
    """
    logger.info(f"Inserting record: {record}")
    
    # Clean the record
    cleaned_record = clean_record(record)
    
    if cleaned_record is None:
        logger.error("Failed to clean record, skipping insertion")
        return None
    
    try:
        response = supabase.table(GENETICS_TABLE).insert(cleaned_record).execute()
        logger.info(f"Successfully inserted record into genetics: {cleaned_record}")
        return response
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error inserting record into genetics: {error_msg} | Record: {cleaned_record}")
        
        # Check if it's a duplicate key error
        if "duplicate key value violates unique constraint" in error_msg:
            logger.warning(f"Duplicate record detected, skipping: {cleaned_record}")
            return "DUPLICATE"
        
        return None

def insert_genetic_records_batch(records):
    """
    Insert multiple genetic records in batch
    """
    if not records:
        logger.warning("No records to insert")
        return {"success": 0, "duplicates": 0, "errors": 0}
    
    success_count = 0
    duplicate_count = 0
    error_count = 0
    
    logger.info(f"Starting batch insertion of {len(records)} records")
    
    for record in records:
        result = insert_genetic_record(record)
        
        if result == "DUPLICATE":
            duplicate_count += 1
        elif result is not None:
            success_count += 1
        else:
            error_count += 1
    
    logger.info(f"Batch insertion completed. Success: {success_count}, Duplicates: {duplicate_count}, Errors: {error_count}")
    
    return {
        "success": success_count,
        "duplicates": duplicate_count,
        "errors": error_count,
        "total": len(records)
    }

def check_existing_record(record):
    """
    Check if a record already exists based on key fields
    """
    try:
        query = supabase.table(GENETICS_TABLE).select("id")
        # Build query based on available fields
        if record.get("variety_name"):
            query = query.eq("variety_name", record["variety_name"])
        if record.get("country_of_origin"):
            query = query.eq("country_of_origin", record["country_of_origin"])
        if record.get("genus"):
            query = query.eq("genus", record["genus"])
        if record.get("crop_name"):
            query = query.eq("crop_name", record["crop_name"])
        if record.get("collection_date"):
            query = query.eq("collection_date", format_date(record["collection_date"]))
        response = query.execute()
        if len(response.data) > 0:
            logger.info(f"Record already exists in genetics table: {record}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error checking existing record: {e}")
        return False

def insert_genetic_record_safe(record):
    """
    Insert a genetic record with duplicate checking
    """
    cleaned_record = clean_record(record)
    
    if cleaned_record is None:
        logger.error("Failed to clean record, skipping insertion")
        return None
    
    # Check if record already exists
    if check_existing_record(cleaned_record):
        logger.info(f"Record already exists, skipping: {cleaned_record}")
        return "DUPLICATE"
    
    return insert_genetic_record(cleaned_record)