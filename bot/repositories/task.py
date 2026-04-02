from datetime import datetime, date
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import Task, TaskCompletion


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_task(
        self,
        title: str,
        description: str,
        task_type: str,
        points: int | None,
        status: str,
        created_by: int
    ) -> Task:
        task = Task(
            title=title,
            description=description,
            type=task_type,
            points=points,
            status=status,
            created_by=created_by
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task
    
    async def get_task(self, task_id: int) -> Task | None:
        stmt = select(Task).where(Task.id == task_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_tasks(self, user_id: int, status: str | None = None) -> list[Task]:
        stmt = select(Task).where(Task.created_by == user_id)
        if status:
            stmt = stmt.where(Task.status == status)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_active_tasks(self, user_id: int | None = None) -> list[Task]:
        """Получает активные задачи. Для one-time исключает выполненные."""
        from datetime import datetime, date
        
        if user_id:
            # Для конкретного пользователя - фильтруем выполненные one-time
            today = date.today()
            stmt = (
                select(Task)
                .where(
                    and_(
                        Task.status == 'active',
                        or_(
                            # Daily задачи показываем если не выполнены сегодня
                            and_(
                                Task.type == 'daily',
                                ~Task.completions.any(
                                    and_(
                                        TaskCompletion.user_id == user_id,
                                        TaskCompletion.status == 'approved',
                                        TaskCompletion.created_at >= datetime.combine(today, datetime.min.time())
                                    )
                                )
                            ),
                            # One-time задачи показываем если никогда не выполнены
                            and_(
                                Task.type == 'one-time',
                                ~Task.completions.any(
                                    and_(
                                        TaskCompletion.user_id == user_id,
                                        TaskCompletion.status == 'approved'
                                    )
                                )
                            )
                        )
                    )
                )
            )
        else:
            # Для админа - все активные задачи
            stmt = select(Task).where(Task.status == 'active')
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_user_active_tasks(self, user_id: int) -> list[Task]:
        """Получает активные задачи, созданные пользователем, исключая выполненные one-time"""
        from datetime import datetime, date
        
        today = date.today()
        stmt = (
            select(Task)
            .where(
                and_(
                    Task.status == 'active',
                    Task.created_by == user_id,
                    or_(
                        # Daily задачи показываем если не выполнены сегодня
                        and_(
                            Task.type == 'daily',
                            ~Task.completions.any(
                                and_(
                                    TaskCompletion.user_id == user_id,
                                    TaskCompletion.status == 'approved',
                                    TaskCompletion.created_at >= datetime.combine(today, datetime.min.time())
                                )
                            )
                        ),
                        # One-time задачи показываем если никогда не выполнены
                        and_(
                            Task.type == 'one-time',
                            ~Task.completions.any(
                                and_(
                                    TaskCompletion.user_id == user_id,
                                    TaskCompletion.status == 'approved'
                                )
                            )
                        )
                    )
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_pending_tasks(self) -> list[Task]:
        stmt = select(Task).where(Task.status == 'draft')
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_task_status(self, task_id: int, status: str, points: int | None = None) -> Task:
        stmt = select(Task).where(Task.id == task_id)
        result = await self.session.execute(stmt)
        task = result.scalar_one()
        
        task.status = status
        if points is not None:
            task.points = points
        
        await self.session.commit()
        await self.session.refresh(task)
        return task
    
    async def create_task_completion(
        self,
        task_id: int,
        user_id: int,
        proof: str | None = None,
        status: str = 'pending'
    ) -> TaskCompletion:
        completion = TaskCompletion(
            task_id=task_id,
            user_id=user_id,
            proof=proof,
            status=status
        )
        self.session.add(completion)
        await self.session.commit()
        await self.session.refresh(completion)
        return completion
    
    async def get_pending_completions(self) -> list[TaskCompletion]:
        stmt = select(TaskCompletion).where(TaskCompletion.status == 'pending')
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_completion_status(
        self,
        completion_id: int,
        status: str
    ) -> TaskCompletion:
        stmt = select(TaskCompletion).where(TaskCompletion.id == completion_id)
        result = await self.session.execute(stmt)
        completion = result.scalar_one()
        
        completion.status = status
        await self.session.commit()
        await self.session.refresh(completion)
        return completion
    
    async def get_completed_tasks_by_user(self, user_id: int) -> list[TaskCompletion]:
        """Получает все выполненные задачи пользователя"""
        stmt = (
            select(TaskCompletion)
            .where(
                and_(
                    TaskCompletion.user_id == user_id,
                    TaskCompletion.status == 'approved'
                )
            )
            .order_by(TaskCompletion.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_daily_tasks_not_completed_today(self, user_id: int) -> list[Task]:
        today = date.today()
        stmt = (
            select(Task)
            .outerjoin(TaskCompletion)
            .where(
                and_(
                    Task.type == 'daily',
                    Task.status == 'active',
                    ~Task.completions.any(
                        and_(
                            TaskCompletion.user_id == user_id,
                            TaskCompletion.status == 'approved',
                            TaskCompletion.created_at >= datetime.combine(today, datetime.min.time())
                        )
                    )
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
