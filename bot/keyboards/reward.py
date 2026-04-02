from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_reward_actions_keyboard(rewards) -> InlineKeyboardMarkup:
    buttons = []
    for reward in rewards:
        buttons.append([
            InlineKeyboardButton(
                text=f"🎁 {reward.title} ({reward.cost} баллов)",
                callback_data=f"redeem_reward:{reward.id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_pending_rewards_keyboard(rewards) -> InlineKeyboardMarkup:
    buttons = []
    for reward in rewards:
        buttons.append([
            InlineKeyboardButton(
                text=f"✅ {reward.title} (10 баллов)",
                callback_data=f"approve_reward:{reward.id}:10"
            ),
            InlineKeyboardButton(
                text=f"✅ {reward.title} (20 баллов)",
                callback_data=f"approve_reward:{reward.id}:20"
            ),
            InlineKeyboardButton(
                text=f"✅ {reward.title} (30 баллов)",
                callback_data=f"approve_reward:{reward.id}:30"
            ),
        ])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_pending_reward_requests_keyboard(requests) -> InlineKeyboardMarkup:
    buttons = []
    for request in requests:
        buttons.append([
            InlineKeyboardButton(
                text=f"✅ Подтвердить #{request.id}",
                callback_data=f"approve_reward_request:{request.id}"
            ),
        ])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
