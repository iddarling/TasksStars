from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import PointsHistory, User


class PointsService:
    @staticmethod
    async def get_user_balance(db: AsyncSession, user_id: int) -> int:
        # Use cached balance for fast retrieval
        result = await db.execute(
            select(User.cached_balance).where(User.id == user_id)
        )
        balance = result.scalar()
        return balance if balance is not None else 0

    @staticmethod
    async def add_points(db: AsyncSession, user_id: int, amount: int, source: str):
        # Create record in points history
        new_entry = PointsHistory(user_id=user_id, amount=amount, source=source)
        db.add(new_entry)
        
        # Update cached balance atomically
        result = await db.execute(
            select(User).where(User.id == user_id).with_for_update()
        )
        user = result.scalar_one()
        user.cached_balance += amount
        
        await db.flush()
        return new_entry
    
    @staticmethod
    async def recalculate_balance(db: AsyncSession, user_id: int) -> int:
        """Recalculate balance from history (for maintenance/repair)"""
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
        await db.flush()
        
        return balance
