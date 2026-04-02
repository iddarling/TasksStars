from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.services import TaskService, UserService


async def daily_reminder_job(bot, config):
    from bot.database import init_db, get_session
    from bot.repositories import UserRepository
    
    engine = await init_db(config.database)
    session_factory = get_session(engine)
    
    async with session_factory() as session:
        user_service = UserService(session)
        notification_service = NotificationService(bot, config)
        
        users = await UserRepository(session).get_all_users()
        for user in users:
            await notification_service.send_daily_reminder(user.telegram_id)


async def daily_task_reminder_job(bot, config):
    from bot.database import get_session
    from bot.repositories import UserRepository
    
    engine = await init_db(config.database)
    session_factory = get_session(engine)
    
    async with session_factory() as session:
        task_service = TaskService(session, NotificationService(bot, config))
        notification_service = NotificationService(bot, config)
        
        users = await UserRepository(session).get_all_users()
        for user in users:
            if user.role == 'user':
                tasks = await task_service.get_daily_tasks_not_completed_today(user.telegram_id)
                await notification_service.send_daily_task_reminder(user.telegram_id, tasks)


def setup_scheduler(scheduler: AsyncIOScheduler, bot, config):
    hour, minute = map(int, config.notifications.daily_reminder_time.split(':'))
    
    scheduler.add_job(
        daily_reminder_job,
        CronTrigger(hour=hour, minute=minute),
        args=[bot, config],
        id='daily_reminder',
        replace_existing=True
    )
    
    scheduler.add_job(
        daily_task_reminder_job,
        CronTrigger(hour=hour+1, minute=minute),
        args=[bot, config],
        id='daily_task_reminder',
        replace_existing=True
    )
