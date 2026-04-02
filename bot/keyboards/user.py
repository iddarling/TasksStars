from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    if is_admin:
        buttons = [
            [InlineKeyboardButton(text="📋 Задачи (выбор пользователя)", callback_data="admin_tasks")],
            [InlineKeyboardButton(text="✅ Выполненные (выбор пользователя)", callback_data="admin_completed")],
            [InlineKeyboardButton(text="🚫 Досрочное закрытие", callback_data="admin_force_close")],
            [InlineKeyboardButton(text="🎁 Награды", callback_data="rewards")],
            [InlineKeyboardButton(text="➕ Добавить задачу", callback_data="add_task")],
            [InlineKeyboardButton(text="🎁 Добавить награду", callback_data="suggest_reward")],
            [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
            [InlineKeyboardButton(text="⚙️ Админ панель", callback_data="admin")],
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="📋 Мои задачи", callback_data="tasks")],
            [InlineKeyboardButton(text="✅ Выполненные задачи", callback_data="completed_tasks")],
            [InlineKeyboardButton(text="🎁 Награды", callback_data="rewards")],
            [InlineKeyboardButton(text="➕ Добавить задачу", callback_data="add_task")],
            [InlineKeyboardButton(text="✅ Выполнить задачу", callback_data="done")],
            [InlineKeyboardButton(text="🎁 Предложить награду", callback_data="suggest_reward")],
            [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_tasks_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить задачу", callback_data="add_task")],
        [InlineKeyboardButton(text="✅ Выполнить задачу", callback_data="done")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_rewards_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🎁 Предложить награду", callback_data="suggest_reward")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
