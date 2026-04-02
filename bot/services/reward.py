from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories import RewardRepository, PointsRepository
from bot.services.notification import NotificationService


class RewardService:
    def __init__(self, session: AsyncSession, notification_service: NotificationService):
        self.reward_repo = RewardRepository(session)
        self.points_repo = PointsRepository(session)
        self.notification_service = notification_service
    
    async def suggest_reward(
        self,
        title: str,
        description: str,
        user_id: int
    ) -> int:
        reward = await self.reward_repo.create_reward(
            title=title,
            description=description,
            cost=None,
            status='proposed',
            proposed_by=user_id
        )
        
        await self.notification_service.notify_reward_suggested(reward.id)
        return reward.id
    
    async def create_system_reward(
        self,
        title: str,
        description: str,
        cost: int
    ) -> int:
        reward = await self.reward_repo.create_reward(
            title=title,
            description=description,
            cost=cost,
            status='active'
        )
        return reward.id
    
    async def get_active_rewards(self) -> list:
        return await self.reward_repo.get_active_rewards()
    
    async def get_pending_rewards(self) -> list:
        return await self.reward_repo.get_pending_rewards()
    
    async def approve_reward(self, reward_id: int, cost: int) -> None:
        reward = await self.reward_repo.update_reward_status(reward_id, 'active', cost)
        await self.notification_service.notify_reward_approved(reward.proposed_by)
    
    async def redeem_reward(self, reward_id: int, user_id: int) -> bool:
        reward = await self.reward_repo.get_reward(reward_id)
        if not reward or reward.status != 'active' or not reward.cost:
            return False
        
        balance = await self.points_repo.get_user_balance(user_id)
        if balance < reward.cost:
            return False
        
        request = await self.reward_repo.create_reward_request(reward_id, user_id)
        await self.notification_service.notify_reward_requested(request.id)
        return True
    
    async def get_pending_reward_requests(self) -> list:
        return await self.reward_repo.get_pending_reward_requests()
    
    async def approve_reward_request(self, request_id: int) -> None:
        request = await self.reward_repo.update_reward_request_status(request_id, 'approved')
        
        reward = await self.reward_repo.get_reward(request.reward_id)
        if reward and reward.cost:
            await self.points_repo.add_points(
                request.user_id,
                -reward.cost,
                f'reward_redemption_{request_id}'
            )
            await self.notification_service.notify_reward_request_approved(
                request.user_id,
                reward.title
            )
