#schemas\researcher_schema.py

#Import Libraries
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

# Model for updating Researcher details
class ResearcherUpdate(BaseModel):
    full_name: Optional[str] = None  # Optional new full name for the researcher
    email: Optional[EmailStr] = None  # Optional new email address for the researcher
    password: Optional[str] = None  # Optional new password for the researcher

# Output model for Researcher data
class ResearcherOut(BaseModel):
    id: UUID  # Unique identifier for the researcher
    email: EmailStr  # Researcher's email address
    full_name: Optional[str]  # Optional full name of the researcher
    created_at: datetime  # Timestamp when the researcher was created
    role: str  # Role of the researcher (e.g., researcher)
