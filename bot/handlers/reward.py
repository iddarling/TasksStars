from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from bot.database import init_db, get_session
from bot.config import load_config
from bot.services import RewardService, UserService
from bot.keyboards.user import get_rewards_keyboard
from bot.keyboards.reward import get_reward_actions_keyboard, get_pending_rewards_keyboard


class SuggestRewardState(StatesGroup):
    title = State()
    description = State()


def register_reward_handlers(dp):
    router = Router()
    
    @router.message(Command('rewards'))
    async def cmd_rewards(message: Message):
        config = load_config()
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.services.notification import NotificationService
            notification_service = NotificationService(message.bot, config)
            reward_service = RewardService(session, notification_service)
            user_service = UserService(session)
            
            rewards = await reward_service.get_active_rewards()
            balance = await user_service.get_user_balance(message.from_user.id)
            
            if not rewards:
                await message.answer("🎁 Активных наград пока нет")
                return
            
            text = f"🎁 Доступные награды (ваш баланс: {balance} баллов):\n\n"
            for reward in rewards:
                text += f"• {reward.title} - {reward.cost} баллов\n"
                if reward.description:
                    text += f"  {reward.description}\n"
                text += "\n"
            
            await message.answer(text, reply_markup=get_rewards_keyboard())
    
    @router.message(Command('suggest_reward'))
    async def cmd_suggest_reward(message: Message, state: FSMContext):
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await message.answer(
            "🎁 Введите название награды:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]
            ])
        )
        await state.set_state(SuggestRewardState.title)
    
    @router.message(SuggestRewardState.title)
    async def process_reward_title(message: Message, state: FSMContext):
        await state.update_data(title=message.text)
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await message.answer(
            "🎁 Введите описание награды:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]
            ])
        )
        await state.set_state(SuggestRewardState.description)
    
    @router.message(SuggestRewardState.description)
    async def process_reward_description(message: Message, state: FSMContext):
        data = await state.get_data()
        description = message.text
        
        config = load_config()
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.services.notification import NotificationService
            notification_service = NotificationService(message.bot, config)
            reward_service = RewardService(session, notification_service)
            
            reward_id = await reward_service.suggest_reward(
                title=data['title'],
                description=description,
                user_id=message.from_user.id
            )
            
            from bot.keyboards.user import get_main_keyboard
            config = load_config()
            is_admin = message.from_user.id == config.telegram.admin_id
            await message.answer(
                f"✅ Награда предложена! ID: {reward_id}",
                reply_markup=get_main_keyboard(is_admin)
            )
        
        await state.clear()
    
    @router.callback_query(F.data.startswith('redeem_reward:'))
    async def redeem_reward(callback: CallbackQuery):
        reward_id = int(callback.data.split(':')[1])
        
        config = load_config()
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.services.notification import NotificationService
            notification_service = NotificationService(callback.bot, config)
            reward_service = RewardService(session, notification_service)
            user_service = UserService(session)
            
            balance = await user_service.get_user_balance(callback.from_user.id)
            
            success = await reward_service.redeem_reward(reward_id, callback.from_user.id)
            
            if success:
                from bot.keyboards.user import get_main_keyboard
                is_admin = callback.from_user.id == config.telegram.admin_id
                await callback.answer()
                await callback.message.edit_text(
                    "✅ Запрос на награду отправлен!",
                    reply_markup=get_main_keyboard(is_admin)
                )
            else:
                await callback.answer("❌ Недостаточно баллов или награда недоступна", show_alert=True)
    
    @router.message(Command('pending_rewards'))
    async def cmd_pending_rewards(message: Message):
        config = load_config()
        if message.from_user.id != config.telegram.admin_id:
            return
        
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.services.notification import NotificationService
            notification_service = NotificationService(message.bot, config)
            reward_service = RewardService(session, notification_service)
            
            rewards = await reward_service.get_pending_rewards()
            
            if not rewards:
                from bot.keyboards.user import get_main_keyboard
                await message.answer(
                    "🎁 Наград на утверждении нет",
                    reply_markup=get_main_keyboard(True)
                )
                return
            
            await message.answer(
                "🎁 Награды на утверждении:",
                reply_markup=get_pending_rewards_keyboard(rewards)
            )
    
    dp.include_router(router)
