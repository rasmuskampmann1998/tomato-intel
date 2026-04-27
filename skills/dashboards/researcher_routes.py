#routes\researcher_routes.py

#Import Libraries
from fastapi import APIRouter, Depends
from schemas.researcher_schema import ResearcherOut, ResearcherUpdate
from supabase_service.researcher_service import (
    get_researcher_by_id,
    update_researcher,
    delete_researcher,
)
from core.dependencies import require_researcher
from loguru import logger


logger.add("app.log", level="INFO") 
router = APIRouter(prefix="/researcher", tags=["Researcher"])

# 1. Fetch Researcher Profile
@router.get("/me", response_model=ResearcherOut)
def get_my_profile(current_user=Depends(require_researcher)):
    """
    Fetch the profile of the currently logged-in researcher.
    """
    logger.info(f"Fetching profile for researcher ID: {current_user['id']}")
    user_data = get_researcher_by_id(current_user["id"])
    user_data["role"] = current_user["role"]  # Add the role to the user data
    return user_data

# 2. Update Researcher Profile
@router.put("/me/update")
def update_my_profile(
    updates: ResearcherUpdate,
    current_user=Depends(require_researcher)
):
    """
    Update the profile of the currently logged-in researcher.
    """
    logger.info(f"Updating profile for researcher ID: {current_user['id']}")
    update_researcher(current_user["id"], updates)
    return {"message": "Profile updated successfully"}

# 3. Delete Researcher Profile
@router.delete("/me/delete")
def delete_my_profile(current_user=Depends(require_researcher)):
    """
    Delete the profile of the currently logged-in researcher.
    """
    logger.info(f"Deleting profile for researcher ID: {current_user['id']}")
    return delete_researcher(current_user["id"])
