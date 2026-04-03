"""
Migration script to initialize cached_balance for existing users.
Run this once after deploying the balance caching feature.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from app.models.base import User, PointsHistory
from app.core.config import settings


async def migrate_balance_cache():
    """Initialize cached_balance for all existing users."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get all users
        result = await db.execute(select(User.id))
        user_ids = result.scalars().all()
        
        print(f"Migrating {len(user_ids)} users...")
        
        for user_id in user_ids:
            # Calculate balance from history
            result = await db.execute(
                select(func.sum(PointsHistory.amount)).where(
                    PointsHistory.user_id == user_id
                )
            )
            balance = result.scalar() or 0
            
            # Update cached balance
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one()
            user.cached_balance = balance
            
            print(f"  User {user_id}: balance = {balance}")
        
        await db.commit()
        print("Migration complete!")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate_balance_cache())
