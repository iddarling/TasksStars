from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import PointsHistory


class PointsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def add_points(self, user_id: int, amount: int, source: str) -> PointsHistory:
        history = PointsHistory(
            user_id=user_id,
            amount=amount,
            source=source
        )
        self.session.add(history)
        await self.session.commit()
        await self.session.refresh(history)
        return history
    
    async def get_user_balance(self, user_id: int) -> int:
        stmt = (
            select(func.coalesce(func.sum(PointsHistory.amount), 0))
            .where(PointsHistory.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar()
    
    async def get_user_history(self, user_id: int) -> list[PointsHistory]:
        stmt = select(PointsHistory).where(PointsHistory.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
