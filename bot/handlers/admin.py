from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.database import init_db, get_session
from bot.config import load_config
from bot.services import TaskService, RewardService
from bot.keyboards.admin import get_admin_keyboard


class AddPointsState(StatesGroup):
    user_id = State()
    amount = State()


class EditTaskPointsState(StatesGroup):
    task_id = State()
    new_points = State()


def register_admin_handlers(dp):
    router = Router()
    
    @router.message(Command('admin'))
    async def cmd_admin(message: Message):
        config = load_config()
        if message.from_user.id != config.telegram.admin_id:
            await message.answer("❌ Доступ запрещен")
            return
        
        await message.answer("⚙️ Панель администратора", reply_markup=get_admin_keyboard())
    
    @router.message(Command('add_points'))
    async def cmd_add_points(message: Message, state: FSMContext):
        config = load_config()
        if message.from_user.id != config.telegram.admin_id:
            from bot.keyboards.user import get_main_keyboard
            await message.answer(
                "❌ Доступ запрещен",
                reply_markup=get_main_keyboard(
                    message.from_user.id == config.telegram.admin_id
                )
            )
            return
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await message.answer(
            "📝 Введите ID пользователя (telegram_id):",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]
            ])
        )
        await state.set_state(AddPointsState.user_id)
    
    @router.message(AddPointsState.user_id)
    async def process_points_user(message: Message, state: FSMContext):
        try:
            user_id = int(message.text)
            await state.update_data(user_id=user_id)
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            await message.answer(
                "📝 Введите количество баллов (положительное - начислить, отрицательное - списать):",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]
                ])
            )
            await state.set_state(AddPointsState.amount)
            await state.set_state(AddPointsState.amount)
        except ValueError:
            await message.answer("❌ Неверный формат ID. Введите число:")
    
    @router.message(AddPointsState.amount)
    async def process_points_amount(message: Message, state: FSMContext):
        config = load_config()
        data = await state.get_data()
        
        try:
            amount = int(message.text)
            user_id = data['user_id']
            
            engine = await init_db(config.database)
            session_factory = get_session(engine)
            
            async with session_factory() as session:
                from bot.repositories import PointsRepository
                points_repo = PointsRepository(session)
                
                await points_repo.add_points(user_id, amount, f'admin_adjustment')
                
                action = "начислено" if amount > 0 else "списано"
                await message.answer(f"✅ {action} {abs(amount)} баллов пользователю {user_id}")
        except ValueError:
            await message.answer("❌ Неверный формат баллов. Введите число:")
        
        await state.clear()
    
    @router.message(Command('edit_task_points'))
    async def cmd_edit_task_points(message: Message, state: FSMContext):
        config = load_config()
        if message.from_user.id != config.telegram.admin_id:
            await message.answer("❌ Доступ запрещен")
            return
        
        await message.answer("📝 Введите ID задачи:")
        await state.set_state(EditTaskPointsState.task_id)
    
    @router.message(EditTaskPointsState.task_id)
    async def process_edit_task_id(message: Message, state: FSMContext):
        try:
            task_id = int(message.text)
            await state.update_data(task_id=task_id)
            await message.answer("📝 Введите новое количество баллов за задачу:")
            await state.set_state(EditTaskPointsState.new_points)
        except ValueError:
            await message.answer("❌ Неверный формат ID. Введите число:")
    
    @router.message(EditTaskPointsState.new_points)
    async def process_edit_task_points(message: Message, state: FSMContext):
        config = load_config()
        data = await state.get_data()
        
        try:
            new_points = int(message.text)
            task_id = data['task_id']
            
            engine = await init_db(config.database)
            session_factory = get_session(engine)
            
            async with session_factory() as session:
                from bot.repositories import TaskRepository
                task_repo = TaskRepository(session)
                
                task = await task_repo.get_task(task_id)
                if task:
                    await task_repo.update_task_status(task_id, task.status, new_points)
                    from bot.keyboards.user import get_main_keyboard
                    await message.answer(
                        f"✅ Баллы задачи #{task_id} изменены на {new_points}",
                        reply_markup=get_main_keyboard(True)
                    )
                else:
                    from bot.keyboards.user import get_main_keyboard
                    await message.answer(
                        f"❌ Задача #{task_id} не найдена",
                        reply_markup=get_main_keyboard(True)
                    )
        except ValueError:
            await message.answer("❌ Неверный формат баллов. Введите число:")
        
        await state.clear()
    
    @router.callback_query(F.data == 'admin')
    async def cb_admin(callback: CallbackQuery):
        config = load_config()
        if callback.from_user.id != config.telegram.admin_id:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        await callback.answer()
        await callback.message.edit_text(
            "⚙️ Панель администратора",
            reply_markup=get_admin_keyboard()
        )
    
    @router.callback_query(F.data == 'pending_tasks')
    async def cb_pending_tasks(callback: CallbackQuery):
        config = load_config()
        if callback.from_user.id != config.telegram.admin_id:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.services.notification import NotificationService
            notification_service = NotificationService(callback.bot, config)
            task_service = TaskService(session, notification_service)
            
            tasks = await task_service.get_pending_tasks()
            
            if not tasks:
                await callback.answer()
                await callback.message.edit_text(
                    "📋 Задач на утверждении нет",
                    reply_markup=get_admin_keyboard()
                )
                return
            
            from bot.keyboards.task import get_pending_tasks_keyboard
            await callback.answer()
            await callback.message.edit_text(
                "📋 Задачи на утверждении:",
                reply_markup=get_pending_tasks_keyboard(tasks)
            )
    
    @router.callback_query(F.data == 'pending_rewards')
    async def cb_pending_rewards(callback: CallbackQuery):
        config = load_config()
        if callback.from_user.id != config.telegram.admin_id:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.services.notification import NotificationService
            notification_service = NotificationService(callback.bot, config)
            from bot.services import RewardService
            reward_service = RewardService(session, notification_service)
            
            rewards = await reward_service.get_pending_rewards()
            
            if not rewards:
                await callback.answer()
                await callback.message.edit_text(
                    "🎁 Наград на утверждении нет",
                    reply_markup=get_admin_keyboard()
                )
                return
            
            from bot.keyboards.reward import get_pending_rewards_keyboard
            await callback.answer()
            await callback.message.edit_text(
                "🎁 Награды на утверждении:",
                reply_markup=get_pending_rewards_keyboard(rewards)
            )
    
    @router.callback_query(F.data.startswith('approve_task:'))
    async def approve_task(callback: CallbackQuery):
        config = load_config()
        if callback.from_user.id != config.telegram.admin_id:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        task_id = int(callback.data.split(':')[1])
        points = int(callback.data.split(':')[2])
        
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.services.notification import NotificationService
            notification_service = NotificationService(callback.bot, config)
            task_service = TaskService(session, notification_service)
            
            await task_service.approve_task(task_id, points)
            from bot.keyboards.admin import get_admin_keyboard
            await callback.answer()
            await callback.message.edit_text(
                f"✅ Задача #{task_id} утверждена с {points} баллами",
                reply_markup=get_admin_keyboard()
            )
    
    @router.callback_query(F.data.startswith('approve_completion:'))
    async def approve_completion(callback: CallbackQuery):
        config = load_config()
        if callback.from_user.id != config.telegram.admin_id:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        completion_id = int(callback.data.split(':')[1])
        
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.services.notification import NotificationService
            notification_service = NotificationService(callback.bot, config)
            task_service = TaskService(session, notification_service)
            
            await task_service.approve_completion(completion_id)
            from bot.keyboards.admin import get_admin_keyboard
            await callback.answer()
            await callback.message.edit_text(
                f"✅ Выполнение #{completion_id} подтверждено",
                reply_markup=get_admin_keyboard()
            )
    
    @router.callback_query(F.data.startswith('reject_completion:'))
    async def reject_completion(callback: CallbackQuery):
        config = load_config()
        if callback.from_user.id != config.telegram.admin_id:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        completion_id = int(callback.data.split(':')[1])
        
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.services.notification import NotificationService
            notification_service = NotificationService(callback.bot, config)
            task_service = TaskService(session, notification_service)
            
            await task_service.reject_completion(completion_id)
            from bot.keyboards.admin import get_admin_keyboard
            await callback.answer()
            await callback.message.edit_text(
                f"❌ Выполнение #{completion_id} отклонено",
                reply_markup=get_admin_keyboard()
            )
    
    @router.callback_query(F.data.startswith('approve_reward:'))
    async def approve_reward(callback: CallbackQuery):
        config = load_config()
        if callback.from_user.id != config.telegram.admin_id:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        reward_id = int(callback.data.split(':')[1])
        cost = int(callback.data.split(':')[2])
        
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.services.notification import NotificationService
            notification_service = NotificationService(callback.bot, config)
            reward_service = RewardService(session, notification_service)
            
            await reward_service.approve_reward(reward_id, cost)
            from bot.keyboards.admin import get_admin_keyboard
            await callback.answer()
            await callback.message.edit_text(
                f"✅ Награда #{reward_id} утверждена со стоимостью {cost} баллов",
                reply_markup=get_admin_keyboard()
            )
    
    @router.callback_query(F.data.startswith('approve_reward_request:'))
    async def approve_reward_request(callback: CallbackQuery):
        config = load_config()
        if callback.from_user.id != config.telegram.admin_id:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        request_id = int(callback.data.split(':')[1])
        
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.services.notification import NotificationService
            notification_service = NotificationService(callback.bot, config)
            reward_service = RewardService(session, notification_service)
            
            await reward_service.approve_reward_request(request_id)
            from bot.keyboards.admin import get_admin_keyboard
            await callback.answer()
            await callback.message.edit_text(
                f"✅ Запрос на награду #{request_id} подтвержден",
                reply_markup=get_admin_keyboard()
            )
    
    @router.callback_query(F.data == 'add_points')
    async def cb_add_points(callback: CallbackQuery, state: FSMContext):
        config = load_config()
        if callback.from_user.id != config.telegram.admin_id:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        await callback.answer()
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await callback.message.edit_text(
            "📝 Введите ID пользователя (telegram_id):",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]
            ])
        )
        await state.set_state(AddPointsState.user_id)
    
    @router.callback_query(F.data == 'edit_task_points')
    async def cb_edit_task_points(callback: CallbackQuery, state: FSMContext):
        config = load_config()
        if callback.from_user.id != config.telegram.admin_id:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        await callback.answer()
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await callback.message.edit_text(
            "📝 Введите ID задачи:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]
            ])
        )
        await state.set_state(EditTaskPointsState.task_id)
    
    @router.callback_query(F.data == 'list_users')
    async def cb_list_users(callback: CallbackQuery):
        config = load_config()
        if callback.from_user.id != config.telegram.admin_id:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.repositories import UserRepository, PointsRepository
            user_repo = UserRepository(session)
            points_repo = PointsRepository(session)
            
            users = await user_repo.get_all_users()
            
            # Создаем список пользователей с балансом
            users_with_balance = []
            for user in users:
                balance = await points_repo.get_user_balance(user.telegram_id)
                users_with_balance.append((user, balance))
            
            # Сортируем по балансу (по убыванию)
            users_with_balance.sort(key=lambda x: x[1], reverse=True)
            
            if not users_with_balance:
                await callback.answer()
                await callback.message.edit_text(
                    "👥 Пользователей пока нет",
                    reply_markup=get_admin_keyboard()
                )
                return
            
            text = "👥 Пользователи (отсортированы по баллам):\n\n"
            for i, (user, balance) in enumerate(users_with_balance, 1):
                role_emoji = "👑" if user.role == 'admin' else "👤"
                # Формируем имя пользователя
                display_name = user.first_name or ""
                if user.last_name:
                    display_name += f" {user.last_name}"
                if user.username:
                    display_name += f" (@{user.username})"
                if not display_name:
                    display_name = f"Пользователь {user.telegram_id}"
                
                text += f"{i}. {role_emoji} {display_name}\n"
                text += f"   🆔 ID: {user.telegram_id}\n"
                text += f"   💰 Баланс: {balance} баллов\n"
                text += f"   🎭 Роль: {user.role}\n\n"
            
            await callback.answer()
            await callback.message.edit_text(
                text,
                reply_markup=get_admin_keyboard()
            )
    
    dp.include_router(router)
