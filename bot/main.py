import asyncio
import logging
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import Config, load_config
from bot.database import init_db
from bot.handlers import register_handlers
from bot.services import NotificationService
from bot.services.scheduler import setup_scheduler


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    config: Config = load_config()
    
    bot = Bot(token=config.telegram.token)
    dp = Dispatcher()
    
    await init_db(config.database)
    
    register_handlers(dp)
    
    scheduler = AsyncIOScheduler()
    setup_scheduler(scheduler, bot, config)
    scheduler.start()
    
    notification_service = NotificationService(bot, config)
    
    try:
        await dp.start_polling(bot)
    finally:
        with suppress(TelegramAPIError):
            await bot.session.close()
        scheduler.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
