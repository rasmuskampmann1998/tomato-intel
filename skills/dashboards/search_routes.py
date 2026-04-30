"""
search_routes.py — AI-powered keyword suggestion for search profiles.
"""
import json
import os
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI

router = APIRouter(prefix="/search", tags=["Search"])

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


class SuggestRequest(BaseModel):
    terms: List[str]
    brief: str = ""
    category_slug: str = ""


@router.post("/suggest-keywords")
async def suggest_keywords(body: SuggestRequest):
    if not body.terms:
        return {"suggestions": []}

    prompt = (
        f"Agriculture market intelligence platform. Category: {body.category_slug or 'general'}.\n"
        f"Current search terms: {', '.join(body.terms)}\n"
        f"Intelligence brief: {body.brief or 'not provided'}\n\n"
        "Suggest 10 additional search keywords that improve coverage of this topic.\n"
        "Include: scientific names, synonyms, related diseases or traits, key companies, "
        "regional or regulatory terms, and common abbreviations.\n"
        "Return ONLY a JSON array of strings. Example: [\"term1\", \"term2\", \"term3\"]"
    )

    try:
        resp = _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        raw = resp.choices[0].message.content.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        suggestions = json.loads(raw)
        if isinstance(suggestions, dict):
            # Handle {"keywords": [...]} style response
            suggestions = next(iter(suggestions.values()), [])
        return {"suggestions": [str(s).strip() for s in suggestions[:12] if s]}
    except Exception:
        return {"suggestions": []}
