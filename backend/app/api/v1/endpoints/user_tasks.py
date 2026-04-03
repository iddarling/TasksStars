from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_, or_
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
from pydantic import BaseModel
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


async def create_notification(db: AsyncSession, user_id: int, type: NotificationType, title: str, message: str, related_id: int = None):
    """Helper to create notifications"""
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        related_id=related_id
    )
    db.add(notification)


# ==================== TASK SUGGESTION (User creates task) ====================

class TaskSuggest(BaseModel):
    title: str
    description: str
    type: TaskType
    points: int
    requires_review: bool = True  # Default to requiring admin review


@router.post("/suggest")
async def suggest_task(
    task_in: TaskSuggest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """User suggests a new task (auto-approved if requires_review=False)"""
    
    # Determine task status based on requires_review flag
    if task_in.requires_review:
        task_status = TaskStatus.PENDING
    else:
        task_status = TaskStatus.ACTIVE
    
    task = Task(
        title=task_in.title,
        description=task_in.description,
        type=task_in.type,
        points=task_in.points,
        status=task_status,
        suggested_by=current_user.id,
        requires_review=task_in.requires_review,
        is_personal=True,  # User-suggested tasks are personal by default
    )
    db.add(task)
    await db.commit()
    
    if task_in.requires_review:
        # Broadcast to all admins about new pending task
        await manager.broadcast({
            "type": "task_suggested_by_user",
            "data": {
                "task_id": task.id,
                "title": task.title,
                "suggested_by": current_user.id,
                "suggested_by_email": current_user.email,
                "points": task.points,
                "status": "pending"
            }
        })
        
        return {
            "msg": "Task suggested successfully",
            "task_id": task.id,
            "status": "pending",
            "note": "Task is awaiting admin approval"
        }
    else:
        # Task is active immediately - broadcast to refresh available tasks
        await manager.send_to_user(current_user.id, {
            "type": "task_created",
            "data": {
                "task_id": task.id,
                "title": task.title,
                "points": task.points,
                "status": "active",
                "auto_approved": True
            }
        })
        
        return {
            "msg": "Task created and approved automatically",
            "task_id": task.id,
            "status": "active",
            "note": "Task is now available to complete"
        }


# ==================== USER TASKS ====================

@router.get("/my-active")
async def get_my_active_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's in-progress task completions with task details"""
    result = await db.execute(
        select(TaskCompletion)
        .options(joinedload(TaskCompletion.task))
        .where(
            and_(
                TaskCompletion.user_id == current_user.id,
                TaskCompletion.status == TaskStatus.IN_PROGRESS
            )
        )
        .order_by(desc(TaskCompletion.created_at))
    )
    completions = result.scalars().all()
    
    return [
        {
            "id": c.id,
            "task_id": c.task_id,
            "user_id": c.user_id,
            "task": {
                "id": c.task.id,
                "title": c.task.title,
                "description": c.task.description,
                "type": c.task.type.value,
                "points": c.task.points,
                "requires_review": c.task.requires_review,
                "status": c.task.status.value,
                "created_at": c.task.created_at.isoformat() if c.task.created_at else None,
            } if c.task else None,
            "started_at": c.started_at.isoformat() if c.started_at else None,
            "time_spent": c.time_spent,
            "status": c.status.value,
        }
        for c in completions
    ]


@router.get("/my-pending")
async def get_my_pending_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get tasks suggested by user that are awaiting admin approval"""
    result = await db.execute(
        select(Task)
        .where(
            and_(
                Task.suggested_by == current_user.id,
                Task.status == TaskStatus.PENDING
            )
        )
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
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tasks
    ]


@router.get("/my-completed")
async def get_my_completed_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get APPROVED completed task instances only (for completed tab)"""
    result = await db.execute(
        select(TaskCompletion)
        .options(joinedload(TaskCompletion.task))
        .where(TaskCompletion.user_id == current_user.id)
        .where(TaskCompletion.status == TaskStatus.APPROVED)
        .order_by(desc(TaskCompletion.completed_at))
    )
    completions = result.scalars().all()
    
    return [
        {
            "id": c.id,
            "task_id": c.task_id,
            "task": {
                "id": c.task.id if c.task else None,
                "title": c.task.title if c.task else "Unknown",
                "description": c.task.description if c.task else "",
                "type": c.task.type.value if c.task else "one-time",
                "points": c.task.points if c.task else 0,
            },
            "points_awarded": c.points_awarded,
            "status": c.status.value,
            "proof": c.proof,
            "proof_image_url": c.proof_image_url,
            "admin_comment": c.admin_comment,
            "time_spent": c.time_spent,
            "started_at": c.started_at.isoformat() if c.started_at else None,
            "completed_at": c.completed_at.isoformat() if c.completed_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in completions
    ]


@router.get("/my-awaiting-review")
async def get_my_awaiting_review(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get tasks awaiting admin review (COMPLETED status, not yet approved)"""
    result = await db.execute(
        select(TaskCompletion)
        .options(joinedload(TaskCompletion.task))
        .where(TaskCompletion.user_id == current_user.id)
        .where(TaskCompletion.status == TaskStatus.COMPLETED)
        .order_by(desc(TaskCompletion.completed_at))
    )
    completions = result.scalars().all()
    
    return [
        {
            "id": c.id,
            "task_id": c.task_id,
            "task": {
                "id": c.task.id if c.task else None,
                "title": c.task.title if c.task else "Unknown",
                "description": c.task.description if c.task else "",
                "type": c.task.type.value if c.task else "one-time",
                "points": c.task.points if c.task else 0,
            },
            "points_awarded": c.points_awarded,
            "status": c.status.value,
            "proof": c.proof,
            "proof_image_url": c.proof_image_url,
            "admin_comment": c.admin_comment,
            "time_spent": c.time_spent,
            "started_at": c.started_at.isoformat() if c.started_at else None,
            "completed_at": c.completed_at.isoformat() if c.completed_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in completions
    ]


# ==================== TASK EXECUTION ====================

@router.post("/{task_id}/start")
async def start_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start task timer - creates TaskCompletion record with IN_PROGRESS status"""
    # Verify task exists and is active
    task_result = await db.execute(
        select(Task).where(
            and_(
                Task.id == task_id,
                Task.status == TaskStatus.ACTIVE
            )
        )
    )
    task = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or not active")
    
    # Check if user already has this task in progress
    existing = await db.execute(
        select(TaskCompletion)
        .where(
            and_(
                TaskCompletion.task_id == task_id,
                TaskCompletion.user_id == current_user.id,
                TaskCompletion.status == TaskStatus.IN_PROGRESS
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Task already in progress")
    
    # Create completion record
    completion = TaskCompletion(
        task_id=task_id,
        user_id=current_user.id,
        status=TaskStatus.IN_PROGRESS,
        started_at=datetime.utcnow(),
        time_spent=0
    )
    db.add(completion)
    await db.commit()
    
    # Broadcast update to user
    await manager.send_to_user(current_user.id, {
        "type": "task_started",
        "data": {
            "completion_id": completion.id,
            "task_id": task_id,
            "started_at": completion.started_at.isoformat()
        }
    })
    
    return {
        "msg": "Task started",
        "completion_id": completion.id,
        "started_at": completion.started_at.isoformat()
    }


class TaskCompleteRequest(BaseModel):
    proof: Optional[str] = None
    proof_image_url: Optional[str] = None
    time_spent: int  # Time in seconds


@router.post("/{task_id}/complete")
async def complete_task(
    task_id: int,
    data: TaskCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Complete task - saves proof and time spent"""
    # Find in-progress completion
    result = await db.execute(
        select(TaskCompletion)
        .options(joinedload(TaskCompletion.task))
        .where(
            and_(
                TaskCompletion.task_id == task_id,
                TaskCompletion.user_id == current_user.id,
                TaskCompletion.status == TaskStatus.IN_PROGRESS
            )
        )
    )
    completion = result.scalar_one_or_none()
    
    if not completion:
        raise HTTPException(status_code=404, detail="No active task execution found")
    
    task = completion.task
    
    # Update completion
    completion.completed_at = datetime.utcnow()
    completion.time_spent = data.time_spent
    completion.proof = data.proof
    completion.proof_image_url = data.proof_image_url
    
    if task.requires_review:
        # Needs admin approval
        completion.status = TaskStatus.COMPLETED
        await db.commit()
        
        # Broadcast to admins about pending review
        await manager.broadcast({
            "type": "task_completion_pending_review",
            "data": {
                "completion_id": completion.id,
                "task_id": task_id,
                "task_title": task.title,
                "user_id": current_user.id,
                "user_email": current_user.email,
                "points": task.points,
                "status": "completed_pending_review"
            }
        })
        
        # Broadcast to user
        await manager.send_to_user(current_user.id, {
            "type": "task_completed_pending",
            "data": {
                "completion_id": completion.id,
                "task_id": task_id,
                "points_pending": task.points
            }
        })
        
        return {
            "msg": "Task completed, awaiting admin review",
            "completion_id": completion.id,
            "status": "completed_pending_review",
            "time_spent": data.time_spent,
            "points_pending": task.points
        }
    else:
        # Auto-approve, give points immediately
        completion.status = TaskStatus.APPROVED
        completion.points_awarded = task.points
        completion.reviewed_at = datetime.utcnow()
        
        # Award points
        await PointsService.add_points(
            db, current_user.id, task.points, f"task_completion:{completion.id}"
        )
        await db.commit()
        
        # Create notification
        await create_notification(
            db, current_user.id,
            NotificationType.COMPLETION_APPROVED,
            "Task Completed!",
            f"You earned {task.points} points for completing '{task.title}'",
            completion.id
        )
        await db.commit()
        
        # Broadcast to user
        await manager.send_to_user(current_user.id, {
            "type": "task_completed_approved",
            "data": {
                "completion_id": completion.id,
                "task_id": task_id,
                "points_earned": task.points,
                "new_balance": await PointsService.get_user_balance(db, current_user.id)
            }
        })
        
        return {
            "msg": "Task completed and approved automatically",
            "completion_id": completion.id,
            "points_earned": task.points,
            "time_spent": data.time_spent,
            "new_balance": await PointsService.get_user_balance(db, current_user.id)
        }


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel in-progress task"""
    result = await db.execute(
        select(TaskCompletion)
        .where(
            and_(
                TaskCompletion.task_id == task_id,
                TaskCompletion.user_id == current_user.id,
                TaskCompletion.status == TaskStatus.IN_PROGRESS
            )
        )
    )
    completion = result.scalar_one_or_none()
    
    if not completion:
        raise HTTPException(status_code=404, detail="No active task execution found")
    
    await db.delete(completion)
    await db.commit()
    
    # Broadcast to user
    await manager.send_to_user(current_user.id, {
        "type": "task_cancelled",
        "data": {
            "task_id": task_id
        }
    })
    
    return {"msg": "Task execution cancelled"}


# ==================== DASHBOARD ====================

@router.get("/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user dashboard with all relevant data"""
    
    # Balance
    balance = await PointsService.get_user_balance(db, current_user.id)
    
    # Stats - points earned
    earned_result = await db.execute(
        select(func.sum(PointsHistory.amount))
        .where(
            and_(
                PointsHistory.user_id == current_user.id,
                PointsHistory.amount > 0
            )
        )
    )
    total_earned = earned_result.scalar() or 0
    
    # Stats - points spent
    spent_result = await db.execute(
        select(func.sum(PointsHistory.amount))
        .where(
            and_(
                PointsHistory.user_id == current_user.id,
                PointsHistory.amount < 0
            )
        )
    )
    total_spent = abs(spent_result.scalar() or 0)
    
    # Active tasks (in progress)
    active_result = await db.execute(
        select(TaskCompletion)
        .options(joinedload(TaskCompletion.task))
        .where(
            and_(
                TaskCompletion.user_id == current_user.id,
                TaskCompletion.status == TaskStatus.IN_PROGRESS
            )
        )
    )
    active_completions = active_result.scalars().all()
    
    # Pending review tasks
    pending_result = await db.execute(
        select(TaskCompletion)
        .options(joinedload(TaskCompletion.task))
        .where(
            and_(
                TaskCompletion.user_id == current_user.id,
                TaskCompletion.status == TaskStatus.COMPLETED
            )
        )
    )
    pending_completions = pending_result.scalars().all()
    
    # Available tasks (active, not started)
    available_result = await db.execute(
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
    )
    available_tasks = available_result.scalars().all()
    
    # Get task IDs that user has already started/completed
    user_task_ids_result = await db.execute(
        select(TaskCompletion.task_id)
        .where(TaskCompletion.user_id == current_user.id)
    )
    user_task_ids = {r[0] for r in user_task_ids_result.all()}
    
    # Filter out started tasks
    truly_available = [t for t in available_tasks if t.id not in user_task_ids]
    
    # Count all completed tasks (not just recent 5)
    total_completed_result = await db.execute(
        select(func.count(TaskCompletion.id))
        .where(
            and_(
                TaskCompletion.user_id == current_user.id,
                TaskCompletion.status == TaskStatus.APPROVED
            )
        )
    )
    total_completed = total_completed_result.scalar() or 0
    
    # Count pending review tasks
    pending_count_result = await db.execute(
        select(func.count(TaskCompletion.id))
        .where(
            and_(
                TaskCompletion.user_id == current_user.id,
                TaskCompletion.status == TaskStatus.COMPLETED
            )
        )
    )
    pending_count = pending_count_result.scalar() or 0
    
    # Recent completed tasks (limit to 5 for display)
    recent_completed_result = await db.execute(
        select(TaskCompletion)
        .options(joinedload(TaskCompletion.task))
        .where(
            and_(
                TaskCompletion.user_id == current_user.id,
                TaskCompletion.status == TaskStatus.APPROVED
            )
        )
        .order_by(desc(TaskCompletion.completed_at))
        .limit(5)
    )
    recent_completed = recent_completed_result.scalars().all()
    
    # Available rewards
    rewards_result = await db.execute(
        select(Reward)
        .where(Reward.status == RewardStatus.ACTIVE)
        .order_by(Reward.cost)
    )
    available_rewards = rewards_result.scalars().all()
    
    # User's reward requests
    my_requests_result = await db.execute(
        select(RewardRequest)
        .options(joinedload(RewardRequest.reward))
        .where(RewardRequest.user_id == current_user.id)
        .order_by(desc(RewardRequest.created_at))
    )
    my_reward_requests = my_requests_result.scalars().all()
    
    # Unread notifications count
    notifications_result = await db.execute(
        select(func.count(Notification.id))
        .where(
            and_(
                Notification.user_id == current_user.id,
                Notification.is_read == False
            )
        )
    )
    unread_notifications = notifications_result.scalar() or 0
    
    # Recent notifications
    recent_notifications_result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(desc(Notification.created_at))
        .limit(5)
    )
    recent_notifications = recent_notifications_result.scalars().all()
    
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role.value
        },
        "balance": balance,
        "stats": {
            "total_earned": total_earned,
            "total_spent": total_spent,
            "tasks_completed": total_completed,
            "tasks_pending_review": pending_count,
            "active_tasks_count": len(active_completions),
            "unread_notifications": unread_notifications
        },
        "active_tasks": [
            {
                "completion_id": c.id,
                "task_id": c.task_id,
                "title": c.task.title if c.task else "Unknown",
                "description": c.task.description if c.task else "",
                "points": c.task.points if c.task else 0,
                "started_at": c.started_at.isoformat() + "Z" if c.started_at else None,
                "time_spent_so_far": int((datetime.utcnow() - c.started_at).total_seconds()) if c.started_at else 0
            }
            for c in active_completions
        ],
        "pending_review": [
            {
                "completion_id": c.id,
                "task_id": c.task_id,
                "title": c.task.title if c.task else "Unknown",
                "points": c.task.points if c.task else 0,
                "completed_at": c.completed_at.isoformat() if c.completed_at else None,
                "proof": c.proof,
                "time_spent": c.time_spent
            }
            for c in pending_completions
        ],
        "available_tasks": [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "type": t.type.value,
                "points": t.points,
                "requires_review": t.requires_review
            }
            for t in truly_available[:5]  # Limit to 5
        ],
        "recent_completed": [
            {
                "completion_id": c.id,
                "task_id": c.task_id,
                "title": c.task.title if c.task else "Unknown",
                "points_earned": c.points_awarded,
                "completed_at": c.completed_at.isoformat() if c.completed_at else None,
                "time_spent": c.time_spent
            }
            for c in recent_completed
        ],
        "available_rewards": [
            {
                "id": r.id,
                "title": r.title,
                "description": r.description,
                "cost": r.cost,
                "can_afford": balance >= r.cost
            }
            for r in available_rewards[:5]
        ],
        "my_reward_requests": [
            {
                "id": req.id,
                "reward_id": req.reward_id,
                "reward_title": req.reward.title if req.reward else "Unknown",
                "status": req.status,
                "points_spent": req.points_spent,
                "created_at": req.created_at.isoformat() if req.created_at else None
            }
            for req in my_reward_requests[:5]
        ],
        "notifications": [
            {
                "id": n.id,
                "type": n.type.value if n.type else None,
                "title": n.title,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None
            }
            for n in recent_notifications
        ]
    }


# ==================== NOTIFICATIONS ====================

@router.get("/notifications")
async def get_notifications(
    unread_only: bool = False,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user notifications"""
    query = select(Notification).where(Notification.user_id == current_user.id)
    
    if unread_only:
        query = query.where(Notification.is_read == False)
    
    query = query.order_by(desc(Notification.created_at)).limit(limit)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return [
        {
            "id": n.id,
            "type": n.type.value if n.type else None,
            "title": n.title,
            "message": n.message,
            "related_id": n.related_id,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None
        }
        for n in notifications
    ]


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark notification as read"""
    result = await db.execute(
        select(Notification)
        .where(
            and_(
                Notification.id == notification_id,
                Notification.user_id == current_user.id
            )
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    await db.commit()
    
    return {"msg": "Notification marked as read"}


@router.post("/notifications/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark all notifications as read"""
    await db.execute(
        select(Notification)
        .where(
            and_(
                Notification.user_id == current_user.id,
                Notification.is_read == False
            )
        )
    )
    
    # Update all unread to read
    from sqlalchemy import update
    await db.execute(
        update(Notification)
        .where(
            and_(
                Notification.user_id == current_user.id,
                Notification.is_read == False
            )
        )
        .values(is_read=True)
    )
    await db.commit()
    
    return {"msg": "All notifications marked as read"}
