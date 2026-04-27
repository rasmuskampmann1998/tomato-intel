import re
from datetime import datetime
from supabase_service.genetic_service import insert_genetic_record_safe

def extract_country(origin):
    if not origin:
        return ""
    origin = re.sub(r"^(Donated|Collected|Developed)\s*[\u2013-]\s*", "", origin)
    if "–" in origin:
        origin = origin.split("–")[-1].strip()
    if "," in origin:
        origin = origin.split(",")[-1].strip()
    return origin.strip()

def parse_collection_date(date_str):
    # Try to parse various formats and always return YYYY-MM-DD
    if not date_str:
        return None
    for fmt in ("%d %b %Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%Y.%m.%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except Exception:
            continue
    # If all fail, return as is (or None)
    return None

def clean_and_insert_genetics(data):
    for record in data:
        print("[DEBUG] Original record:", record)  # Print before any processing
        if "id" in record:
            del record["id"]
        record["country_of_origin"] = extract_country(record.get("country_of_origin", ""))
        # Robust date parsing
        record["collection_date"] = parse_collection_date(record.get("collection_date", ""))
        if "id" in record:
            print("[ERROR] 'id' field still present before insert!", record)
        else:
            print("Inserting record (no id):", record)  # Debug log
        insert_genetic_record_safe(record) 