from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_or_create(self, telegram_id: int, role: str = 'user', 
                           first_name: str | None = None, 
                           last_name: str | None = None, 
                           username: str | None = None) -> User:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=telegram_id, 
                role=role,
                first_name=first_name,
                last_name=last_name,
                username=username
            )
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        else:
            # Обновляем имя если оно изменилось
            updated = False
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if last_name and user.last_name != last_name:
                user.last_name = last_name
                updated = True
            if username and user.username != username:
                user.username = username
                updated = True
            if updated:
                await self.session.commit()
                await self.session.refresh(user)
        
        return user
    
    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_users(self) -> list[User]:
        stmt = select(User)
        result = await self.session.execute(stmt)
        return result.scalars().all()
