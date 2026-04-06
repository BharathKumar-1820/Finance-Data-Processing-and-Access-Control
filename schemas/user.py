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
    role_id: int
    role_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm_user(cls, user):
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            role_id=user.role_id,
            role_name=user.role.name if user.role else None,
            created_at=user.created_at,
            updated_at=user.updated_at
        )


class UserInDB(UserResponse):
    password_hash: str