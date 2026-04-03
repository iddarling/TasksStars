from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.db.session import get_db
from app.models.base import Reward, RewardRequest, RewardStatus, User
from app.services.websocket import manager
from app.core.config import settings
from pydantic import BaseModel
from typing import List

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


class RewardCreate(BaseModel):
    title: str
    description: str
    cost: int


@router.get("/")
async def get_rewards(
    current_user: User = Depends(get_db_user),
    db: AsyncSession = Depends(get_db)
):
    """Get active rewards available to user (personal + shared public rewards)"""
    result = await db.execute(
        select(Reward)
        .where(
            and_(
                Reward.status == RewardStatus.ACTIVE,
                or_(
                    Reward.suggested_by == current_user.id,  # User's own rewards
                    Reward.is_personal == False  # Shared public rewards
                )
            )
        )
        .order_by(Reward.created_at.desc())
    )
    return result.scalars().all()


@router.post("/")
async def suggest_reward(
    reward_in: RewardCreate,
    current_user: User = Depends(get_db_user),
    db: AsyncSession = Depends(get_db)
):
    """Suggest a new reward (user initiated, admin approval needed)"""
    reward = Reward(
        title=reward_in.title,
        description=reward_in.description,
        cost=reward_in.cost,
        status=RewardStatus.PROPOSED,
        suggested_by=current_user.id,
        is_personal=True  # User-suggested rewards are personal by default
    )
    db.add(reward)
    await db.commit()
    
    # Broadcast to admins about new proposed reward
    await manager.broadcast({
        "type": "reward_suggested_by_user",
        "data": {
            "reward_id": reward.id,
            "title": reward.title,
            "suggested_by": current_user.id,
            "suggested_by_email": current_user.email,
            "cost": reward.cost,
            "status": "proposed"
        }
    })
    
    # Notify user
    await manager.send_to_user(current_user.id, {
        "type": "reward_suggested",
        "data": {
            "reward_id": reward.id,
            "title": reward.title,
            "status": "proposed"
        }
    })
    
    return reward


@router.post("/{reward_id}/redeem")
async def redeem_reward(
    reward_id: int,
    current_user: User = Depends(get_db_user),
    db: AsyncSession = Depends(get_db)
):
    """Request to redeem a reward"""
    from app.services.points import PointsService
    
    # Check reward exists and is active
    result = await db.execute(
        select(Reward).where(Reward.id == reward_id, Reward.status == RewardStatus.ACTIVE)
    )
    reward = result.scalar_one_or_none()
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found or not active")
    
    # Check user balance
    balance = await PointsService.get_user_balance(db, current_user.id)
    if balance < reward.cost:
        raise HTTPException(status_code=400, detail=f"Insufficient points. Need {reward.cost}, have {balance}")
    
    # Check for existing pending request
    existing = await db.execute(
        select(RewardRequest)
        .where(RewardRequest.reward_id == reward_id, RewardRequest.user_id == current_user.id, RewardRequest.status == "pending")
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already have a pending request for this reward")
    
    # Create redemption request
    request = RewardRequest(
        reward_id=reward_id,
        user_id=current_user.id,
        status="pending"
    )
    db.add(request)
    await db.commit()
    
    # Broadcast to admins about new reward request
    await manager.broadcast({
        "type": "reward_redemption_requested",
        "data": {
            "request_id": request.id,
            "reward_id": reward_id,
            "reward_title": reward.title,
            "user_id": current_user.id,
            "user_email": current_user.email,
            "points_required": reward.cost,
            "status": "pending"
        }
    })
    
    # Notify user
    await manager.send_to_user(current_user.id, {
        "type": "reward_redeemed",
        "data": {
            "request_id": request.id,
            "reward_id": reward_id,
            "reward_title": reward.title,
            "points_required": reward.cost,
            "current_balance": balance
        }
    })
    
    return {
        "msg": "Redemption request submitted",
        "request_id": request.id,
        "reward_title": reward.title,
        "points_required": reward.cost,
        "current_balance": balance
    }


@router.get("/my-requests")
async def get_my_reward_requests(
    current_user: User = Depends(get_db_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's reward requests with reward details"""
    from sqlalchemy.orm import joinedload
    result = await db.execute(
        select(RewardRequest)
        .options(joinedload(RewardRequest.reward))
        .where(RewardRequest.user_id == current_user.id)
    )
    requests = result.scalars().all()
    
    # Return with flat fields for frontend compatibility
    return [
        {
            "id": r.id,
            "reward_id": r.reward_id,
            "user_id": r.user_id,
            "status": r.status,
            "admin_comment": r.admin_comment,
            "points_spent": r.points_spent,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
            "reward_title": r.reward.title if r.reward else None,
            "reward_description": r.reward.description if r.reward else None,
            "reward_cost": r.reward.cost if r.reward else None,
            "reward": {
                "id": r.reward.id if r.reward else None,
                "title": r.reward.title if r.reward else None,
                "description": r.reward.description if r.reward else None,
                "cost": r.reward.cost if r.reward else None,
            } if r.reward else None
        }
        for r in requests
    ]
