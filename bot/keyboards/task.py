from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_task_type_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="📅 Ежедневная", callback_data="task_type:daily"),
            InlineKeyboardButton(text="🎯 Разовая", callback_data="task_type:one-time"),
        ],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_task_actions_keyboard(tasks) -> InlineKeyboardMarkup:
    buttons = []
    for task in tasks:
        buttons.append([
            InlineKeyboardButton(
                text=f"✅ {task.title} ({task.points} баллов)",
                callback_data=f"complete_task:{task.id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_pending_tasks_keyboard(tasks) -> InlineKeyboardMarkup:
    buttons = []
    for task in tasks:
        buttons.append([
            InlineKeyboardButton(
                text=f"✅ {task.title} (10 баллов)",
                callback_data=f"approve_task:{task.id}:10"
            ),
            InlineKeyboardButton(
                text=f"✅ {task.title} (20 баллов)",
                callback_data=f"approve_task:{task.id}:20"
            ),
            InlineKeyboardButton(
                text=f"✅ {task.title} (30 баллов)",
                callback_data=f"approve_task:{task.id}:30"
            ),
        ])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_points_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="5 баллов", callback_data="task_points:5"),
            InlineKeyboardButton(text="10 баллов", callback_data="task_points:10"),
        ],
        [
            InlineKeyboardButton(text="15 баллов", callback_data="task_points:15"),
            InlineKeyboardButton(text="20 баллов", callback_data="task_points:20"),
        ],
        [
            InlineKeyboardButton(text="30 баллов", callback_data="task_points:30"),
            InlineKeyboardButton(text="50 баллов", callback_data="task_points:50"),
        ],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_user_selection_keyboard(users) -> InlineKeyboardMarkup:
    """Клавиатура для выбора пользователя (для админа)"""
    buttons = []
    for user in users:
        # Формируем имя пользователя
        display_name = user.first_name or ""
        if user.last_name:
            display_name += f" {user.last_name}"
        if user.username:
            display_name += f" (@{user.username})"
        if not display_name:
            display_name = f"ID: {user.telegram_id}"
        
        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {display_name}",
                callback_data=f"task_user:{user.telegram_id}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
