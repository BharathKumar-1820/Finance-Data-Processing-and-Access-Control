from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from db import async_session

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session"""
    async with async_session() as session:
        yield session