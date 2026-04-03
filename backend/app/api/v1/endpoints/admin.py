from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update, delete, and_
from sqlalchemy.orm import joinedload
from app.db.session import get_db
from app.models.base import (
    User,
    UserRole,
    Task,
    TaskCompletion,
    TaskStatus,
    TaskType,
    Reward,
    RewardStatus,
    RewardRequest,
    PointsHistory,
    Notification,
    NotificationType,
)
from app.services.points import PointsService
from app.services.websocket import manager
from app.core.config import settings
from app.core.security import get_password_hash
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter()
oauth2_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
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


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ==================== USER MANAGEMENT ====================

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    balance: Optional[int] = 0

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all users with their balance"""
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    users = result.scalars().all()
    
    user_list = []
    for user in users:
        balance = await PointsService.get_user_balance(db, user.id)
        user_list.append(UserResponse(
            id=user.id,
            email=user.email,
            role=user.role.value,
            balance=balance
        ))
    return user_list


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get user details by ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    balance = await PointsService.get_user_balance(db, user.id)
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role.value,
        balance=balance
    )


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update user details"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_update.email:
        user.email = user_update.email
    if user_update.role:
        user.role = user_update.role
    if user_update.password:
        user.password_hash = get_password_hash(user_update.password)
    
    await db.commit()
    return {"msg": "User updated successfully"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete user"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    await db.delete(user)
    await db.commit()
    return {"msg": "User deleted successfully"}


# ==================== TASK MANAGEMENT ====================

class TaskCreateAdmin(BaseModel):
    title: str
    description: str
    type: TaskType
    points: int
    status: TaskStatus = TaskStatus.ACTIVE
    requires_review: bool = True  # If True, admin must approve completions


class TaskUpdateAdmin(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[TaskType] = None
    points: Optional[int] = None
    status: Optional[TaskStatus] = None
    requires_review: Optional[bool] = None


@router.get("/tasks")
async def get_all_tasks(
    status: Optional[TaskStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all tasks with optional status filter"""
    query = select(Task)
    if status:
        query = query.where(Task.status == status)
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/tasks")
async def create_task_admin(
    task_in: TaskCreateAdmin,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create new task"""
    task = Task(
        title=task_in.title,
        description=task_in.description,
        type=task_in.type,
        points=task_in.points,
        status=task_in.status,
        requires_review=task_in.requires_review,
        created_by=admin.id
    )
    db.add(task)
    await db.commit()
    return task


@router.put("/tasks/{task_id}")
async def update_task_admin(
    task_id: int,
    task_update: TaskUpdateAdmin,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update task"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task_update.title:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.type:
        task.type = task_update.type
    if task_update.points is not None:
        task.points = task_update.points
    if task_update.status:
        task.status = task_update.status
    if task_update.requires_review is not None:
        task.requires_review = task_update.requires_review
    
    await db.commit()
    return task


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete task"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db.delete(task)
    await db.commit()
    return {"msg": "Task deleted successfully"}


# ==================== TASK SUGGESTION MODERATION ====================

@router.get("/pending-tasks")
async def get_pending_task_suggestions(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get tasks suggested by users awaiting approval"""
    result = await db.execute(
        select(Task)
        .options(joinedload(Task.suggested_by_user))
        .where(Task.status == TaskStatus.PENDING)
        .order_by(desc(Task.created_at))
    )
    tasks = result.scalars().all()
    
    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "type": t.type.value,
            "points": t.points,
            "requires_review": t.requires_review,
            "suggested_by": {
                "id": t.suggested_by_user.id if t.suggested_by_user else None,
                "email": t.suggested_by_user.email if t.suggested_by_user else None
            },
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in tasks
    ]


class TaskModerationRequest(BaseModel):
    comment: Optional[str] = None


@router.post("/pending-tasks/{task_id}/approve")
async def approve_task_suggestion(
    task_id: int,
    data: TaskModerationRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Approve user-suggested task"""
    result = await db.execute(
        select(Task).where(
            and_(Task.id == task_id, Task.status == TaskStatus.PENDING)
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Pending task not found")
    
    task.status = TaskStatus.ACTIVE
    task.approved_at = datetime.utcnow()
    task.created_by = admin.id
    
    # Notify user
    if task.suggested_by:
        notification = Notification(
            user_id=task.suggested_by,
            type=NotificationType.TASK_APPROVED,
            title="Task Approved!",
            message=f"Your task '{task.title}' has been approved and is now active.",
            related_id=task.id
        )
        db.add(notification)
    
    await db.commit()
    
    # Notify user via WebSocket
    if task.suggested_by:
        await manager.send_to_user(task.suggested_by, {
            "type": "task_suggestion_approved",
            "data": {
                "task_id": task.id,
                "title": task.title,
                "status": "active"
            }
        })
    
    return {
        "msg": "Task approved successfully",
        "task_id": task.id,
        "status": "active"
    }


@router.post("/pending-tasks/{task_id}/reject")
async def reject_task_suggestion(
    task_id: int,
    data: TaskModerationRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Reject user-suggested task"""
    result = await db.execute(
        select(Task).where(
            and_(Task.id == task_id, Task.status == TaskStatus.PENDING)
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Pending task not found")
    
    # Notify user
    if task.suggested_by:
        notification = Notification(
            user_id=task.suggested_by,
            type=NotificationType.TASK_REJECTED,
            title="Task Rejected",
            message=f"Your task '{task.title}' was not approved. Reason: {data.comment or 'No reason provided'}",
            related_id=task.id
        )
        db.add(notification)
    
    await db.delete(task)
    await db.commit()
    
    # Notify user via WebSocket
    if task.suggested_by:
        await manager.send_to_user(task.suggested_by, {
            "type": "task_suggestion_rejected",
            "data": {
                "task_id": task_id,
                "title": task.title,
                "admin_comment": data.comment
            }
        })
    
    return {
        "msg": "Task rejected and deleted",
        "task_id": task_id
    }


# ==================== TASK COMPLETIONS MANAGEMENT ====================

@router.get("/completions")
async def get_pending_completions(
    status: Optional[TaskStatus] = TaskStatus.COMPLETED,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get task completions with status filter"""
    query = select(TaskCompletion).options(
        joinedload(TaskCompletion.task),
        joinedload(TaskCompletion.user)
    )
    if status:
        query = query.where(TaskCompletion.status == status)
    query = query.order_by(desc(TaskCompletion.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    completions = result.scalars().all()
    
    return [
        {
            "id": c.id,
            "task_id": c.task_id,
            "task_title": c.task.title if c.task else None,
            "user_id": c.user_id,
            "user_email": c.user.email if c.user else None,
            "proof": c.proof,
            "status": c.status.value,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "points": c.task.points if c.task else 0
        }
        for c in completions
    ]


@router.post("/completions/{completion_id}/approve")
async def approve_completion_admin(
    completion_id: int,
    data: TaskModerationRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Approve task completion and award points"""
    result = await db.execute(
        select(TaskCompletion)
        .options(joinedload(TaskCompletion.task), joinedload(TaskCompletion.user))
        .where(TaskCompletion.id == completion_id)
    )
    completion = result.scalar_one_or_none()
    if not completion:
        raise HTTPException(status_code=404, detail="Completion not found")
    
    if completion.status == TaskStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Already approved")
    
    completion.status = TaskStatus.APPROVED
    completion.admin_comment = data.comment
    completion.reviewed_at = datetime.utcnow()
    
    # Award points
    task = completion.task
    if task:
        completion.points_awarded = task.points
        await PointsService.add_points(
            db, completion.user_id, task.points, f"task_completion:{completion.id}"
        )
    
    # Notify user
    notification = Notification(
        user_id=completion.user_id,
        type=NotificationType.COMPLETION_APPROVED,
        title="Task Completed!",
        message=f"Your completion of '{task.title if task else 'task'}' was approved. You earned {task.points if task else 0} points!",
        related_id=completion.id
    )
    db.add(notification)
    
    await db.commit()
    
    # Notify user via WebSocket
    await manager.send_to_user(completion.user_id, {
        "type": "completion_approved",
        "data": {
            "completion_id": completion.id,
            "task_id": task.id if task else None,
            "points_awarded": task.points if task else 0,
            "new_balance": await PointsService.get_user_balance(db, completion.user_id)
        }
    })
    
    return {
        "msg": "Completion approved",
        "points_awarded": task.points if task else 0,
        "user_email": completion.user.email if completion.user else None
    }


@router.post("/completions/{completion_id}/reject")
async def reject_completion(
    completion_id: int,
    data: TaskModerationRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Reject task completion with feedback"""
    result = await db.execute(
        select(TaskCompletion)
        .options(joinedload(TaskCompletion.task), joinedload(TaskCompletion.user))
        .where(TaskCompletion.id == completion_id)
    )
    completion = result.scalar_one_or_none()
    if not completion:
        raise HTTPException(status_code=404, detail="Completion not found")
    
    if completion.status not in [TaskStatus.PENDING, TaskStatus.COMPLETED]:
        raise HTTPException(status_code=400, detail="Can only reject pending or completed tasks")
    
    completion.status = TaskStatus.REJECTED
    completion.admin_comment = data.comment
    completion.reviewed_at = datetime.utcnow()
    
    # Notify user
    task = completion.task
    notification = Notification(
        user_id=completion.user_id,
        type=NotificationType.COMPLETION_REJECTED,
        title="Task Completion Rejected",
        message=f"Your completion of '{task.title if task else 'task'}' was not approved. Reason: {data.comment or 'No reason provided'}. You can try again.",
        related_id=completion.id
    )
    db.add(notification)
    
    await db.commit()
    
    # Notify user via WebSocket
    await manager.send_to_user(completion.user_id, {
        "type": "completion_rejected",
        "data": {
            "completion_id": completion.id,
            "task_id": task.id if task else None,
            "admin_comment": data.comment
        }
    })
    
    return {
        "msg": "Completion rejected",
        "admin_comment": data.comment,
        "user_email": completion.user.email if completion.user else None
    }


# ==================== REWARD MANAGEMENT ====================

class RewardCreateAdmin(BaseModel):
    title: str
    description: str
    cost: int
    status: RewardStatus = RewardStatus.ACTIVE


class RewardUpdateAdmin(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    cost: Optional[int] = None
    status: Optional[RewardStatus] = None


@router.get("/rewards")
async def get_all_rewards(
    status: Optional[RewardStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all rewards"""
    query = select(Reward)
    if status:
        query = query.where(Reward.status == status)
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/rewards")
async def create_reward_admin(
    reward_in: RewardCreateAdmin,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create new reward"""
    reward = Reward(
        title=reward_in.title,
        description=reward_in.description,
        cost=reward_in.cost,
        status=reward_in.status
    )
    db.add(reward)
    await db.commit()
    return reward


@router.put("/rewards/{reward_id}")
async def update_reward(
    reward_id: int,
    reward_update: RewardUpdateAdmin,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update reward"""
    result = await db.execute(select(Reward).where(Reward.id == reward_id))
    reward = result.scalar_one_or_none()
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    
    if reward_update.title:
        reward.title = reward_update.title
    if reward_update.description is not None:
        reward.description = reward_update.description
    if reward_update.cost is not None:
        reward.cost = reward_update.cost
    if reward_update.status:
        reward.status = reward_update.status
    
    await db.commit()
    return reward


@router.delete("/rewards/{reward_id}")
async def delete_reward(
    reward_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete reward"""
    result = await db.execute(select(Reward).where(Reward.id == reward_id))
    reward = result.scalar_one_or_none()
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    
    await db.delete(reward)
    await db.commit()
    return {"msg": "Reward deleted successfully"}


# ==================== REWARD REQUESTS ====================

@router.get("/reward-requests")
async def get_reward_requests(
    status: Optional[str] = "pending",
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get reward redemption requests"""
    query = select(RewardRequest).options(
        joinedload(RewardRequest.reward),
        joinedload(RewardRequest.user)
    )
    if status:
        query = query.where(RewardRequest.status == status)
    query = query.order_by(desc(RewardRequest.created_at))
    
    result = await db.execute(query)
    requests = result.scalars().all()
    
    return [
        {
            "id": r.id,
            "reward_id": r.reward_id,
            "reward_title": r.reward.title if r.reward else None,
            "reward_cost": r.reward.cost if r.reward else 0,
            "user_id": r.user_id,
            "user_email": r.user.email if r.user else None,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in requests
    ]


@router.post("/reward-requests/{request_id}/approve")
async def approve_reward_request(
    request_id: int,
    data: TaskModerationRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Approve reward request (deduct points)"""
    result = await db.execute(
        select(RewardRequest)
        .options(joinedload(RewardRequest.reward), joinedload(RewardRequest.user))
        .where(RewardRequest.id == request_id)
    )
    request = result.scalar_one_or_none()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")
    
    # Check user balance
    balance = await PointsService.get_user_balance(db, request.user_id)
    reward = request.reward
    
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    
    if balance < reward.cost:
        raise HTTPException(status_code=400, detail="User has insufficient points")
    
    # Deduct points and approve
    await PointsService.add_points(
        db, request.user_id, -reward.cost, f"reward_redemption:{request.id}"
    )
    request.status = "approved"
    request.points_spent = reward.cost
    request.reviewed_at = datetime.utcnow()
    request.admin_comment = data.comment
    
    # Notify user
    notification = Notification(
        user_id=request.user_id,
        type=NotificationType.REWARD_APPROVED,
        title="Reward Approved!",
        message=f"Your request for '{reward.title}' was approved! {reward.cost} points have been deducted.",
        related_id=request.id
    )
    db.add(notification)
    
    await db.commit()
    
    # Notify user via WebSocket
    await manager.send_to_user(request.user_id, {
        "type": "reward_request_approved",
        "data": {
            "request_id": request.id,
            "reward_id": reward.id if reward else None,
            "reward_title": reward.title if reward else None,
            "points_deducted": reward.cost if reward else 0,
            "new_balance": await PointsService.get_user_balance(db, request.user_id)
        }
    })
    
    return {
        "msg": "Reward request approved",
        "points_deducted": reward.cost,
        "user_email": request.user.email if request.user else None
    }


@router.post("/reward-requests/{request_id}/reject")
async def reject_reward_request(
    request_id: int,
    data: TaskModerationRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Reject reward request with feedback"""
    result = await db.execute(
        select(RewardRequest)
        .options(joinedload(RewardRequest.reward), joinedload(RewardRequest.user))
        .where(RewardRequest.id == request_id)
    )
    request = result.scalar_one_or_none()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")
    
    request.status = "rejected"
    request.reviewed_at = datetime.utcnow()
    request.admin_comment = data.comment
    
    # Notify user
    reward = request.reward
    notification = Notification(
        user_id=request.user_id,
        type=NotificationType.REWARD_REJECTED,
        title="Reward Request Rejected",
        message=f"Your request for '{reward.title if reward else 'reward'}' was not approved. Reason: {data.comment or 'No reason provided'}",
        related_id=request.id
    )
    db.add(notification)
    
    await db.commit()
    
    # Notify user via WebSocket
    await manager.send_to_user(request.user_id, {
        "type": "reward_request_rejected",
        "data": {
            "request_id": request.id,
            "reward_id": reward.id if reward else None,
            "reward_title": reward.title if reward else None,
            "admin_comment": data.comment
        }
    })
    
    return {
        "msg": "Reward request rejected",
        "admin_comment": data.comment,
        "user_email": request.user.email if request.user else None
    }


# ==================== STATISTICS ====================

@router.get("/stats/dashboard")
async def get_dashboard_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard statistics"""
    # Total users
    users_result = await db.execute(select(func.count(User.id)))
    total_users = users_result.scalar()
    
    # Total tasks
    tasks_result = await db.execute(select(func.count(Task.id)))
    total_tasks = tasks_result.scalar()
    
    # Active tasks
    active_tasks_result = await db.execute(
        select(func.count(Task.id)).where(Task.status == TaskStatus.ACTIVE)
    )
    active_tasks = active_tasks_result.scalar()
    
    # Total completions
    completions_result = await db.execute(select(func.count(TaskCompletion.id)))
    total_completions = completions_result.scalar()
    
    # Pending completions
    pending_result = await db.execute(
        select(func.count(TaskCompletion.id))
        .where(TaskCompletion.status == TaskStatus.PENDING)
    )
    pending_completions = pending_result.scalar()
    
    # Approved completions
    approved_result = await db.execute(
        select(func.count(TaskCompletion.id))
        .where(TaskCompletion.status == TaskStatus.APPROVED)
    )
    approved_completions = approved_result.scalar()
    
    # Total points awarded
    points_result = await db.execute(
        select(func.sum(PointsHistory.amount)).where(PointsHistory.amount > 0)
    )
    total_points_awarded = points_result.scalar() or 0
    
    # Total rewards
    rewards_result = await db.execute(select(func.count(Reward.id)))
    total_rewards = rewards_result.scalar()
    
    # Active rewards
    active_rewards_result = await db.execute(
        select(func.count(Reward.id)).where(Reward.status == RewardStatus.ACTIVE)
    )
    active_rewards = active_rewards_result.scalar()
    
    # Pending reward requests
    pending_rewards_result = await db.execute(
        select(func.count(RewardRequest.id)).where(RewardRequest.status == "pending")
    )
    pending_reward_requests = pending_rewards_result.scalar()
    
    return {
        "users": {
            "total": total_users,
            "admins": (
                await db.execute(
                    select(func.count(User.id)).where(User.role == UserRole.ADMIN)
                )
            ).scalar(),
            "regular": (
                await db.execute(
                    select(func.count(User.id)).where(User.role == UserRole.USER)
                )
            ).scalar()
        },
        "tasks": {
            "total": total_tasks,
            "active": active_tasks,
            "draft": (
                await db.execute(
                    select(func.count(Task.id)).where(Task.status == TaskStatus.DRAFT)
                )
            ).scalar()
        },
        "completions": {
            "total": total_completions,
            "pending": pending_completions,
            "approved": approved_completions,
            "rejected": (
                await db.execute(
                    select(func.count(TaskCompletion.id))
                    .where(TaskCompletion.status == TaskStatus.REJECTED)
                )
            ).scalar()
        },
        "points": {
            "total_awarded": total_points_awarded,
            "total_redeemed": abs(
                (
                    await db.execute(
                        select(func.sum(PointsHistory.amount)).where(PointsHistory.amount < 0)
                    )
                ).scalar() or 0
            )
        },
        "rewards": {
            "total": total_rewards,
            "active": active_rewards,
            "proposed": (
                await db.execute(
                    select(func.count(Reward.id)).where(Reward.status == RewardStatus.PROPOSED)
                )
            ).scalar(),
            "pending_requests": pending_reward_requests
        }
    }


@router.get("/users/{user_id}/details")
async def get_user_details(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed user information with all tasks, rewards, and balance"""
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get balance
    balance = await PointsService.get_user_balance(db, user_id)
    
    # Get active tasks (completions in progress)
    active_completions_result = await db.execute(
        select(TaskCompletion)
        .options(joinedload(TaskCompletion.task))
        .where(TaskCompletion.user_id == user_id)
        .where(TaskCompletion.status == TaskStatus.IN_PROGRESS)
    )
    active_completions = active_completions_result.scalars().all()
    
    # Get completed tasks (approved completions)
    completed_result = await db.execute(
        select(TaskCompletion)
        .options(joinedload(TaskCompletion.task))
        .where(TaskCompletion.user_id == user_id)
        .where(TaskCompletion.status == TaskStatus.APPROVED)
        .order_by(desc(TaskCompletion.completed_at))
    )
    completed_tasks = completed_result.scalars().all()
    
    # Get pending task completions
    pending_completions_result = await db.execute(
        select(TaskCompletion)
        .options(joinedload(TaskCompletion.task))
        .where(TaskCompletion.user_id == user_id)
        .where(TaskCompletion.status == TaskStatus.COMPLETED)
        .order_by(desc(TaskCompletion.created_at))
    )
    pending_completions = pending_completions_result.scalars().all()
    
    # Get reward requests
    reward_requests_result = await db.execute(
        select(RewardRequest)
        .options(joinedload(RewardRequest.reward))
        .where(RewardRequest.user_id == user_id)
        .order_by(desc(RewardRequest.created_at))
    )
    reward_requests = reward_requests_result.scalars().all()
    
    # Get points history
    points_history_result = await db.execute(
        select(PointsHistory)
        .where(PointsHistory.user_id == user_id)
        .order_by(desc(PointsHistory.created_at))
        .limit(50)
    )
    points_history = points_history_result.scalars().all()
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "balance": balance
        },
        "active_tasks": [
            {
                "id": c.id,
                "task_id": c.task_id,
                "title": c.task.title if c.task else "Unknown",
                "description": c.task.description if c.task else "",
                "points": c.task.points if c.task else 0,
                "started_at": c.started_at.isoformat() if c.started_at else None,
                "time_spent": c.time_spent
            }
            for c in active_completions
        ],
        "completed_tasks": [
            {
                "id": c.id,
                "task_id": c.task_id,
                "title": c.task.title if c.task else "Unknown",
                "points_awarded": c.points_awarded,
                "completed_at": c.completed_at.isoformat() if c.completed_at else None,
                "time_spent": c.time_spent
            }
            for c in completed_tasks
        ],
        "pending_completions": [
            {
                "id": c.id,
                "task_id": c.task_id,
                "title": c.task.title if c.task else "Unknown",
                "proof": c.proof,
                "proof_image_url": c.proof_image_url,
                "points": c.task.points if c.task else 0,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in pending_completions
        ],
        "reward_requests": [
            {
                "id": r.id,
                "reward_id": r.reward_id,
                "reward_title": r.reward.title if r.reward else None,
                "reward_description": r.reward.description if r.reward else None,
                "points_spent": r.points_spent or (r.reward.cost if r.reward else 0),
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in reward_requests
        ],
        "points_history": [
            {
                "id": h.id,
                "amount": h.amount,
                "source": h.source,
                "created_at": h.created_at.isoformat() if h.created_at else None
            }
            for h in points_history
        ]
    }


@router.get("/stats/users/{user_id}")
async def get_user_stats(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed statistics for a specific user"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Balance
    balance = await PointsService.get_user_balance(db, user_id)
    
    # Total earned
    earned_result = await db.execute(
        select(func.sum(PointsHistory.amount))
        .where(PointsHistory.user_id == user_id, PointsHistory.amount > 0)
    )
    total_earned = earned_result.scalar() or 0
    
    # Total spent
    spent_result = await db.execute(
        select(func.sum(PointsHistory.amount))
        .where(PointsHistory.user_id == user_id, PointsHistory.amount < 0)
    )
    total_spent = abs(spent_result.scalar() or 0)
    
    # Task completions
    completions_result = await db.execute(
        select(func.count(TaskCompletion.id)).where(TaskCompletion.user_id == user_id)
    )
    completions = completions_result.scalar()
    
    approved_completions_result = await db.execute(
        select(func.count(TaskCompletion.id))
        .where(TaskCompletion.user_id == user_id, TaskCompletion.status == TaskStatus.APPROVED)
    )
    approved_completions = approved_completions_result.scalar()
    
    # Reward requests
    rewards_result = await db.execute(
        select(func.count(RewardRequest.id)).where(RewardRequest.user_id == user_id)
    )
    reward_requests = rewards_result.scalar()
    
    # Points history
    history_result = await db.execute(
        select(PointsHistory)
        .where(PointsHistory.user_id == user_id)
        .order_by(desc(PointsHistory.created_at))
        .limit(10)
    )
    recent_history = history_result.scalars().all()
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
            "created_at": user.completions[0].created_at.isoformat() if user.completions else None
        },
        "balance": balance,
        "stats": {
            "total_earned": total_earned,
            "total_spent": total_spent,
            "completions_total": completions,
            "completions_approved": approved_completions,
            "reward_requests": reward_requests
        },
        "recent_history": [
            {
                "id": h.id,
                "amount": h.amount,
                "source": h.source,
                "created_at": h.created_at.isoformat() if h.created_at else None
            }
            for h in recent_history
        ]
    }


@router.get("/stats/top-users")
async def get_top_users(
    limit: int = Query(10, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get top users by points earned"""
    result = await db.execute(
        select(
            User.id,
            User.email,
            func.sum(PointsHistory.amount).label("total_points")
        )
        .join(PointsHistory, User.id == PointsHistory.user_id)
        .where(PointsHistory.amount > 0)
        .group_by(User.id)
        .order_by(desc("total_points"))
        .limit(limit)
    )
    
    users = result.all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "total_points": u.total_points or 0
        }
        for u in users
    ]


@router.get("/stats/task-performance")
async def get_task_performance(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get task completion statistics"""
    result = await db.execute(
        select(
            Task.id,
            Task.title,
            Task.points,
            func.count(TaskCompletion.id).label("completion_count"),
            func.sum(func.case((TaskCompletion.status == TaskStatus.APPROVED, 1), else_=0)).label("approved_count")
        )
        .outerjoin(TaskCompletion, Task.id == TaskCompletion.task_id)
        .group_by(Task.id)
        .order_by(desc("completion_count"))
    )
    
    tasks = result.all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "points": t.points,
            "total_completions": t.completion_count,
            "approved_completions": t.approved_count or 0
        }
        for t in tasks
    ]


# ==================== POINTS MANAGEMENT ====================

class PointsAdjustment(BaseModel):
    user_id: int
    amount: int
    reason: str


@router.post("/points/adjust")
async def adjust_user_points(
    adjustment: PointsAdjustment,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Manually adjust user points (admin only)"""
    result = await db.execute(select(User).where(User.id == adjustment.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await PointsService.add_points(
        db, adjustment.user_id, adjustment.amount, f"admin_adjustment:{admin.id}:{adjustment.reason}"
    )
    await db.commit()
    
    new_balance = await PointsService.get_user_balance(db, adjustment.user_id)
    
    return {
        "msg": "Points adjusted",
        "user_id": adjustment.user_id,
        "amount": adjustment.amount,
        "new_balance": new_balance
    }


@router.get("/points/history")
async def get_all_points_history(
    user_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get points history (all users or specific user)"""
    query = select(PointsHistory).options(joinedload(PointsHistory.user))
    if user_id:
        query = query.where(PointsHistory.user_id == user_id)
    query = query.order_by(desc(PointsHistory.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    history = result.scalars().all()
    
    return [
        {
            "id": h.id,
            "user_id": h.user_id,
            "user_email": h.user.email if h.user else None,
            "amount": h.amount,
            "source": h.source,
            "created_at": h.created_at.isoformat() if h.created_at else None
        }
        for h in history
    ]
