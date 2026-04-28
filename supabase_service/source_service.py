from fastapi import HTTPException
from core.settings import supabase
from loguru import logger


# ── Source CRUD ───────────────────────────────────────────────────────────────

def get_sources_for_category(category_id: str) -> list[dict]:
    resp = supabase.table("sources").select("*").eq("category_id", category_id).order("name").execute()
    return resp.data or []


def get_source_by_url(url: str) -> dict | None:
    resp = supabase.table("sources").select("*").eq("url", url).execute()
    return resp.data[0] if resp.data else None


def create_source(payload: dict) -> dict:
    try:
        resp = supabase.table("sources").insert(payload).execute()
        if not resp.data:
            raise HTTPException(status_code=500, detail="Source insert returned no data")
        return resp.data[0]
    except Exception as e:
        logger.error(f"create_source error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── User source prefs ─────────────────────────────────────────────────────────

def get_user_source_prefs(user_id: str) -> list[dict]:
    resp = (
        supabase.table("user_source_prefs")
        .select("source_id, is_followed, updated_at")
        .eq("user_id", user_id)
        .execute()
    )
    return resp.data or []


def get_followed_source_ids(user_id: str) -> list[str]:
    resp = (
        supabase.table("user_source_prefs")
        .select("source_id")
        .eq("user_id", user_id)
        .eq("is_followed", True)
        .execute()
    )
    return [r["source_id"] for r in (resp.data or [])]


def upsert_source_pref(user_id: str, source_id: str, is_followed: bool) -> dict:
    resp = supabase.table("user_source_prefs").upsert(
        {
            "user_id": user_id,
            "source_id": source_id,
            "is_followed": is_followed,
            "updated_at": "now()",
        },
        on_conflict="user_id,source_id",
    ).execute()
    return resp.data[0] if resp.data else {}


def seed_prefs_for_user(user_id: str, experience: str) -> None:
    try:
        supabase.rpc(
            "seed_source_prefs_for_user",
            {"p_user_id": user_id, "p_experience": experience},
        ).execute()
        logger.info(f"Source prefs seeded for user {user_id} (experience: {experience})")
    except Exception as e:
        logger.warning(f"seed_prefs_for_user failed for {user_id}: {e}")
