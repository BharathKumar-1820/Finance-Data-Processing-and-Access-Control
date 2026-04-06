from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from decimal import Decimal

class SummaryResponse(BaseModel):
    total_income: Decimal = Field(default=0, ge=0)
    total_expense: Decimal = Field(default=0, ge=0)
    net_balance: Decimal = Field(default=0)


class CategoryBreakdownResponse(BaseModel):
    category: str = Field(..., max_length=100)
    type: str = Field(..., description="'income' or 'expense'")
    total_amount: Decimal = Field(..., ge=0)


class RecentActivityResponse(BaseModel):
    id: int
    user_id: int
    type: str
    amount: Decimal
    category: str
    date: date
    description: Optional[str] = None

    class Config:
        from_attributes = True


class TrendDataResponse(BaseModel):
    date: date
    total_income: Decimal = Field(default=0, ge=0)
    total_expense: Decimal = Field(default=0, ge=0)