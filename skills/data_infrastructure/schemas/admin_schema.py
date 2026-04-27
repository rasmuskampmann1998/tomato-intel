#schemas\admin_schema.py

#Import Lirbaries
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

# Output model for Admin data
class AdminOut(BaseModel):
    id: UUID  # Unique identifier for the admin
    email: EmailStr  # Admin's email address
    full_name: str  # Admin's full name
    created_at: str  # Timestamp when the admin was created
    role: str  # Role of the admin (e.g., admin, researcher)

# Model for updating Admin details
class AdminUpdate(BaseModel):
    email: Optional[EmailStr] = None  # Optional new email address
    full_name: Optional[str] = None  # Optional new full name
    password: Optional[str] = None  # Optional new password
    role: Optional[str] = None  # Optional new role

# Model for creating a new Admin
class AdminCreate(BaseModel):
    email: EmailStr  # Admin's email address
    full_name: str  # Admin's full name
    password: str  # Admin's password
    role: Optional[str] = "researcher"  # Default role is 'researcher'

# Output model for Admin with minimal details (e.g., for lists)
class AdminShortOut(BaseModel):
    id: UUID  # Unique identifier for the admin
    full_name: str  # Admin's full name

# Request model for changing an Admin's role
class RoleChangeRequest(BaseModel):
    user_id: UUID  # ID of the user whose role is being changed
    new_role: str  # The new role to assign to the user
