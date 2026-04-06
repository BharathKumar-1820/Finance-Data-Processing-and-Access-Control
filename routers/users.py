from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from models.models import User, Role
from schemas.user import UserCreate, UserResponse, UserUpdate
from schemas.pagination import PaginatedResponse
from utils.database import get_db
from utils.auth import hash_password
from utils.auth_dependency import get_current_user, RoleChecker

router = APIRouter(prefix="/users", tags=["users"])

# Create new user (admin only)
@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['admin']))
):
    """Create new user account (admin only)."""
    
    # Check if username already exists
    stmt = select(User).where(User.username == user_data.username)
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_data.username}' is already taken"
        )
    
    # Check if email already exists
    stmt = select(User).where(User.email == user_data.email)
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{user_data.email}' is already registered"
        )
    
    # Validate that the specified role exists
    stmt = select(Role).where(Role.name == user_data.role)
    role_result = await db.execute(stmt)
    role = role_result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{user_data.role}' does not exist. Valid roles: 'viewer', 'analyst', 'admin'"
        )
    
    # Create new user with hashed password
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
    return UserResponse.from_orm_user(new_user)


# Get All users with pagination (admin and analyst only)
@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['admin', 'analyst']))
):
    """List all users with pagination (admin and analyst only)."""
    
    # Get total user count
    total_stmt = select(func.count()).select_from(User)
    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0
    
    # Calculate pagination
    pages = (total + size - 1) // size if size > 0 else 1
    skip = (page - 1) * size

    # Fetch paginated users
    stmt = select(User).offset(skip).limit(size)
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    users_resp = [UserResponse.from_orm_user(u) for u in users]
    
    return PaginatedResponse(
        items=users_resp,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

# Get user details by ID (viewers see own only)
@router.get("/{target_user_id}", response_model=UserResponse)
async def get_user(
    target_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    # Check access permissions - viewers can only access their own profile
    if current_user.id != target_user_id and current_user.role.name not in ['admin', 'analyst']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile."
        )
    
    # Fetch the requested user
    stmt = select(User).where(User.id == target_user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {target_user_id} not found"
        )
    
    return UserResponse.from_orm_user(user)


# Update user details (admin only)
@router.put("/{target_user_id}", response_model=UserResponse)
async def update_user(
    target_user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['admin']))
):
    """Update user details (admin only)."""
    
    # Find the user to update
    stmt = select(User).where(User.id == target_user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {target_user_id} not found"
        )
    
    # Update username if provided (check uniqueness)
    if user_data.username is not None:
        stmt = select(User).where(User.username == user_data.username)
        existing_result = await db.execute(stmt)
        existing_user = existing_result.scalar_one_or_none()
        if existing_user and existing_user.id != target_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{user_data.username}' is already taken"
            )
        user.username = user_data.username
    
    # Update email if provided (check uniqueness)
    if user_data.email is not None:
        stmt = select(User).where(User.email == user_data.email)
        existing_result = await db.execute(stmt)
        existing_user = existing_result.scalar_one_or_none()
        if existing_user and existing_user.id != target_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{user_data.email}' is already registered"
            )
        user.email = user_data.email
    
    # Update password if provided (will be hashed)
    if user_data.password is not None:
        user.password_hash = hash_password(user_data.password)
    
    # Update active status if provided
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    # Commit changes and refresh user object
    await db.commit()
    await db.refresh(user)
    return UserResponse.from_orm_user(user)

# Delete user (admin only)
@router.delete("/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    target_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['admin']))
):
    """Delete user and their financial records permanently (admin only)."""
    
    # Prevent admin from deleting themselves
    if target_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account."
        )
    
    # Find the user to delete
    stmt = select(User).where(User.id == target_user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {target_user_id} not found"
        )
    
    # Delete the user (cascades to delete financial records)
    await db.delete(user)
    await db.commit()