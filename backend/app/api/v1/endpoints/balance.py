from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.base import User, PointsHistory
from app.services.points import PointsService
from app.api.v1.endpoints.rewards import get_db_user

router = APIRouter()


@router.get("/")
async def get_balance(current_user: User = Depends(get_db_user), db: AsyncSession = Depends(get_db)):
    balance = await PointsService.get_user_balance(db, current_user.id)
    return {"balance": balance}
