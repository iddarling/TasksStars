from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from bot.database import init_db, get_session
from bot.config import load_config
from bot.services import UserService
from bot.keyboards.user import get_main_keyboard, get_tasks_keyboard, get_rewards_keyboard


class AdminActionState(StatesGroup):
    action = State()  # 'tasks', 'completed', 'force_close'
    target_user = State()


def register_user_handlers(dp):
    router = Router()
    
    @router.message(Command('start'))
    async def cmd_start(message: Message):
        config = load_config()
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            user_service = UserService(session)
            is_admin = message.from_user.id == config.telegram.admin_id
            
            # Получаем имя пользователя
            first_name = message.from_user.first_name
            last_name = message.from_user.last_name
            username = message.from_user.username
            
            user, balance = await user_service.get_or_create_user(
                message.from_user.id,
                is_admin,
                first_name,
                last_name,
                username
            )
            
            # Формируем приветствие с именем
            display_name = first_name or username or "Пользователь"
            welcome_text = (
                f"👋 Привет, {display_name}!\n\n"
                f"Добро пожаловать в TaskStars!\n"
                f"💰 Ваш баланс: {balance} баллов\n"
                f"🎭 Роль: {user.role}"
            )
            
            await message.answer(
                welcome_text,
                reply_markup=get_main_keyboard(is_admin)
            )
    
    @router.message(Command('balance'))
    async def cmd_balance(message: Message):
        config = load_config()
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            user_service = UserService(session)
            balance = await user_service.get_user_balance(message.from_user.id)
            
            is_admin = message.from_user.id == config.telegram.admin_id
            await message.answer(
                f"💰 Ваш баланс: {balance} баллов",
                reply_markup=get_main_keyboard(is_admin)
            )
    
    @router.callback_query(F.data == 'main_menu')
    async def cb_main_menu(callback: CallbackQuery):
        config = load_config()
        is_admin = callback.from_user.id == config.telegram.admin_id
        
        await callback.answer()
        try:
            await callback.message.edit_text(
                "🏠 Главное меню",
                reply_markup=get_main_keyboard(is_admin)
            )
        except Exception:
            await callback.message.delete()
            await callback.message.answer(
                "🏠 Главное меню",
                reply_markup=get_main_keyboard(is_admin)
            )
    
    @router.callback_query(F.data == 'balance')
    async def cb_balance(callback: CallbackQuery):
        config = load_config()
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            user_service = UserService(session)
            balance = await user_service.get_user_balance(callback.from_user.id)
            
            text = f"💰 Ваш баланс: {balance} баллов"
            await callback.answer(text)
            try:
                await callback.message.edit_text(
                    text,
                    reply_markup=get_main_keyboard(callback.from_user.id == config.telegram.admin_id)
                )
            except Exception:
                pass
    
    @router.callback_query(F.data == 'tasks')
    async def cb_tasks(callback: CallbackQuery):
        from bot.services import TaskService
        from bot.services.notification import NotificationService
        from bot.keyboards.task import get_task_actions_keyboard
        
        config = load_config()
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        is_admin = callback.from_user.id == config.telegram.admin_id
        
        async with session_factory() as session:
            notification_service = NotificationService(callback.bot, config)
            task_service = TaskService(session, notification_service)
            
            # Для обычного пользователя - только свои невыполненные задачи, для админа - все
            if is_admin:
                tasks = await task_service.get_active_tasks()
            else:
                tasks = await task_service.get_active_tasks(callback.from_user.id)
            
            if not tasks:
                await callback.answer()
                await callback.message.edit_text(
                    "📋 Активных задач пока нет",
                    reply_markup=get_tasks_keyboard()
                )
                return
            
            text = "📋 Активные задачи:\n\n"
            for task in tasks:
                text += f"• {task.title} ({task.points} баллов)\n"
                if task.description:
                    text += f"  {task.description}\n"
                text += f"  Тип: {task.type}\n\n"
            
            await callback.answer()
            try:
                await callback.message.edit_text(text, reply_markup=get_tasks_keyboard())
            except Exception:
                pass
    
    @router.callback_query(F.data == 'rewards')
    async def cb_rewards(callback: CallbackQuery):
        from bot.services import RewardService
        from bot.services.notification import NotificationService
        from bot.keyboards.reward import get_reward_actions_keyboard
        
        config = load_config()
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            notification_service = NotificationService(callback.bot, config)
            reward_service = RewardService(session, notification_service)
            user_service = UserService(session)
            
            rewards = await reward_service.get_active_rewards()
            balance = await user_service.get_user_balance(callback.from_user.id)
            
            if not rewards:
                await callback.answer()
                await callback.message.edit_text(
                    "🎁 Активных наград пока нет",
                    reply_markup=get_rewards_keyboard()
                )
                return
            
            text = f"🎁 Доступные награды (баланс: {balance} баллов):\n\n"
            for reward in rewards:
                text += f"• {reward.title} - {reward.cost} баллов\n"
                if reward.description:
                    text += f"  {reward.description}\n"
                text += "\n"
            
            await callback.answer()
            try:
                await callback.message.edit_text(
                    text,
                    reply_markup=get_reward_actions_keyboard(rewards)
                )
            except Exception:
                pass
    
    @router.callback_query(F.data == 'add_task')
    async def cb_add_task(callback: CallbackQuery, state: FSMContext):
        from bot.handlers.task import CreateTaskState
        from bot.keyboards.task import get_user_selection_keyboard
        from bot.repositories import UserRepository
        
        config = load_config()
        is_admin = callback.from_user.id == config.telegram.admin_id
        
        if is_admin:
            # Для админа - показываем список пользователей
            engine = await init_db(config.database)
            session_factory = get_session(engine)
            
            async with session_factory() as session:
                user_repo = UserRepository(session)
                users = await user_repo.get_all_users()
                
                # Фильтруем - убираем самого админа из списка
                users = [u for u in users if u.telegram_id != config.telegram.admin_id]
                
                if not users:
                    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                    await callback.answer()
                    await callback.message.edit_text(
                        "❌ Нет пользователей для создания задач",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                        ])
                    )
                    return
                
                await callback.answer()
                await callback.message.edit_text(
                    "� Выберите пользователя для создания задачи:",
                    reply_markup=get_user_selection_keyboard(users)
                )
                await state.set_state(CreateTaskState.target_user)
        else:
            # Для обычного пользователя - создаем задачу для себя
            await state.update_data(target_user_id=callback.from_user.id)
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            await callback.answer()
            await callback.message.edit_text(
                "📝 Введите название задачи:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]
                ])
            )
            await state.set_state(CreateTaskState.title)
    
    @router.callback_query(F.data == 'done')
    async def cb_done(callback: CallbackQuery):
        from bot.services import TaskService
        from bot.services.notification import NotificationService
        from bot.keyboards.task import get_task_actions_keyboard
        
        config = load_config()
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        is_admin = callback.from_user.id == config.telegram.admin_id
        
        async with session_factory() as session:
            notification_service = NotificationService(callback.bot, config)
            task_service = TaskService(session, notification_service)
            
            # Для обычного пользователя - только свои невыполненные задачи для выполнения
            if is_admin:
                tasks = await task_service.get_active_tasks()
            else:
                tasks = await task_service.get_active_tasks(callback.from_user.id)
            
            if not tasks:
                await callback.answer()
                await callback.message.edit_text(
                    "📋 Активных задач пока нет",
                    reply_markup=get_main_keyboard(is_admin)
                )
                return
            
            text = "Выберите задачу для выполнения:\n\n"
            for task in tasks:
                text += f"• {task.title} ({task.points} баллов)\n"
            
            await callback.answer()
            try:
                await callback.message.edit_text(text, reply_markup=get_task_actions_keyboard(tasks))
            except Exception:
                pass
    
    @router.callback_query(F.data == 'completed_tasks')
    async def cb_completed_tasks(callback: CallbackQuery):
        config = load_config()
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.services import TaskService
            task_service = TaskService(session, None)
            completed = await task_service.get_completed_tasks(callback.from_user.id)
            
            if not completed:
                await callback.answer()
                await callback.message.edit_text(
                    "📋 У вас пока нет выполненных задач",
                    reply_markup=get_main_keyboard(callback.from_user.id == config.telegram.admin_id)
                )
                return
            
            total_points = sum(item['points'] for item in completed)
            
            text = f"✅ Выполненные задачи ({len(completed)} шт., всего {total_points} баллов):\n\n"
            for i, item in enumerate(completed[:20], 1):
                task = item['task']
                points = item['points']
                text += f"{i}. {task.title}"
                if points > 0:
                    text += f" (+{points} баллов)"
                text += "\n"
            
            if len(completed) > 20:
                text += f"\n... и еще {len(completed) - 20} задач"
            
            await callback.answer()
            await callback.message.edit_text(
                text,
                reply_markup=get_main_keyboard(callback.from_user.id == config.telegram.admin_id)
            )
    
    @router.callback_query(F.data == 'admin_tasks')
    async def cb_admin_tasks(callback: CallbackQuery, state: FSMContext):
        """Админ: выбор пользователя для просмотра задач"""
        config = load_config()
        if callback.from_user.id != config.telegram.admin_id:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.repositories import UserRepository
            user_repo = UserRepository(session)
            users = await user_repo.get_all_users()
            users = [u for u in users if u.telegram_id != config.telegram.admin_id]
            
            if not users:
                await callback.answer()
                await callback.message.edit_text("❌ Нет пользователей")
                return
            
            from bot.keyboards.task import get_user_selection_keyboard
            await callback.answer()
            await state.update_data(action='tasks')
            await callback.message.edit_text(
                "👤 Выберите пользователя для просмотра задач:",
                reply_markup=get_user_selection_keyboard(users)
            )
            await state.set_state(AdminActionState.target_user)
    
    @router.callback_query(F.data == 'admin_completed')
    async def cb_admin_completed(callback: CallbackQuery, state: FSMContext):
        """Админ: выбор пользователя для просмотра выполненных задач"""
        config = load_config()
        if callback.from_user.id != config.telegram.admin_id:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.repositories import UserRepository
            user_repo = UserRepository(session)
            users = await user_repo.get_all_users()
            users = [u for u in users if u.telegram_id != config.telegram.admin_id]
            
            if not users:
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                await callback.answer()
                await callback.message.edit_text(
                    "❌ Нет пользователей",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                    ])
                )
                return
            
            # Используем ту же клавиатуру, но callback будет другой
            from bot.keyboards.task import get_user_selection_keyboard
            await callback.answer()
            await state.update_data(action='completed')
            await callback.message.edit_text(
                "👤 Выберите пользователя для просмотра выполненных задач:",
                reply_markup=get_user_selection_keyboard(users)
            )
            await state.set_state(AdminActionState.target_user)
    
    @router.callback_query(F.data == 'admin_force_close')
    async def cb_admin_force_close(callback: CallbackQuery, state: FSMContext):
        """Админ: выбор пользователя для досрочного закрытия"""
        config = load_config()
        if callback.from_user.id != config.telegram.admin_id:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.repositories import UserRepository
            user_repo = UserRepository(session)
            users = await user_repo.get_all_users()
            users = [u for u in users if u.telegram_id != config.telegram.admin_id]
            
            if not users:
                await callback.answer()
                await callback.message.edit_text("❌ Нет пользователей")
                return
            
            from bot.keyboards.task import get_user_selection_keyboard
            await callback.answer()
            await state.update_data(action='force_close')
            await callback.message.edit_text(
                "👤 Выберите пользователя для досрочного закрытия задач:",
                reply_markup=get_user_selection_keyboard(users)
            )
            await state.set_state(AdminActionState.target_user)
    
    @router.callback_query(F.data.startswith('task_user:'), AdminActionState.target_user)
    async def process_admin_user_selection(callback: CallbackQuery, state: FSMContext):
        """Обработка выбора пользователя админом для разных действий"""
        target_user_id = int(callback.data.split(':')[1])
        data = await state.get_data()
        action = data.get('action')
        
        config = load_config()
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.services import TaskService
            from bot.repositories import UserRepository
            
            user_repo = UserRepository(session)
            target_user = await user_repo.get_by_telegram_id(target_user_id)
            
            if not target_user:
                await callback.answer("❌ Пользователь не найден")
                await state.clear()
                return
            
            # Получаем имя пользователя для отображения
            user_name = target_user.first_name or ""
            if target_user.last_name:
                user_name += f" {target_user.last_name}"
            if target_user.username:
                user_name += f" (@{target_user.username})"
            if not user_name:
                user_name = f"ID: {target_user_id}"
            
            task_service = TaskService(session, None)
            
            if action == 'tasks':
                # Показываем активные задачи пользователя
                tasks = await task_service.get_user_active_tasks(target_user_id)
                
                if not tasks:
                    await callback.answer()
                    await callback.message.edit_text(
                        f"📋 У пользователя {user_name} нет активных задач",
                        reply_markup=get_main_keyboard(True)
                    )
                    await state.clear()
                    return
                
                text = f"📋 Задачи пользователя {user_name}:\n\n"
                for task in tasks:
                    text += f"• {task.title} ({task.points} баллов)\n"
                    if task.description:
                        text += f"  {task.description}\n"
                    text += f"  Тип: {task.type}\n\n"
                
                await callback.answer()
                await callback.message.edit_text(
                    text,
                    reply_markup=get_main_keyboard(True)
                )
                
            elif action == 'completed':
                # Показываем выполненные задачи пользователя
                completed = await task_service.get_completed_tasks(target_user_id)
                
                if not completed:
                    await callback.answer()
                    await callback.message.edit_text(
                        f"📋 У пользователя {user_name} нет выполненных задач",
                        reply_markup=get_main_keyboard(True)
                    )
                    await state.clear()
                    return
                
                total_points = sum(item['points'] for item in completed)
                
                text = f"✅ Выполненные задачи {user_name} ({len(completed)} шт., {total_points} баллов):\n\n"
                for i, item in enumerate(completed[:20], 1):
                    task = item['task']
                    points = item['points']
                    text += f"{i}. {task.title}"
                    if points > 0:
                        text += f" (+{points} баллов)"
                    text += "\n"
                
                if len(completed) > 20:
                    text += f"\n... и еще {len(completed) - 20} задач"
                
                await callback.answer()
                await callback.message.edit_text(
                    text,
                    reply_markup=get_main_keyboard(True)
                )
                
            elif action == 'force_close':
                # Показываем активные задачи для досрочного закрытия
                tasks = await task_service.get_user_active_tasks(target_user_id)
                
                if not tasks:
                    await callback.answer()
                    await callback.message.edit_text(
                        f"📋 У пользователя {user_name} нет активных задач для закрытия",
                        reply_markup=get_main_keyboard(True)
                    )
                    await state.clear()
                    return
                
                # Создаем клавиатуру с задачами для закрытия
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                buttons = []
                for task in tasks:
                    buttons.append([
                        InlineKeyboardButton(
                            text=f"🚫 {task.title} ({task.points} баллов)",
                            callback_data=f"force_close_task:{task.id}:{target_user_id}"
                        )
                    ])
                buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
                
                await callback.answer()
                await callback.message.edit_text(
                    f"🚫 Выберите задачу для досрочного закрытия ({user_name}):",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                )
                return  # Не очищаем state, ждем выбора задачи
        
        await state.clear()
    
    @router.callback_query(F.data.startswith('force_close_task:'))
    async def process_force_close_task(callback: CallbackQuery, state: FSMContext):
        """Досрочное закрытие задачи админом"""
        config = load_config()
        if callback.from_user.id != config.telegram.admin_id:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        # Парсим callback_data: force_close_task:{task_id}:{target_user_id}
        parts = callback.data.split(':')
        task_id = int(parts[1])
        target_user_id = int(parts[2])
        
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.services import TaskService
            from bot.repositories import UserRepository
            
            user_repo = UserRepository(session)
            target_user = await user_repo.get_by_telegram_id(target_user_id)
            
            user_name = target_user.first_name or "" if target_user else f"ID: {target_user_id}"
            if target_user and target_user.last_name:
                user_name += f" {target_user.last_name}"
            
            task_service = TaskService(session, None)
            
            # Выполняем задачу для пользователя (без доказательства)
            completion_id, points_earned = await task_service.complete_task(
                task_id,
                target_user_id,
                proof="Досрочно закрыто администратором"
            )
            
            await callback.answer()
            if points_earned > 0:
                await callback.message.edit_text(
                    f"✅ Задача досрочно закрыта!\n👤 Пользователь: {user_name}\n🏆 Начислено: {points_earned} баллов",
                    reply_markup=get_main_keyboard(True)
                )
            else:
                await callback.message.edit_text(
                    f"✅ Задача досрочно закрыта!\n👤 Пользователь: {user_name}",
                    reply_markup=get_main_keyboard(True)
                )
        
        await state.clear()
    
    @router.callback_query(F.data == 'suggest_reward')
    async def cb_suggest_reward(callback: CallbackQuery, state: FSMContext):
        from bot.handlers.reward import SuggestRewardState
        
        await callback.answer()
        await callback.message.edit_text("🎁 Введите название награды:")
        await state.set_state(SuggestRewardState.title)
    
    dp.include_router(router)
