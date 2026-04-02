from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram import Bot
    from bot.config import Config

from bot.repositories import TaskRepository, RewardRepository


class NotificationService:
    def __init__(self, bot: 'Bot', config: 'Config'):
        self.bot = bot
        self.config = config
    
    async def notify_admin(self, message: str):
        await self.bot.send_message(
            chat_id=self.config.telegram.admin_id,
            text=message
        )
    
    async def notify_user(self, user_id: int, message: str):
        await self.bot.send_message(
            chat_id=user_id,
            text=message
        )
    
    async def notify_new_task(self, task_id: int):
        await self.notify_admin(f"📋 Новая задача на утверждении #{task_id}")
    
    async def notify_task_approved(self, user_id: int, points: int):
        await self.notify_user(
            user_id,
            f"✅ Задача подтверждена! Начислено {points} баллов"
        )
    
    async def notify_task_completed(self, completion_id: int):
        await self.notify_admin(f"✅ Задача выполнена #{completion_id}")
    
    async def notify_completion_approved(self, user_id: int, points: int):
        await self.notify_user(
            user_id,
            f"🎉 Выполнение подтверждено! Получено {points} баллов"
        )
    
    async def notify_completion_rejected(self, user_id: int):
        await self.notify_user(
            user_id,
            "❌ Выполнение отклонено"
        )
    
    async def notify_reward_suggested(self, reward_id: int):
        await self.notify_admin(f"🎁 Предложена награда #{reward_id}")
    
    async def notify_reward_approved(self, user_id: int):
        await self.notify_user(
            user_id,
            "✅ Ваша награда утверждена!"
        )
    
    async def notify_reward_requested(self, request_id: int):
        await self.notify_admin(f"🎁 Запрос на награду #{request_id}")
    
    async def notify_reward_request_approved(self, user_id: int, reward_title: str):
        await self.notify_user(
            user_id,
            f"🎉 Награда '{reward_title}' подтверждена!"
        )
    
    async def send_daily_reminder(self, user_id: int):
        await self.notify_user(
            user_id,
            "📅 Не забудьте выполнить ежедневные задачи!"
        )
    
    async def send_daily_task_reminder(self, user_id: int, tasks: list):
        if tasks:
            task_list = "\n".join([f"• {task.title}" for task in tasks])
            await self.notify_user(
                user_id,
                f"📋 Ежедневные задачи на сегодня:\n{task_list}"
            )
