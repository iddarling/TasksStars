from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories import UserRepository, PointsRepository


class UserService:
    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)
        self.points_repo = PointsRepository(session)
    
    async def get_or_create_user(self, telegram_id: int, is_admin: bool = False,
                                first_name: str | None = None,
                                last_name: str | None = None,
                                username: str | None = None) -> tuple:
        role = 'admin' if is_admin else 'user'
        user = await self.user_repo.get_or_create(telegram_id, role, first_name, last_name, username)
        balance = await self.points_repo.get_user_balance(telegram_id)
        return user, balance
    
    async def get_user_balance(self, telegram_id: int) -> int:
        return await self.points_repo.get_user_balance(telegram_id)
    
    async def get_points_history(self, telegram_id: int) -> list:
        return await self.points_repo.get_user_history(telegram_id)
