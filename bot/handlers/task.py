from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from bot.database import init_db, get_session
from bot.config import load_config
from bot.services import TaskService
from bot.keyboards.user import get_tasks_keyboard, get_rewards_keyboard, get_main_keyboard
from bot.keyboards.task import get_task_type_keyboard, get_pending_tasks_keyboard, get_task_actions_keyboard


class CreateTaskState(StatesGroup):
    title = State()
    description = State()
    type = State()
    target_user = State()  # Для админа - выбор пользователя
    points = State()


def register_task_handlers(dp):
    router = Router()
    
    @router.message(Command('tasks'))
    async def cmd_tasks(message: Message):
        config = load_config()
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        is_admin = message.from_user.id == config.telegram.admin_id
        
        async with session_factory() as session:
            task_service = TaskService(session, None)
            
            # Для обычного пользователя - только свои невыполненные задачи, для админа - все
            if is_admin:
                tasks = await task_service.get_active_tasks()
            else:
                tasks = await task_service.get_active_tasks(message.from_user.id)
            
            if not tasks:
                await message.answer("📋 Активных задач пока нет")
                return
            
            text = "📋 Активные задачи:\n\n"
            for task in tasks:
                text += f"• {task.title} ({task.points} баллов)\n"
                if task.description:
                    text += f"  {task.description}\n"
                text += f"  Тип: {task.type}\n\n"
            
            await message.answer(text, reply_markup=get_tasks_keyboard())
    
    @router.message(Command('add_task'))
    async def cmd_add_task(message: Message, state: FSMContext):
        config = load_config()
        is_admin = message.from_user.id == config.telegram.admin_id
        
        if is_admin:
            # Для админа - показываем список пользователей
            engine = await init_db(config.database)
            session_factory = get_session(engine)
            
            async with session_factory() as session:
                from bot.repositories import UserRepository
                user_repo = UserRepository(session)
                users = await user_repo.get_all_users()
                
                # Фильтруем - убираем самого админа из списка
                users = [u for u in users if u.telegram_id != config.telegram.admin_id]
                
                if not users:
                    await message.answer("❌ Нет пользователей для создания задач")
                    return
                
                from bot.keyboards.task import get_user_selection_keyboard
                await message.answer(
                    "👤 Выберите пользователя для создания задачи:",
                    reply_markup=get_user_selection_keyboard(users)
                )
                await state.set_state(CreateTaskState.target_user)
        else:
            # Для обычного пользователя - создаем задачу для себя
            await state.update_data(target_user_id=message.from_user.id)
            await message.answer("📝 Введите название задачи:")
            await state.set_state(CreateTaskState.title)
    
    @router.callback_query(F.data.startswith('task_user:'), CreateTaskState.target_user)
    async def process_target_user(callback: CallbackQuery, state: FSMContext):
        target_user_id = int(callback.data.split(':')[1])
        await state.update_data(target_user_id=target_user_id)
        
        await callback.answer()
        await callback.message.edit_text("📝 Введите название задачи:")
        await state.set_state(CreateTaskState.title)
    
    @router.message(CreateTaskState.title)
    async def process_title(message: Message, state: FSMContext):
        await state.update_data(title=message.text)
        await message.answer("📝 Введите описание задачи:")
        await state.set_state(CreateTaskState.description)
    
    @router.message(CreateTaskState.description)
    async def process_description(message: Message, state: FSMContext):
        await state.update_data(description=message.text)
        await message.answer(
            "📝 Выберите тип задачи:",
            reply_markup=get_task_type_keyboard()
        )
        await state.set_state(CreateTaskState.type)
    
    @router.callback_query(F.data.startswith('task_type:'), CreateTaskState.type)
    async def process_type(callback: CallbackQuery, state: FSMContext):
        task_type = callback.data.split(':')[1]
        await state.update_data(task_type=task_type)
        
        config = load_config()
        is_admin = callback.from_user.id == config.telegram.admin_id
        
        if is_admin:
            # Для админа показываем выбор баллов
            from bot.keyboards.task import get_points_keyboard
            await callback.answer()
            await callback.message.edit_text(
                "📝 Выберите количество баллов за задачу:",
                reply_markup=get_points_keyboard()
            )
            await state.set_state(CreateTaskState.points)
        else:
            # Для обычного пользователя создаем задачу сразу
            data = await state.get_data()
            
            engine = await init_db(config.database)
            session_factory = get_session(engine)
            
            async with session_factory() as session:
                from bot.services.notification import NotificationService
                notification_service = NotificationService(callback.bot, config)
                task_service = TaskService(session, notification_service)
                
                # Для обычного пользователя создаем задачу сразу
                data = await state.get_data()
                target_user_id = data.get('target_user_id', callback.from_user.id)
                
                task_id = await task_service.create_task(
                    title=data['title'],
                    description=data['description'],
                    task_type=task_type,
                    created_by=target_user_id,
                    is_admin=False
                )
                
                from bot.keyboards.user import get_main_keyboard
                try:
                    await callback.message.edit_text(
                        f"✅ Задача создана! Статус: на утверждении",
                        reply_markup=get_main_keyboard(False)
                    )
                except Exception:
                    await callback.message.answer(
                        f"✅ Задача создана! Статус: на утверждении",
                        reply_markup=get_main_keyboard(False)
                    )
            
            await state.clear()
    
    @router.callback_query(F.data.startswith('task_points:'), CreateTaskState.points)
    async def process_points(callback: CallbackQuery, state: FSMContext):
        points = int(callback.data.split(':')[1])
        data = await state.get_data()
        
        config = load_config()
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.services.notification import NotificationService
            notification_service = NotificationService(callback.bot, config)
            task_service = TaskService(session, notification_service)
            
            # Получаем target_user_id - для кого создаем задачу
            target_user_id = data.get('target_user_id', callback.from_user.id)
            
            task_id = await task_service.create_task(
                title=data['title'],
                description=data['description'],
                task_type=data['task_type'],
                created_by=target_user_id,  # Задача принадлежит выбранному пользователю
                is_admin=True,
                points=points
            )
            
            from bot.keyboards.user import get_main_keyboard
            try:
                await callback.message.edit_text(
                    f"✅ Задача создана для пользователя {target_user_id}!\nСтатус: активна, Баллы: {points}",
                    reply_markup=get_main_keyboard(True)
                )
            except Exception:
                await callback.message.answer(
                    f"✅ Задача создана для пользователя {target_user_id}!\nСтатус: активна, Баллы: {points}",
                    reply_markup=get_main_keyboard(True)
                )
        
        await state.clear()
    
    @router.message(Command('done'))
    async def cmd_done(message: Message):
        config = load_config()
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            task_service = TaskService(session, None)
            is_admin = message.from_user.id == config.telegram.admin_id
            
            # Для обычного пользователя - только невыполненные задачи
            if is_admin:
                tasks = await task_service.get_active_tasks()
            else:
                tasks = await task_service.get_active_tasks(message.from_user.id)
            
            if not tasks:
                await message.answer("📋 Активных задач пока нет")
                return
            
            text = "Выберите задачу для выполнения:\n\n"
            for task in tasks:
                text += f"• {task.title} ({task.points} баллов)\n"
            
            await message.answer(text, reply_markup=get_task_actions_keyboard(tasks))
    
    @router.callback_query(F.data.startswith('complete_task:'))
    async def complete_task(callback: CallbackQuery, state: FSMContext):
        task_id = int(callback.data.split(':')[1])
        
        from bot.keyboards.user import get_main_keyboard
        config = load_config()
        is_admin = callback.from_user.id == config.telegram.admin_id
        
        await callback.answer()
        await callback.message.edit_text(
            "📸 Отправьте доказательство выполнения (текст или фото):",
            reply_markup=get_main_keyboard(is_admin)
        )
        await state.update_data(task_id=task_id)
        await state.set_state('awaiting_proof')
    
    @router.message(StateFilter('awaiting_proof'))
    async def process_proof(message: Message, state: FSMContext):
        data = await state.get_data()
        task_id = data['task_id']
        
        proof = message.text or message.caption
        
        config = load_config()
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            from bot.services.notification import NotificationService
            notification_service = NotificationService(message.bot, config)
            task_service = TaskService(session, notification_service)
            
            completion_id, points_earned = await task_service.complete_task(
                task_id,
                message.from_user.id,
                proof
            )
            
            from bot.keyboards.user import get_main_keyboard
            is_admin = message.from_user.id == config.telegram.admin_id
            
            if points_earned > 0:
                await message.answer(
                    f"✅ Задача выполнена!\n🏆 Начислено: {points_earned} баллов",
                    reply_markup=get_main_keyboard(is_admin)
                )
            else:
                await message.answer(
                    f"✅ Задача выполнена!",
                    reply_markup=get_main_keyboard(is_admin)
                )
        
        await state.clear()
    
    @router.message(Command('pending_tasks'))
    async def cmd_pending_tasks(message: Message):
        config = load_config()
        if message.from_user.id != config.telegram.admin_id:
            return
        
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            task_service = TaskService(session, None)
            tasks = await task_service.get_pending_tasks()
            
            if not tasks:
                from bot.keyboards.user import get_main_keyboard
                await message.answer(
                    "📋 Задач на утверждении нет",
                    reply_markup=get_main_keyboard(True)
                )
                return
            
            await message.answer(
                "📋 Задачи на утверждении:",
                reply_markup=get_pending_tasks_keyboard(tasks)
            )
    
    @router.message(Command('completed_tasks'))
    async def cmd_completed_tasks(message: Message):
        config = load_config()
        engine = await init_db(config.database)
        session_factory = get_session(engine)
        
        async with session_factory() as session:
            task_service = TaskService(session, None)
            completed = await task_service.get_completed_tasks(message.from_user.id)
            
            if not completed:
                from bot.keyboards.user import get_main_keyboard
                await message.answer(
                    "📋 У вас пока нет выполненных задач",
                    reply_markup=get_main_keyboard(
                        message.from_user.id == config.telegram.admin_id
                    )
                )
                return
            
            total_points = sum(item['points'] for item in completed)
            
            text = f"✅ Выполненные задачи ({len(completed)} шт., всего {total_points} баллов):\n\n"
            for i, item in enumerate(completed[:20], 1):  # Показываем последние 20
                task = item['task']
                points = item['points']
                text += f"{i}. {task.title}"
                if points > 0:
                    text += f" (+{points} баллов)"
                text += "\n"
            
            if len(completed) > 20:
                text += f"\n... и еще {len(completed) - 20} задач"
            
            await message.answer(text, reply_markup=get_main_keyboard(
                message.from_user.id == config.telegram.admin_id
            ))
    
    dp.include_router(router)
