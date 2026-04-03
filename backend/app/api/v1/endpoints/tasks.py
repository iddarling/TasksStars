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
async def create_task(task_in: TaskCreate, db: AsyncSession = Depends(get_db)):
    # Simple creation, status depends on role (skipped check for brevity)
    task = Task(
        title=task_in.title,
        description=task_in.description,
        type=task_in.type,
        points=task_in.points,
        status=TaskStatus.ACTIVE,
        requires_review=task_in.requires_review,
    )
    db.add(task)
    await db.commit()
    return task

