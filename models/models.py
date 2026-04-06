from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, DECIMAL, Date, func
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db import Base

class Role(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    users = relationship("User", back_populates="role", cascade="all, delete-orphan")

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, nullable=False, index=True)
    email = Column(String(254), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    role = relationship("Role", back_populates="users", lazy="selectin")
    financial_records = relationship("FinancialRecord", back_populates="user", cascade="all, delete-orphan")

    def __str__(self):
        return self.username

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.name if self.role else 'None'}')>"


class FinancialRecord(Base):
    __tablename__ = 'financial_records'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    type = Column(String(10), nullable=False, index=True)  # 'income' or 'expense'
    amount = Column(DECIMAL(12, 2), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="financial_records")

    def __str__(self):
        return f"{self.category} - {self.amount} ({self.type})"

    def __repr__(self):
        return f"<FinancialRecord(id={self.id}, user_id={self.user_id}, type='{self.type}', amount={self.amount})>"