from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(default="viewer", description="Role: viewer, analyst, or admin")

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=150)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    role_id: int

    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    password_hash: str