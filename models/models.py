from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, DECIMAL, Date, func
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db import Base

class Role(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    users = relationship("User", back_populates="role")

    def __str__(self):
        return self.name


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    email = Column(String(254), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    role = relationship("Role", back_populates="users")
    financial_records = relationship("FinancialRecord", back_populates="user")

    def __str__(self):
        return self.username


class FinancialRecord(Base):
    __tablename__ = 'financial_records'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(String(10), nullable=False)  # 'income' or 'expense'
    amount = Column(DECIMAL(10, 2), nullable=False)
    category = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="financial_records")

    def __str__(self):
        return f"{self.category} - {self.amount}"