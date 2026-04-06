from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import Optional
from decimal import Decimal

class FinancialRecordCreate(BaseModel):
    type: str = Field(..., description="'income' or 'expense'")
    amount: Decimal = Field(..., gt=0)
    category: str = Field(..., max_length=100)
    date: date
    user_id: int
    description: Optional[str] = Field(None, max_length=256)
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v not in ['income', 'expense']:
            raise ValueError("Type must be 'income' or 'expense' (case-sensitive)")
        return v
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v is None:
            raise ValueError("Amount is required")
        if v <= 0:
            raise ValueError("Amount must be greater than 0.00")
        return v


class FinancialRecordUpdate(BaseModel):
    type: Optional[str] = Field(None)
    amount: Optional[Decimal] = Field(None, gt=0)
    category: Optional[str] = Field(None, max_length=100)
    date: Optional[date] = None  # type: ignore
    description: Optional[str] = Field(None, max_length=256)
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v is not None and v not in ['income', 'expense']:
            raise ValueError("Type must be 'income' or 'expense'")
        return v
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than 0.00")
        return v


class FinancialRecordResponse(BaseModel):
    id: int
    user_id: int
    type: str
    amount: Decimal
    category: str
    date: date
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True