# routes/admin_routes.py

#Importing libraries
from fastapi import APIRouter, Depends, HTTPException
from core.dependencies import require_admin
from schemas.admin_schema import AdminOut, AdminUpdate, AdminCreate
from supabase_service.admin_service import (
    get_admin_profile,
    update_admin_profile,
    delete_admin,
    create_user,
    update_user_by_id,
    get_user_with_role_by_id,
    list_users_by_role,
    list_admin_names_only,
    change_user_role
)
from loguru import logger

# Set up logger
logger.add("app.log", level="INFO") 

router = APIRouter(prefix="/admin", tags=["Admin"])

# 1. Admin CRUD on themselves
@router.get("/me", response_model=AdminOut)
def get_my_profile(current_user=Depends(require_admin)):
    """
    Fetch the profile of the currently logged-in admin.
    """
    logger.info(f"Fetching profile for admin ID: {current_user['id']}")
    return get_admin_profile(current_user["id"])

@router.put("/me/update", response_model=AdminOut)
def update_my_profile(updates: AdminUpdate, current_user=Depends(require_admin)):
    """
    Update the profile of the currently logged-in admin.
    """
    logger.info(f"Updating profile for admin ID: {current_user['id']}")
    return update_admin_profile(current_user["id"], updates)

@router.delete("/me/delete")
def delete_my_profile(current_user=Depends(require_admin)):
    """
    Delete the profile of the currently logged-in admin.
    """
    logger.info(f"Deleting profile for admin ID: {current_user['id']}")
    return delete_admin(current_user["id"])


# 2. Researcher CRUD
@router.post("/researcher/add", response_model=AdminOut)
def add_researcher(user: AdminCreate, current_user=Depends(require_admin)):
    """
    Add a new researcher user.
    """
    if user.role.lower() != "researcher":
        logger.warning(f"Attempted to add non-researcher role: {user.role}")
        raise HTTPException(status_code=400, detail="Only role 'researcher' allowed here")
    logger.info(f"Adding new researcher: {user.email}")
    return create_user(user)

@router.get("/researcher/list", response_model=list[AdminOut])
def list_all_researchers(current_user=Depends(require_admin)):
    """
    Get a list of all researchers.
    """
    logger.info("Fetching list of all researchers")
    return list_users_by_role("researcher")

@router.get("/researcher", response_model=AdminOut)
def get_researcher_by_id(user_id: str, current_user=Depends(require_admin)):
    """
    Get details of a researcher by their user ID.
    """
    logger.info(f"Fetching researcher details for user ID: {user_id}")
    return get_user_with_role_by_id(user_id)

@router.put("/researcher/update", response_model=AdminOut)
def update_researcher(user_id: str, updates: AdminUpdate, current_user=Depends(require_admin)):
    """
    Update a researcher's details by their user ID.
    """
    logger.info(f"Updating researcher details for user ID: {user_id}")
    return update_user_by_id(user_id, updates)

@router.put("/researcher/make-admin")
def make_researcher_admin(user_id: str, current_user=Depends(require_admin)):
    """
    Promote a researcher to an admin role.
    """
    logger.info(f"Promoting researcher ID {user_id} to admin.")
    return change_user_role(user_id, "admin")


# 3. Editor CRUD
@router.post("/editor/add", response_model=AdminOut)
def add_editor(user: AdminCreate, current_user=Depends(require_admin)):
    """
    Add a new editor user.
    """
    if user.role.lower() != "editor":
        logger.warning(f"Attempted to add non-editor role: {user.role}")
        raise HTTPException(status_code=400, detail="Only role 'editor' allowed here")
    logger.info(f"Adding new editor: {user.email}")
    return create_user(user)

@router.get("/editor/list", response_model=list[AdminOut])
def list_all_editors(current_user=Depends(require_admin)):
    """
    Get a list of all editors.
    """
    logger.info("Fetching list of all editors")
    return list_users_by_role("editor")

@router.get("/editor", response_model=AdminOut)
def get_editor_by_id(user_id: str, current_user=Depends(require_admin)):
    """
    Get details of an editor by their user ID.
    """
    logger.info(f"Fetching editor details for user ID: {user_id}")
    return get_user_with_role_by_id(user_id)

@router.put("/editor/update", response_model=AdminOut)
def update_editor(user_id: str, updates: AdminUpdate, current_user=Depends(require_admin)):
    """
    Update an editor's details by their user ID.
    """
    logger.info(f"Updating editor details for user ID: {user_id}")
    return update_user_by_id(user_id, updates)

@router.put("/editor/make-admin")
def make_editor_admin(user_id: str, current_user=Depends(require_admin)):
    """
    Promote an editor to an admin role.
    """
    logger.info(f"Promoting editor ID {user_id} to admin.")
    return change_user_role(user_id, "admin")


# 4. Admin list (names only)
@router.get("/list", response_model=list[dict])
def get_all_admins(current_user=Depends(require_admin)):
    """
    Get a list of admin names only.
    """
    logger.info("Fetching list of all admin names")
    return list_admin_names_only()
