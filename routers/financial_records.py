from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from models.models import FinancialRecord, User, Role
from schemas.financial_record import FinancialRecordCreate, FinancialRecordResponse, FinancialRecordUpdate
from utils.database import get_db
from utils.auth_dependency import get_current_user, RoleChecker
from typing import List, Optional
from datetime import date
router = APIRouter(prefix="/records", tags=["financial_records"])
# POST /records - Create a financial record
@router.post("", response_model=FinancialRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_record(
    record_data: FinancialRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['admin']))
):
    """Create a new financial record (Admin only)"""
    
    # Create new record
    new_record = FinancialRecord(
        user_id=current_user.id,
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


# GET /records - List financial records with filtering
@router.get("", response_model=List[FinancialRecordResponse])
async def list_records(
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = Query(None, description="Filter by category"),
    type: Optional[str] = Query(None, description="Filter by type (income/expense)"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['viewer', 'analyst', 'admin']))
):
    """List financial records with optional filtering (All roles)"""
    
    # Build query - viewers see only their own, analysts and admins see all
    if current_user.role.name == 'viewer':
        stmt = select(FinancialRecord).where(FinancialRecord.user_id == current_user.id)
    else:
        # Analysts and admins can see all records
        stmt = select(FinancialRecord)
    
    # Apply filters
    if category:
        stmt = stmt.where(FinancialRecord.category == category)
    
    if type:
        stmt = stmt.where(FinancialRecord.type == type)
    
    if start_date:
        stmt = stmt.where(FinancialRecord.date >= start_date)
    
    if end_date:
        stmt = stmt.where(FinancialRecord.date <= end_date)
    
    stmt = stmt.offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    records = result.scalars().all()
    
    return records


# GET /records/{record_id} - Get single record
@router.get("/{record_id}", response_model=FinancialRecordResponse)
async def get_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['viewer', 'analyst', 'admin']))
):
    """Get a single financial record (All roles)"""
    
    stmt = select(FinancialRecord).where(FinancialRecord.id == record_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )
    
    # Viewers can only see their own records
    if current_user.role.name == 'viewer' and record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own records"
        )

    return record


# PUT /records/{record_id} - Update record
@router.put("/{record_id}", response_model=FinancialRecordResponse)
async def update_record(
    record_id: int,
    record_data: FinancialRecordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['admin']))
):
    """Update a financial record (Admin only)"""
    
    stmt = select(FinancialRecord).where(FinancialRecord.id == record_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )
    
    # Update fields if provided
    if record_data.type:
        if record_data.type not in ['income', 'expense']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Type must be 'income' or 'expense'"
            )
        record.type = record_data.type
    
    if record_data.amount:
        record.amount = record_data.amount
    
    if record_data.category:
        record.category = record_data.category
    
    if record_data.date:
        record.date = record_data.date
    
    if record_data.description is not None:
        record.description = record_data.description
    
    await db.commit()
    await db.refresh(record)
    
    return record


# DELETE /records/{record_id} - Delete record
@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['admin']))
):
    """Delete a financial record (admin only)"""
    stmt = select(FinancialRecord).where(FinancialRecord.id == record_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )
    
    await db.delete(record)
    await db.commit()