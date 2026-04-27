# services/editor_service.py

#Import libraries
from fastapi import HTTPException
from core.settings import supabase
from core.security import hash_password 
from schemas.editor_schema import EditorCreate, EditorUpdate
from uuid import UUID
from datetime import datetime
from loguru import logger
# Set up logger
logger.add("app.log", level="INFO") 

def is_valid_uuid(uuid_string):
    """Check if a string is a valid UUID"""
    try:
        UUID(uuid_string)
        return True
    except (ValueError, TypeError):
        return False
    
def create_editor(data: EditorCreate):
    """Create a new editor user"""
    # Check if role 'editor' exists
    logger.info(f"Checking if 'editor' role exists in roles table")
    role_resp = supabase.table("roles").select("id").eq("name", "editor").single().execute()
    if not role_resp.data:
        logger.error("Role 'editor' not found")
        raise HTTPException(status_code=400, detail="Role 'editor' not found")

    # Create user in the 'users' table
    logger.info(f"Creating new editor with email: {data.email}")
    user_resp = supabase.table("users").insert({
        "email": data.email,
        "full_name": data.full_name,
        "password": hash_password(data.password),
        "created_at": str(datetime.utcnow())
    }).execute()

    if not user_resp.data:
        logger.error(f"Failed to create editor with email: {data.email}")
        raise HTTPException(status_code=500, detail="Failed to create editor")

    user_id = user_resp.data[0]["id"]

    # Assign the 'editor' role
    logger.info(f"Assigning 'editor' role to user ID: {user_id}")
    supabase.table("user_roles").insert({
        "user_id": user_id,
        "role_id": role_resp.data["id"]
    }).execute()

    logger.info(f"Editor '{data.full_name}' created successfully with email: {data.email}")
    return {
        "id": user_id,
        "email": data.email,
        "full_name": data.full_name,
        "created_at": user_resp.data[0]["created_at"],
        "role": "editor"
    }

def get_editor_profile(user_id: str):
    """Fetch profile for an editor by ID"""
    if not is_valid_uuid(user_id):
        logger.warning(f"Invalid user ID format: {user_id}")
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    logger.info(f"Fetching profile for editor ID: {user_id}")
    user_resp = supabase.table("users").select("*").eq("id", user_id).single().execute()
    if not user_resp.data:
        logger.warning(f"Editor not found with ID: {user_id}")
        raise HTTPException(status_code=404, detail="Editor not found")

    # Validate role
    user_roles = supabase.table("user_roles").select("role_id").eq("user_id", user_id).single().execute()
    role_id = user_roles.data["role_id"]

    role_resp = supabase.table("roles").select("name").eq("id", role_id).single().execute()
    role_name = role_resp.data["name"]

    if role_name != "editor":
        logger.warning(f"User ID {user_id} does not have the 'editor' role")
        raise HTTPException(status_code=403, detail="User is not an editor")

    logger.info(f"Editor profile found: {user_resp.data['email']}")
    return {**user_resp.data, "role": "editor"}

def update_editor_profile(user_id: str, updates: EditorUpdate):
    """Update editor profile"""
    if not is_valid_uuid(user_id):
        logger.warning(f"Invalid user ID format: {user_id}")
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    update_payload = {}
    if updates.email:
        update_payload["email"] = updates.email
    if updates.full_name:
        update_payload["full_name"] = updates.full_name
    if updates.password:
        update_payload["password_hash"] = hash_password(updates.password)

    if not update_payload:
        logger.warning("No fields provided for update")
        raise HTTPException(status_code=400, detail="No fields provided for update")

    logger.info(f"Updating editor profile for user ID: {user_id}")
    supabase.table("users").update(update_payload).eq("id", user_id).execute()

    user = supabase.table("users").select("*").eq("id", user_id).single().execute().data
    logger.info(f"Editor profile updated for user ID: {user_id}")
    return {**user, "role": "editor"}

def delete_editor(user_id: str):
    """Delete an editor by ID"""
    if not is_valid_uuid(user_id):
        logger.warning(f"Invalid user ID format: {user_id}")
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    # Confirm role is editor
    logger.info(f"Confirming role for user ID: {user_id}")
    role_check = get_editor_profile(user_id)

    logger.info(f"Deleting editor profile for user ID: {user_id}")
    supabase.table("users").delete().eq("id", user_id).execute()
    supabase.table("user_roles").delete().eq("user_id", user_id).execute()

    logger.info(f"Editor '{role_check['full_name']}' deleted successfully")
    return {"message": f"Editor '{role_check['full_name']}' deleted successfully"}

def list_researchers(role_name: str):
    """List all users with a specific role"""
    try:
        # Step 1: Fetch the role_id using the role name from the 'roles' table
        logger.info(f"Fetching role ID for role: {role_name}")
        role_resp = supabase.table("roles").select("id").eq("name", role_name.lower()).single().execute()
        if not role_resp.data:
            logger.error(f"Role '{role_name}' not found")
            raise HTTPException(status_code=404, detail=f"Role '{role_name}' not found")

        role_id = role_resp.data["id"]

        # Step 2: Fetch user_ids mapped to the role_id from the 'user_roles' table
        logger.info(f"Fetching user IDs for role ID: {role_id}")
        user_roles_resp = supabase.table("user_roles").select("user_id").eq("role_id", role_id).execute()
        if not user_roles_resp.data:
            logger.info(f"No users found for role: {role_name}")
            return []  # No users found for this role

        user_ids = [entry["user_id"] for entry in user_roles_resp.data]

        # Step 3: Fetch only the 'full_name' of users for the given user_ids from the 'users' table
        logger.info(f"Fetching user names for user IDs: {user_ids}")
        users_resp = supabase.table("users").select("full_name").in_("id", user_ids).execute()
        if not users_resp.data:
            logger.info(f"No users found for the given user_ids: {user_ids}")
            return []  # No users found for the given user_ids

        # Step 4: Return only the 'full_name' of the users
        logger.info(f"Found {len(users_resp.data)} users for role '{role_name}'")
        return [user["full_name"] for user in users_resp.data]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in list_researchers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
