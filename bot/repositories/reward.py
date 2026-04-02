from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import Reward, RewardRequest


class RewardRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_reward(
        self,
        title: str,
        description: str,
        cost: int | None,
        status: str,
        proposed_by: int | None = None
    ) -> Reward:
        reward = Reward(
            title=title,
            description=description,
            cost=cost,
            status=status,
            proposed_by=proposed_by
        )
        self.session.add(reward)
        await self.session.commit()
        await self.session.refresh(reward)
        return reward
    
    async def get_reward(self, reward_id: int) -> Reward | None:
        stmt = select(Reward).where(Reward.id == reward_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_active_rewards(self) -> list[Reward]:
        stmt = select(Reward).where(Reward.status == 'active')
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_pending_rewards(self) -> list[Reward]:
        stmt = select(Reward).where(Reward.status == 'proposed')
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_reward_status(self, reward_id: int, status: str, cost: int | None = None) -> Reward:
        stmt = select(Reward).where(Reward.id == reward_id)
        result = await self.session.execute(stmt)
        reward = result.scalar_one()
        
        reward.status = status
        if cost is not None:
            reward.cost = cost
        
        await self.session.commit()
        await self.session.refresh(reward)
        return reward
    
    async def create_reward_request(self, reward_id: int, user_id: int) -> RewardRequest:
        request = RewardRequest(
            reward_id=reward_id,
            user_id=user_id,
            status='pending'
        )
        self.session.add(request)
        await self.session.commit()
        await self.session.refresh(request)
        return request
    
    async def get_pending_reward_requests(self) -> list[RewardRequest]:
        stmt = select(RewardRequest).where(RewardRequest.status == 'pending')
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_reward_request_status(self, request_id: int, status: str) -> RewardRequest:
        stmt = select(RewardRequest).where(RewardRequest.id == request_id)
        result = await self.session.execute(stmt)
        request = result.scalar_one()
        
        request.status = status
        await self.session.commit()
        await self.session.refresh(request)
        return request
