# services/supabase_service/auth_service.py

#Import Libraries
from fastapi import HTTPException
from core.settings import supabase
from core.security import hash_password
from uuid import uuid4
from loguru import logger

# Set up logger
logger.add("app.log", level="INFO") 

def get_user_with_roles_by_email(email: str):
    """
    Fetch the user and their role based on the provided email.
    This function retrieves the user data from the 'users' table, then fetches the user's role 
    from the 'user_roles' table and maps it to the corresponding role name from the 'roles' table.

    Parameters:
    - email: The email address of the user to retrieve.

    Returns:
    - A dictionary containing user data along with their role, or None if no user is found.
    """
    # Step 1: Fetch user by email
    logger.info(f"Fetching user data for email: {email}")
    user_resp = supabase.table("users").select("*").eq("email", email).execute()
    if not user_resp.data:
        logger.warning(f"User not found with email: {email}")
        return None
    user = user_resp.data[0]
    user_id = user["id"]

    # Step 2: Fetch user role_id from user_roles
    logger.info(f"Fetching role information for user ID: {user_id}")
    user_roles_resp = supabase.table("user_roles").select("role_id").eq("user_id", user_id).single().execute()
    if not user_roles_resp.data:
        logger.warning(f"Role mapping not found for user ID: {user_id}")
        return None
    role_id = user_roles_resp.data["role_id"]

    # Step 3: Fetch role name using role_id
    logger.info(f"Fetching role name for role ID: {role_id}")
    role_resp = supabase.table("roles").select("name").eq("id", role_id).single().execute()
    if not role_resp.data:
        logger.warning(f"Role not found for role ID: {role_id}")
        return None
    role_name = role_resp.data["name"]

    # Return user data along with role information
    logger.info(f"User found: {user['email']} with role: {role_name}")
    return {
        **user,
        "role": role_name
    }

def create_user_with_default_role(user_data):
    """
    Create a new user with the default role 'researcher'. 
    If the user already exists, it returns None. If the user is successfully created, 
    it assigns the default role to the user and returns the user data with their role.

    Parameters:
    - user_data: The user data including email, full_name, and password.

    Returns:
    - The created user with their role or None if creation fails.
    """
    # Check if user already exists
    logger.info(f"Checking if user already exists with email: {user_data.email}")
    existing = get_user_with_roles_by_email(user_data.email)
    if existing:
        logger.warning(f"User already exists with email: {user_data.email}")
        return None

    # Step 1: Create new user in the 'users' table
    user_id = str(uuid4())
    logger.info(f"Creating new user with email: {user_data.email}")
    response = supabase.table("users").insert({
        "id": user_id,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "password_hash": hash_password(user_data.password),
    }).execute()

    if not response.data:
        logger.error(f"Failed to create user with email: {user_data.email}")
        return None

    # Step 2: Get the role ID for "researcher"
    logger.info(f"Fetching role ID for 'researcher'")
    role_resp = supabase.table("roles").select("id").eq("name", "researcher").single().execute()
    if not role_resp.data:
        logger.error("Default role 'researcher' not found in roles table")
        raise HTTPException(status_code=500, detail="Default role 'researcher' not found in roles table")

    role_id = role_resp.data["id"]

    # Step 3: Assign the "researcher" role to the user in the 'user_roles' table
    logger.info(f"Assigning 'researcher' role to user ID: {user_id}")
    supabase.table("user_roles").insert({
        "user_id": user_id,
        "role_id": role_id
    }).execute()

    # Return the created user with role data
    logger.info(f"User {user_data.email} created successfully with 'researcher' role")
    return get_user_with_roles_by_email(user_data.email)
