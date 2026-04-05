from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from models.models import FinancialRecord, User, Role
from schemas.dashboard import SummaryResponse, CategoryBreakdownResponse, RecentActivityResponse, TrendDataResponse
from utils.database import get_db
from utils.auth_dependency import get_current_user, RoleChecker
from typing import List
from decimal import Decimal
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# GET /dashboard/summary - Get total income, expense and net balance
@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['viewer', 'analyst', 'admin']))
):
    """Get total income, expense and net balance"""
    
    # For viewers, show only their own data
    # For analysts and admins, show all data
    if current_user.role.name == 'viewer':
        # Calculate total income for viewer
        income_stmt = select(func.sum(FinancialRecord.amount)).where(
            (FinancialRecord.user_id == current_user.id) &
            (FinancialRecord.type == 'income')
        )
        # Calculate total expense for viewer
        expense_stmt = select(func.sum(FinancialRecord.amount)).where(
            (FinancialRecord.user_id == current_user.id) &
            (FinancialRecord.type == 'expense')
        )
    else:
        # Calculate total income for analyst/admin (all data)
        income_stmt = select(func.sum(FinancialRecord.amount)).where(
            FinancialRecord.type == 'income'
        )
        # Calculate total expense for analyst/admin (all data)
        expense_stmt = select(func.sum(FinancialRecord.amount)).where(
            FinancialRecord.type == 'expense'
        )
    
    income_result = await db.execute(income_stmt)
    total_income = income_result.scalar() or Decimal(0)
    
    expense_result = await db.execute(expense_stmt)
    total_expense = expense_result.scalar() or Decimal(0)
    
    # Calculate net balance
    net_balance = total_income - total_expense
    
    return SummaryResponse(
        total_income=total_income,
        total_expense=total_expense,
        net_balance=net_balance
    )

# GET /dashboard/category-breakdown - Get category-wise totals
@router.get("/category-breakdown", response_model=List[CategoryBreakdownResponse])
async def get_category_breakdown(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['analyst', 'admin']))
):
    """Get income and expense breakdown by category"""
    
    # Get category totals for all records (analysts have cross-user visibility)
    stmt = select(
        FinancialRecord.category,
        func.sum(FinancialRecord.amount).label('total')
    ).group_by(
        FinancialRecord.category
    )
    
    result = await db.execute(stmt)
    categories = result.all()
    
    return [
        CategoryBreakdownResponse(category=cat, total_amount=total)
        for cat, total in categories
    ]


# GET /dashboard/recent-activity - Get recent transactions
@router.get("/recent-activity", response_model=List[RecentActivityResponse])
async def get_recent_activity(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['viewer', 'analyst', 'admin']))
):
    """Get recent financial transactions"""
    # Viewers see their own recent activity
    # Analysts and admins see all recent activity
    
    if current_user.role.name == 'viewer':
        stmt = select(FinancialRecord).where(
            FinancialRecord.user_id == current_user.id
        ).order_by(
            FinancialRecord.created_at.desc()
        ).limit(limit)
    else:
        # Analysts and admins see all records
        stmt = select(FinancialRecord).order_by(
            FinancialRecord.created_at.desc()
        ).limit(limit)
    
    result = await db.execute(stmt)
    records = result.scalars().all()
    
    return records


# GET /dashboard/trends - Get monthly trends
@router.get("/trends", response_model=List[TrendDataResponse])
async def get_trends(
    months: int = 6,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(['analyst', 'admin']))
):
    """Get monthly income and expense trends"""
    
    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30 * months)
    
    trends = []
    current_date = start_date.replace(day=1)
    
    while current_date <= end_date:
        # Get next month
        if current_date.month == 12:
            next_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            next_date = current_date.replace(month=current_date.month + 1)
        
        # Get income for month - analysts see all data, admins see all data
        income_stmt = select(func.sum(FinancialRecord.amount)).where(
            (FinancialRecord.type == 'income') &
            (FinancialRecord.date >= current_date.date()) &
            (FinancialRecord.date < next_date.date())
        )
        income_result = await db.execute(income_stmt)
        total_income = income_result.scalar() or Decimal(0)
        
        # Get expense for month - analysts see all data, admins see all data
        expense_stmt = select(func.sum(FinancialRecord.amount)).where(
            (FinancialRecord.type == 'expense') &
            (FinancialRecord.date >= current_date.date()) &
            (FinancialRecord.date < next_date.date())
        )
        expense_result = await db.execute(expense_stmt)
        total_expense = expense_result.scalar() or Decimal(0)
        
        trends.append(TrendDataResponse(
            date=current_date.date(),
            total_income=total_income,
            total_expense=total_expense
        ))
        
        current_date = next_date
    
    return trends