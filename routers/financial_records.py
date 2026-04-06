from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from models.models import FinancialRecord, User
from schemas.financial_record import FinancialRecordCreate, FinancialRecordResponse, FinancialRecordUpdate
from schemas.pagination import PaginatedResponse
from utils.database import get_db
from utils.auth_dependency import get_current_user, RoleChecker
from typing import Optional
from datetime import date

router = APIRouter(prefix="/records", tags=["financial_records"])

# Create new financial record (admin only)
@router.post("", response_model=FinancialRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_record(
    record_data: FinancialRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['admin']))
):
    
    # Validate that the target user exists
    stmt = select(User).where(User.id == record_data.user_id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {record_data.user_id} not found"
        )

    # Create new financial record
    new_record = FinancialRecord(
        user_id=record_data.user_id,
        type=record_data.type,
        amount=record_data.amount,
        category=record_data.category,
        date=record_data.date,
        description=record_data.description
    )
    
    db.add(new_record)
    await db.commit()
    await db.refresh(new_record)
    
    return new_record

# Get all financial records with pagination and filtering.

@router.get("", response_model=PaginatedResponse[FinancialRecordResponse])
async def list_records(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    category: Optional[str] = Query(None, description="Filter by transaction category"),
    type: Optional[str] = Query(None, description="Filter by type: 'income' or 'expense'"),
    start_date: Optional[date] = Query(None, description="Filter from date (inclusive)"),
    end_date: Optional[date] = Query(None, description="Filter to date (inclusive)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['viewer', 'analyst', 'admin']))
):
    """List records with pagination and filtering (viewers see own only)."""
    
    # Build base query - viewers see only their records
    if current_user.role.name == 'viewer':
        stmt = select(FinancialRecord).where(FinancialRecord.user_id == current_user.id)
    else:
        # Analysts and admins can see all records
        stmt = select(FinancialRecord)
    
    # Optional filters
    if category:
        stmt = stmt.where(FinancialRecord.category == category)
    
    if type:
        stmt = stmt.where(FinancialRecord.type == type)
    
    if start_date:
        stmt = stmt.where(FinancialRecord.date >= start_date)
    
    if end_date:
        stmt = stmt.where(FinancialRecord.date <= end_date)
    
    # Order by date
    stmt = stmt.order_by(FinancialRecord.date.desc())
    
    # Get total count
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0
    
    # Calculate pagination
    pages = (total + size - 1) // size if size > 0 else 1
    skip = (page - 1) * size
    
    # Fetch paginated records
    stmt = stmt.offset(skip).limit(size)
    result = await db.execute(stmt)
    records = result.scalars().all()
    
    return PaginatedResponse(
        items=records,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

# Get record by ID (viewers see own only)
@router.get("/{record_id}", response_model=FinancialRecordResponse)
async def get_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['viewer', 'analyst', 'admin']))
):
    
    # Fetch the record
    stmt = select(FinancialRecord).where(FinancialRecord.id == record_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record with ID {record_id} not found"
        )
    
    # Viewers can only access their own records
    if current_user.role.name == 'viewer' and record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own financial records"
        )

    return record

# Update record fields (admin only)
@router.put("/{record_id}", response_model=FinancialRecordResponse)
async def update_record(
    record_id: int,
    record_data: FinancialRecordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['admin']))
):
    """Update record fields (admin only)."""
    
    # Find the record to update
    stmt = select(FinancialRecord).where(FinancialRecord.id == record_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record with ID {record_id} not found"
        )
    
    # Update fields if provided
    if record_data.type is not None:
        record.type = record_data.type
    
    if record_data.amount is not None:
        record.amount = record_data.amount
    
    if record_data.category is not None:
        record.category = record_data.category
    
    if record_data.date is not None:
        record.date = record_data.date
    
    if record_data.description is not None:
        record.description = record_data.description
    
    # Save changes
    await db.commit()
    await db.refresh(record)
    
    return record


# Delete record permanently (admin only)

@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['admin']))
):
    
    # Find the record to delete
    stmt = select(FinancialRecord).where(FinancialRecord.id == record_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record with ID {record_id} not found"
        )
    
    # Delete the record from database
    await db.delete(record)
    await db.commit()