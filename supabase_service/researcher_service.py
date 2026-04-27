#supabase_service/researcher_service.py

#Import Libraries
from core.security import hash_password
from core.settings import supabase
from schemas.researcher_schema import ResearcherUpdate
from fastapi import HTTPException
from loguru import logger

# Set up logger
logger.add("app.log", level="INFO") 

def get_researcher_by_id(user_id: str):
    """
    Fetch the researcher profile by user ID.
    This function retrieves the user's data from the 'users' table based on the provided user ID.

    Parameters:
    - user_id: The ID of the researcher to retrieve.

    Returns:
    - The researcher profile data if found.
    
    Raises:
    - HTTPException: If the user is not found.
    """
    logger.info(f"Fetching researcher profile for user ID: {user_id}")
    resp = supabase.table("users").select("*").eq("id", user_id).single().execute()
    if not resp.data:
        logger.warning(f"Researcher not found with user ID: {user_id}")
        raise HTTPException(status_code=404, detail="Researcher not found")
    
    logger.info(f"Researcher profile found for user ID: {user_id}")
    return resp.data

def update_researcher(user_id: str, data: ResearcherUpdate):
    """
    Update the researcher's profile data.
    This function updates the researcher's details such as full name, email, and password.

    Parameters:
    - user_id: The ID of the researcher to update.
    - data: The new data to update the researcher profile with.

    Returns:
    - A success message if the profile is updated successfully.

    Raises:
    - HTTPException: If the user is not found or the update fails.
    """
    logger.info(f"Updating researcher profile for user ID: {user_id}")

    # Fetch existing user data
    existing = supabase.table("users").select("*").eq("id", user_id).single().execute()
    if not existing.data:
        logger.warning(f"User not found for update with user ID: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")

    current_data = existing.data
    update_data = data.dict(exclude_unset=True)

    # Prepare update payload
    payload = {
        "full_name": update_data.get("full_name", current_data.get("full_name")),
        "email": update_data.get("email", current_data.get("email")),
        "password_hash": hash_password(update_data["password"]) if "password" in update_data else current_data.get("password_hash")
    }

    # Perform update
    resp = supabase.table("users").update(payload).eq("id", user_id).execute()
    if not resp.data:
        logger.error(f"Failed to update researcher profile for user ID: {user_id}")
        raise HTTPException(status_code=500, detail="Update failed")

    logger.info(f"Researcher profile updated successfully for user ID: {user_id}")
    return {"message": "Profile updated successfully"}

def delete_researcher(user_id: str):
    """
    Delete the researcher's profile by user ID.
    This function deletes the user from the 'users' table and their associated role from the 'user_roles' table.

    Parameters:
    - user_id: The ID of the researcher to delete.

    Returns:
    - A success message if the researcher is deleted successfully.

    Raises:
    - HTTPException: If the user is not found or already deleted.
    """
    logger.info(f"Deleting researcher with user ID: {user_id}")

    resp = supabase.table("users").delete().eq("id", user_id).execute()
    
    # Supabase returns an empty list in `data` if nothing was deleted
    if not resp.data:
        logger.warning(f"Researcher not found or already deleted with user ID: {user_id}")
        raise HTTPException(status_code=404, detail="User not found or already deleted")
    
    logger.info(f"Researcher deleted successfully with user ID: {user_id}")
    return {"message": "Researcher deleted successfully"}
