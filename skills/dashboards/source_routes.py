"""
source_routes.py — Source preferences + agentic URL analyzer endpoints.
"""
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from loguru import logger

from core.dependencies import get_current_user
from supabase_service.source_service import (
    get_user_source_prefs,
    upsert_source_pref,
    create_source,
    get_source_by_url,
    seed_prefs_for_user,
    get_followed_source_ids,
    get_sources_for_category,
)

router = APIRouter(prefix="/sources", tags=["Sources"])


# ── Pydantic models ───────────────────────────────────────────────────────────

class SubmitSourceRequest(BaseModel):
    url: str
    name: str
    category_id: str
    scrape_type: str
    rss_url: Optional[str] = None
    css_selector: Optional[str] = None
    language: str = "en"


class SourcePrefUpdate(BaseModel):
    source_id: str
    is_followed: bool


# ── Source prefs ──────────────────────────────────────────────────────────────

@router.get("/prefs")
def get_my_source_prefs(current_user=Depends(get_current_user)):
    return get_user_source_prefs(current_user["id"])


@router.put("/prefs")
def update_source_pref(body: SourcePrefUpdate, current_user=Depends(get_current_user)):
    return upsert_source_pref(current_user["id"], body.source_id, body.is_followed)


@router.get("/followed-ids")
def get_followed_ids(current_user=Depends(get_current_user)):
    return {"source_ids": get_followed_source_ids(current_user["id"])}


@router.get("/by-category/{category_id}")
def list_sources_for_category(category_id: str, current_user=Depends(get_current_user)):
    return get_sources_for_category(category_id)


# ── Submit confirmed source ───────────────────────────────────────────────────

@router.post("/submit")
def submit_source(body: SubmitSourceRequest, current_user=Depends(get_current_user)):
    existing = get_source_by_url(body.url)
    if existing:
        upsert_source_pref(current_user["id"], existing["id"], True)
        return {
            "source_id": existing["id"],
            "created": False,
            "message": "Source already exists — added to your followed sources.",
        }

    source_row = {
        "url": body.url,
        "name": body.name,
        "category_id": body.category_id,
        "scrape_type": body.scrape_type,
        "rss_url": body.rss_url,
        "css_selector": body.css_selector,
        "language": body.language,
        "active": True,
        "submitted_by": current_user["id"],
        "is_required": False,
    }
    source = create_source(source_row)
    upsert_source_pref(current_user["id"], source["id"], True)
    return {
        "source_id": source["id"],
        "created": True,
        "message": "Source added and followed.",
    }


# ── SSE: Agentic analysis stream ──────────────────────────────────────────────

@router.get("/analyze")
async def analyze_source_stream(
    url: str,
    category_slug: str = "news",
    current_user=Depends(get_current_user),
):
    """
    GET /sources/analyze?url=...&category_slug=...
    Streams Server-Sent Events while the agent tries 5 scraping strategies.
    Use @microsoft/fetch-event-source on the frontend (supports Authorization header).
    """
    from scrapers.agent_scraper import analyze_url

    async def event_stream():
        try:
            async for status in analyze_url(url, category_slug, current_user["id"]):
                yield f"data: {json.dumps(status)}\n\n"
        except Exception as e:
            logger.error(f"[SSE] analyze_url error: {e}")
            error_event = {"step": 0, "strategy": "complete", "status": "failed",
                           "items_found": 0, "config": None, "message": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
