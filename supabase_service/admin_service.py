# supabase_service/admin_service.py

#Import libraries
from core.settings import supabase
from core.security import hash_password
from uuid import uuid4, UUID
from fastapi import HTTPException
from schemas.admin_schema import AdminCreate, AdminUpdate
import re
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

def get_user_with_role_by_id(user_id: str):
    """Get user with role information by user ID"""
    # Validate UUID format first
    if not is_valid_uuid(user_id):
        logger.warning(f"Invalid UUID format for user_id: {user_id}")
        raise HTTPException(status_code=400, detail=f"Invalid user ID format: {user_id}")
    
    try:
        user_id_str = str(user_id)
        
        # Step 1: Fetch user
        logger.info(f"Fetching user data for user ID: {user_id_str}")
        user_resp = supabase.table("users").select("*").eq("id", user_id_str).single().execute()
        if not user_resp.data:
            logger.warning(f"User not found with ID: {user_id_str}")
            raise HTTPException(status_code=404, detail="User not found")
        user = user_resp.data

        # Step 2: Fetch role_id from user_roles
        logger.info(f"Fetching role information for user ID: {user_id_str}")
        user_roles_resp = supabase.table("user_roles").select("role_id").eq("user_id", user_id_str).single().execute()
        if not user_roles_resp.data:
            logger.warning(f"Role mapping not found for user ID: {user_id_str}")
            raise HTTPException(status_code=404, detail="Role mapping not found")
        role_id = user_roles_resp.data["role_id"]

        # Step 3: Fetch role name from roles table
        role_resp = supabase.table("roles").select("name").eq("id", role_id).single().execute()
        if not role_resp.data:
            logger.warning(f"Role not found for role_id: {role_id}")
            raise HTTPException(status_code=404, detail="Role not found")
        role_name = role_resp.data["name"]

        # Final response
        logger.info(f"User found: {user['email']} with role: {role_name}")
        return {**user, "role": role_name}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in get_user_with_role_by_id: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def get_admin_profile(user_id: str):
    """Get admin profile by user ID"""
    logger.info(f"Fetching admin profile for user ID: {user_id}")
    return get_user_with_role_by_id(user_id)

def update_admin_profile(user_id: str, update_data: AdminUpdate):
    """Update admin profile"""
    if not is_valid_uuid(user_id):
        logger.warning(f"Invalid UUID format for user_id: {user_id}")
        raise HTTPException(status_code=400, detail=f"Invalid user ID format: {user_id}")
    
    try:
        logger.info(f"Fetching current profile for admin ID: {user_id}")
        current = supabase.table("users").select("*").eq("id", user_id).single().execute().data
        if not current:
            logger.warning(f"Admin not found with ID: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
            
        updates = update_data.dict(exclude_unset=True)

        payload = {
            "full_name": updates.get("full_name", current["full_name"]),
            "email": updates.get("email", current["email"]),
            "password_hash": hash_password(updates["password"]) if "password" in updates else current["password_hash"]
        }

        logger.info(f"Updating admin profile for user ID: {user_id}")
        supabase.table("users").update(payload).eq("id", user_id).execute()
        return get_user_with_role_by_id(user_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in update_admin_profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def delete_admin(user_id: str):
    """Delete admin by user ID"""
    if not is_valid_uuid(user_id):
        logger.warning(f"Invalid UUID format for user_id: {user_id}")
        raise HTTPException(status_code=400, detail=f"Invalid user ID format: {user_id}")
    
    try:
        logger.info(f"Deleting admin profile for user ID: {user_id}")
        supabase.table("user_roles").delete().eq("user_id", user_id).execute()
        supabase.table("users").delete().eq("id", user_id).execute()
        return {"message": "Admin deleted successfully"}
        
    except Exception as e:
        logger.error(f"Database error in delete_admin: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def create_user(user_data: AdminCreate):
    """Create a new user with specified role"""
    try:
        logger.info(f"Checking if user already exists with email: {user_data.email}")
        existing = supabase.table("users").select("id").eq("email", user_data.email).execute().data
        if existing:
            logger.warning(f"User already exists with email: {user_data.email}")
            raise HTTPException(status_code=400, detail="User already exists")

        user_id = str(uuid4())
        logger.info(f"Creating new user with email: {user_data.email}")
        supabase.table("users").insert({
            "id": user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "password_hash": hash_password(user_data.password),
        }).execute()

        # Get role ID
        role_resp = supabase.table("roles").select("id").eq("name", user_data.role.lower()).single().execute()
        if not role_resp.data:
            logger.warning(f"Invalid role: {user_data.role}")
            raise HTTPException(status_code=400, detail="Invalid role")

        supabase.table("user_roles").insert({
            "user_id": user_id,
            "role_id": role_resp.data["id"]
        }).execute()

        logger.info(f"User created successfully with ID: {user_id}")
        return get_user_with_role_by_id(user_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in create_user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def update_user_by_id(user_id: str, updates: AdminUpdate):
    """Update user by ID"""
    if not is_valid_uuid(user_id):
        logger.warning(f"Invalid UUID format for user_id: {user_id}")
        raise HTTPException(status_code=400, detail=f"Invalid user ID format: {user_id}")
    
    try:
        logger.info(f"Fetching current user data for user ID: {user_id}")
        current = supabase.table("users").select("*").eq("id", user_id).single().execute().data
        if not current:
            logger.warning(f"User not found with ID: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
            
        data = updates.dict(exclude_unset=True)

        payload = {
            "full_name": data.get("full_name", current["full_name"]),
            "email": data.get("email", current["email"]),
            "password_hash": hash_password(data["password"]) if "password" in data else current["password_hash"]
        }

        logger.info(f"Updating user profile for user ID: {user_id}")
        supabase.table("users").update(payload).eq("id", user_id).execute()

        if "role" in data:
            logger.info(f"Updating role for user ID: {user_id}")
            role_resp = supabase.table("roles").select("id").eq("name", data["role"].lower()).single().execute()
            if not role_resp.data:
                logger.warning(f"Invalid role: {data['role']}")
                raise HTTPException(status_code=400, detail="Invalid role")

            supabase.table("user_roles").update({
                "role_id": role_resp.data["id"]
            }).eq("user_id", user_id).execute()

        return get_user_with_role_by_id(user_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in update_user_by_id: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def change_user_role(user_id: str, new_role: str):
    """Change user role"""
    if not is_valid_uuid(user_id):
        logger.warning(f"Invalid UUID format for user_id: {user_id}")
        raise HTTPException(status_code=400, detail=f"Invalid user ID format: {user_id}")

    try:
        # Step 1: Fetch the current role of the user
        logger.info(f"Fetching current role for user ID: {user_id}")
        user_role_resp = supabase.table("user_roles").select("role_id").eq("user_id", user_id).single().execute()
        if not user_role_resp.data:
            logger.warning(f"User not found in user_roles table for user ID: {user_id}")
            raise HTTPException(status_code=404, detail="User not found in user_roles table")

        current_role_id = user_role_resp.data["role_id"]

        # Step 2: Check if the new role exists in the roles table
        logger.info(f"Fetching role data for new role: {new_role}")
        role_resp = supabase.table("roles").select("id").eq("name", new_role.lower()).single().execute()
        if not role_resp.data:
            logger.warning(f"Role '{new_role}' does not exist")
            raise HTTPException(status_code=400, detail=f"Role '{new_role}' does not exist")

        new_role_id = role_resp.data["id"]

        # Step 3: Check if the current role is the same as the new role
        if current_role_id == new_role_id:
            logger.info(f"User ID: {user_id} already has the role '{new_role}'")
            return {"message": "User already has this role"}

        # Step 4: Update the role if it differs from the current role
        logger.info(f"Updating role for user ID: {user_id} to {new_role}")
        supabase.table("user_roles").update({
            "role_id": new_role_id
        }).eq("user_id", user_id).execute()

        return {"message": "Role updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in change_user_role: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def list_users_by_role(role_name: str):
    """List all users with a specific role"""
    try:
        # Step 1: Fetch the role_id using the role name from the 'roles' table
        logger.info(f"Fetching users with role: {role_name}")
        role_resp = supabase.table("roles").select("id").eq("name", role_name.lower()).single().execute()
        if not role_resp.data:
            logger.warning(f"Role '{role_name}' not found")
            raise HTTPException(status_code=404, detail=f"Role '{role_name}' not found")

        role_id = role_resp.data["id"]

        # Step 2: Fetch user_ids mapped to the role_id from the 'user_roles' table
        user_roles_resp = supabase.table("user_roles").select("user_id").eq("role_id", role_id).execute()
        if not user_roles_resp.data:
            logger.info(f"No users found for role: {role_name}")
            return []  # No users found for this role

        user_ids = [entry["user_id"] for entry in user_roles_resp.data]

        # Step 3: Fetch complete user data for all user_ids from the 'users' table
        users_resp = supabase.table("users").select("*").in_("id", user_ids).execute()
        if not users_resp.data:
            logger.info(f"No users found for the given user_ids: {user_ids}")
            return []  # No users found for the given user_ids

        # Step 4: Return the users with role information
        logger.info(f"Found {len(users_resp.data)} users for role '{role_name}'")
        return [{"id": user["id"], "email": user["email"], "full_name": user["full_name"], 
                "created_at": user["created_at"], "role": role_name} for user in users_resp.data]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in list_users_by_role: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def list_admin_names_only():
    """List admin names only"""
    try:
        logger.info("Fetching list of all admin names")
        role_resp = supabase.table("roles").select("id").eq("name", "admin").single().execute()
        if not role_resp.data:
            return []

        role_id = role_resp.data["id"]
        user_roles = supabase.table("user_roles").select("user_id").eq("role_id", role_id).execute()
        
        if not user_roles.data:
            return []
            
        user_ids = [r["user_id"] for r in user_roles.data]
        users = supabase.table("users").select("id, full_name").in_("id", user_ids).execute().data
        return users
        
    except Exception as e:
        logger.error(f"Database error in list_admin_names_only: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
