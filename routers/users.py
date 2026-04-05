from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.models import User, Role
from schemas.user import UserCreate, UserResponse, UserUpdate
from utils.database import get_db
from utils.auth import hash_password
from utils.auth_dependency import get_current_user, RoleChecker
from typing import List

router = APIRouter(prefix="/users", tags=["users"])

# POST /users - Create a new user (Admin only)
@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['admin']))
):
    """Create a new user (Admin only)"""
    
    # Check if user already exists
    stmt = select(User).where(User.username == user_data.username)
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email already exists
    stmt = select(User).where(User.email == user_data.email)
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Get the specified role (or default to viewer)
    stmt = select(Role).where(Role.name == user_data.role)
    role_result = await db.execute(stmt)
    role = role_result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{user_data.role}' does not exist. Must be 'viewer', 'analyst', or 'admin'"
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        role_id=role.id
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


# GET /users - List all users (Admin only)
@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['admin']))
):
    """List all users with pagination (Admin only)"""
    
    stmt = select(User).offset(skip).limit(limit)
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return users


# GET /users/{user_id} - Get user details
@router.get("/{target_user_id}", response_model=UserResponse)
async def get_user(
    target_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user details (self or admin only)"""
    # Check if admin or accessing own profile
    if current_user.id != target_user_id and current_user.role.name != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
        )
    
    stmt = select(User).where(User.id == target_user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


# PUT /users/{user_id} - Update user
@router.put("/{target_user_id}", response_model=UserResponse)
async def update_user(
    target_user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['admin']))
):
    """Update user details (admin only)"""
    
    stmt = select(User).where(User.id == target_user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    if user_data.username:
        # Check if username is unique
        stmt = select(User).where(User.username == user_data.username)
        existing_result = await db.execute(stmt)
        existing_user = existing_result.scalar_one_or_none()
        if existing_user and existing_user.id != target_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        user.username = user_data.username
    
    if user_data.email:
        # Check if email is unique
        stmt = select(User).where(User.email == user_data.email)
        existing_result = await db.execute(stmt)
        existing_user = existing_result.scalar_one_or_none()
        if existing_user and existing_user.id != target_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
        user.email = user_data.email
    
    if user_data.password:
        user.password_hash = hash_password(user_data.password)
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    await db.commit()
    await db.refresh(user)
    
    return user