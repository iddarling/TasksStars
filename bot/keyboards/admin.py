from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📋 Задачи на утверждении", callback_data="pending_tasks")],
        [InlineKeyboardButton(text="🎁 Награды на утверждении", callback_data="pending_rewards")],
        [InlineKeyboardButton(text="💰 Начислить баллы", callback_data="add_points")],
        [InlineKeyboardButton(text="✏️ Изменить баллы задачи", callback_data="edit_task_points")],
        [InlineKeyboardButton(text="👥 Список пользователей", callback_data="list_users")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
