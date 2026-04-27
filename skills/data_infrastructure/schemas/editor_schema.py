# schemas/editor_schema.py

#Import libraries
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

# Output model for Editor data
class EditorOut(BaseModel):
    id: UUID  # Unique identifier for the editor
    email: EmailStr  # Editor's email address
    full_name: str  # Editor's full name
    created_at: str  # Timestamp when the editor was created
    role: str  # Role of the editor (e.g., editor)

# Model for updating Editor details
class EditorUpdate(BaseModel):
    email: Optional[EmailStr] = None  # Optional new email address
    full_name: Optional[str] = None  # Optional new full name
    password: Optional[str] = None  # Optional new password

# Model for creating a new Editor
class EditorCreate(BaseModel):
    email: EmailStr  # Editor's email address
    full_name: str  # Editor's full name
    password: str  # Editor's password
