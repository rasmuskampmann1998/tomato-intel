from fastapi import APIRouter, HTTPException
from supabase_service.weekly_service import get_latest_weekly_data
from supabase_service.weekly_service import get_weekly_report_by_id
from core.settings import supabase
from loguru import logger
from fastapi.responses import FileResponse
import tempfile
import os
import threading
from pdf_generator.weekly_pdf import generate_weekly_report_pdf

router = APIRouter(prefix="/weekly", tags=["Weekly Reports"])

@router.get("/report")
async def get_weekly_report():
    """
    Returns the latest weekly report including news and technical data (JSON).
    """
    try:
        latest_data = get_latest_weekly_data()

        if not latest_data:
            raise HTTPException(status_code=404, detail="No weekly data available")

        response = {
            "id": latest_data.get("id"),
            "date": latest_data.get("date"),
            "created_at": latest_data.get("created_at"),
            "data": {
                "news_data": latest_data.get("news_data", []),
                "technical_data": latest_data.get("technical_data", {
                    "patents": [],
                    "regulations": [],
                    "genetic_resources": []
                }),
                "social_media_data": latest_data.get("social_media_data", {}),
                "breeding_recommendation": latest_data.get("breeding_recommendation", [])
            }
        }
        return response

    except Exception as e:
        logger.error(f"Failed to fetch weekly report: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/ids")
async def get_all_weekly_report_ids():
    """
    Returns a list of all weekly report ids and their dates, sorted by date descending.
    """
    try:
        result = supabase.table("weekly_data_reports").select("id, date").order("date", desc=True).execute()
        reports = result.data if result.data else []
        return [{"id": r["id"], "date": r["date"]} for r in reports]
    except Exception as e:
        logger.error(f"Failed to fetch weekly report ids: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    

@router.get("/pdf")
async def get_weekly_report_pdf(report_id: str):
    """
    Generate a PDF for a weekly report by its id and return it as a downloadable file.
    The PDF file is deleted from the temp directory after a short delay.
    """
    try:
        report = get_weekly_report_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        # Use system temp directory
        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, f"weekly_report.pdf")
        generate_weekly_report_pdf(report, pdf_path)
        def delayed_delete(path):
            import time
            time.sleep(30)  # Wait 30 seconds before deleting
            try:
                os.remove(path)
            except Exception:
                pass
        threading.Thread(target=delayed_delete, args=(pdf_path,), daemon=True).start()
        return FileResponse(pdf_path, filename=f"weekly_report.pdf", media_type="application/pdf")
    except Exception as e:
        logger.error(f"Failed to generate/send weekly report PDF: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

