from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories import TaskRepository, PointsRepository
from bot.services.notification import NotificationService


class TaskService:
    def __init__(self, session: AsyncSession, notification_service: NotificationService):
        self.task_repo = TaskRepository(session)
        self.points_repo = PointsRepository(session)
        self.notification_service = notification_service
    
    async def create_task(
        self,
        title: str,
        description: str,
        task_type: str,
        created_by: int,
        is_admin: bool = False,
        points: int | None = None
    ) -> int:
        status = 'active' if is_admin else 'draft'
        # Если points не передан и админ, ставим 0 по умолчанию
        if points is None and is_admin:
            points = 0
        elif not is_admin:
            points = None
        
        task = await self.task_repo.create_task(
            title=title,
            description=description,
            task_type=task_type,
            points=points,
            status=status,
            created_by=created_by
        )
        
        if not is_admin:
            await self.notification_service.notify_new_task(task.id)
        
        return task.id
    
    async def get_user_tasks(self, user_id: int) -> list:
        return await self.task_repo.get_user_tasks(user_id)
    
    async def get_user_active_tasks(self, user_id: int) -> list:
        """Получает активные задачи, созданные пользователем"""
        return await self.task_repo.get_user_active_tasks(user_id)
    
    async def get_active_tasks(self, user_id: int | None = None) -> list:
        """Получает активные задачи. Если user_id указан, фильтрует выполненные one-time для этого пользователя"""
        return await self.task_repo.get_active_tasks(user_id)
    
    async def get_pending_tasks(self) -> list:
        return await self.task_repo.get_pending_tasks()
    
    async def approve_task(self, task_id: int, points: int) -> None:
        task = await self.task_repo.update_task_status(task_id, 'active', points)
        await self.notification_service.notify_task_approved(task.created_by, points)
    
    async def complete_task(self, task_id: int, user_id: int, proof: str | None = None) -> tuple[int, int]:
        """Завершает задачу и сразу начисляет баллы. Возвращает (completion_id, points_earned)"""
        # Создаем запись о выполнении со статусом approved (сразу подтверждено)
        completion = await self.task_repo.create_task_completion(task_id, user_id, proof, status='approved')
        
        # Получаем задачу для начисления баллов
        task = await self.task_repo.get_task(task_id)
        points_earned = 0
        
        if task and task.points:
            # Начисляем баллы сразу
            await self.points_repo.add_points(
                user_id,
                task.points,
                f'task_completion_{completion.id}'
            )
            points_earned = task.points
            await self.notification_service.notify_completion_approved(user_id, task.points)
        
        # Для one-time задач меняем статус на completed
        if task and task.type == 'one-time':
            await self.task_repo.update_task_status(task_id, 'completed')
        
        return completion.id, points_earned
    
    async def get_pending_completions(self) -> list:
        return await self.task_repo.get_pending_completions()
    
    async def approve_completion(self, completion_id: int) -> None:
        completion = await self.task_repo.update_completion_status(completion_id, 'approved')
        
        task = await self.task_repo.get_task(completion.task_id)
        if task and task.points:
            await self.points_repo.add_points(
                completion.user_id,
                task.points,
                f'task_completion_{completion.id}'
            )
            await self.notification_service.notify_completion_approved(
                completion.user_id,
                task.points
            )
    
    async def reject_completion(self, completion_id: int) -> None:
        completion = await self.task_repo.update_completion_status(completion_id, 'rejected')
        await self.notification_service.notify_completion_rejected(completion.user_id)
    
    async def get_completed_tasks(self, user_id: int) -> list:
        """Получает список выполненных задач пользователя с деталями"""
        completions = await self.task_repo.get_completed_tasks_by_user(user_id)
        
        result = []
        for completion in completions:
            task = await self.task_repo.get_task(completion.task_id)
            if task:
                result.append({
                    'task': task,
                    'completion': completion,
                    'points': task.points or 0
                })
        
        return result
