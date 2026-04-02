import os
from pathlib import Path
from typing import Final
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv(Path(__file__).parent.parent / '.env')


class TelegramConfig:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.admin_id = int(os.getenv('ADMIN_ID'))


class DatabaseConfig:
    def __init__(self):
        self.url = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///./bot.db')


class NotificationConfig:
    def __init__(self):
        self.daily_reminder_time = os.getenv('DAILY_REMINDER_TIME', '09:00')


class Config:
    def __init__(self):
        self.telegram = TelegramConfig()
        self.database = DatabaseConfig()
        self.notifications = NotificationConfig()


def load_config() -> Config:
    return Config()
