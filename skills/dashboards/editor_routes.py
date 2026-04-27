# routes/editor_routes.py

#Import Libraries
from fastapi import APIRouter, Depends, HTTPException
from core.dependencies import require_editor
from schemas.editor_schema import EditorOut, EditorUpdate
from supabase_service.editor_service import (
    get_editor_profile,
    list_researchers,
    update_editor_profile,
    delete_editor,
)
from loguru import logger

# Set up logger
logger.add("app.log", level="INFO") 

router = APIRouter(prefix="/editor", tags=["Editor"])

# 1. Editor Profile Routes
@router.get("/me", response_model=EditorOut)
def get_my_profile(current_user=Depends(require_editor)):
    """
    Fetch the profile of the currently logged-in editor.
    """
    logger.info(f"Fetching profile for editor ID: {current_user['id']}")
    return get_editor_profile(current_user["id"])

@router.put("/me/update", response_model=EditorOut)
def update_my_profile(updates: EditorUpdate, current_user=Depends(require_editor)):
    """
    Update the profile of the currently logged-in editor.
    """
    logger.info(f"Updating profile for editor ID: {current_user['id']}")
    return update_editor_profile(current_user["id"], updates)

@router.delete("/me/delete")
def delete_my_profile(current_user=Depends(require_editor)):
    """
    Delete the profile of the currently logged-in editor.
    """
    logger.info(f"Deleting profile for editor ID: {current_user['id']}")
    return delete_editor(current_user["id"])


# 2. View Researcher List
@router.get("/researcher/list")
def list_all_researchers(current_user=Depends(require_editor)):
    """
    Get a list of all researchers.
    """
    logger.info("Fetching list of all researchers")
    return list_researchers("researcher")
