from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings
engine = create_async_engine(settings.DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False)
Base = declarative_base()

async def init_db():
    """Create all tables and seed predefined roles and initial admin user"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed predefined roles and initial admin user
    async with async_session() as session:
        from models.models import Role, User
        from sqlalchemy.future import select
        from utils.auth import hash_password
        
        # Check if roles already exist
        stmt = select(Role).where(Role.name == 'admin')
        result = await session.execute(stmt)
        if result.scalar_one_or_none() is None:
            # Create predefined roles
            roles = [
                Role(name='admin', description='Administrator with full access to create, read, update, delete records and manage users'),
                Role(name='analyst', description='Analyst can view and analyze all users financial records and access cross-user analytics and insights'),
                Role(name='viewer', description='Viewer can only view their own financial records. No access to other users data or analytics')
            ]
            session.add_all(roles)
            await session.commit()
        
        # Check if initial admin user exists
        stmt = select(User).where(User.username == 'admin')
        result = await session.execute(stmt)
        if result.scalar_one_or_none() is None:
            # Get admin role
            stmt = select(Role).where(Role.name == 'admin')
            admin_role = await session.execute(stmt)
            admin_role = admin_role.scalar_one()
            
            # Create initial admin user
            initial_admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=hash_password('admin123'),
                role_id=admin_role.id,
                is_active=True
            )
            session.add(initial_admin)
            await session.commit()