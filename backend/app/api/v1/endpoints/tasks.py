from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.db.session import get_db
from app.models.base import (
    Task,
    TaskCompletion,
    TaskStatus,
    TaskType,
    User,
)
from app.core.config import settings
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()
oauth2_scheme = HTTPBearer(auto_error=False)


async def get_db_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials:
        raise credentials_exception
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


class TaskCreate(BaseModel):
    title: str
    description: str
    type: TaskType
    points: int
    requires_review: bool = True  # Default to requiring review
    deadline: Optional[str] = None  # ISO date string


@router.get("/")
async def get_tasks(
    current_user: User = Depends(get_db_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all active tasks available to user (excluding already started)"""
    # Get active tasks available to user
    result = await db.execute(
        select(Task)
        .where(
            and_(
                Task.status == TaskStatus.ACTIVE,
                or_(
                    Task.suggested_by == current_user.id,
                    Task.is_personal == False
                )
            )
        )
        .order_by(Task.created_at.desc())
    )
    tasks = result.scalars().all()
    
    # Get task IDs that user has already started/completed
    user_task_ids_result = await db.execute(
        select(TaskCompletion.task_id)
        .where(TaskCompletion.user_id == current_user.id)
    )
    user_task_ids = {r[0] for r in user_task_ids_result.all()}
    
    # Filter out started tasks
    available_tasks = [t for t in tasks if t.id not in user_task_ids]
    
    return available_tasks


@router.post("/")
async def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_db_user),
    db: AsyncSession = Depends(get_db)
):
    from datetime import datetime
    # Parse deadline if provided
    deadline = None
    if task_in.deadline:
        try:
            deadline = datetime.fromisoformat(task_in.deadline.replace('Z', '+00:00'))
        except ValueError:
            pass
    
    task = Task(
        title=task_in.title,
        description=task_in.description,
        type=task_in.type,
        points=task_in.points,
        status=TaskStatus.ACTIVE,
        requires_review=task_in.requires_review,
        deadline=deadline,
        suggested_by=current_user.id
    )
    db.add(task)
    await db.commit()
    return task


@router.get("/by-date")
async def get_tasks_by_date(
    date: Optional[str] = None,  # ISO date string (YYYY-MM-DD)
    current_user: User = Depends(get_db_user),
    db: AsyncSession = Depends(get_db)
):
    """Get tasks for a specific date or tasks without deadline (always visible)"""
    from datetime import datetime, timedelta
    
    result = await db.execute(
        select(Task)
        .where(
            and_(
                Task.status == TaskStatus.ACTIVE,
                or_(
                    Task.suggested_by == current_user.id,
                    Task.is_personal == False
                )
            )
        )
        .order_by(Task.deadline.asc().nulls_last(), Task.created_at.desc())
    )
    tasks = result.scalars().all()
    
    # Get task IDs that user has already started/completed
    user_task_ids_result = await db.execute(
        select(TaskCompletion.task_id)
        .where(TaskCompletion.user_id == current_user.id)
    )
    user_task_ids = {r[0] for r in user_task_ids_result.all()}
    
    # Filter out started tasks
    available_tasks = [t for t in tasks if t.id not in user_task_ids]
    
    if date:
        # Parse the date
        try:
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
            # Filter tasks with deadline on this date OR tasks without deadline
            filtered_tasks = []
            for t in available_tasks:
                if t.deadline is None:
                    # Tasks without deadline always show as "today's tasks"
                    filtered_tasks.append(t)
                elif t.deadline.date() == target_date:
                    filtered_tasks.append(t)
            return filtered_tasks
        except ValueError:
            pass
    
    # Return all available tasks if no date specified
    return available_tasks


@router.get("/calendar")
async def get_task_calendar(
    year: int,
    month: int,
    current_user: User = Depends(get_db_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all dates in a month that have tasks with deadlines"""
    from datetime import datetime
    
    # Calculate date range
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    result = await db.execute(
        select(Task)
        .where(
            and_(
                Task.status == TaskStatus.ACTIVE,
                Task.deadline >= start_date,
                Task.deadline < end_date,
                or_(
                    Task.suggested_by == current_user.id,
                    Task.is_personal == False
                )
            )
        )
    )
    tasks = result.scalars().all()
    
    # Get unique dates with tasks
    dates_with_tasks = set()
    for t in tasks:
        if t.deadline:
            dates_with_tasks.add(t.deadline.day)
    
    return {
        "year": year,
        "month": month,
        "dates_with_tasks": sorted(list(dates_with_tasks))
    }

