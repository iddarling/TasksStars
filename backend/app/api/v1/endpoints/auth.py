from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.base import User, UserRole
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from pydantic import BaseModel, EmailStr
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register(request: Request, user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    body = await request.body()
    logger.info(f"Register attempt: {body.decode()}")
    
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        logger.warning(f"User already exists: {user_in.email}")
        raise HTTPException(status_code=400, detail="User already registered")

    # Check if this is the first user (make them admin)
    user_count_result = await db.execute(select(func.count(User.id)))
    user_count = user_count_result.scalar()
    
    # Create new user
    user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=UserRole.ADMIN if user_count == 0 else UserRole.USER,
    )
    db.add(user)
    await db.commit()
    
    role_msg = "Admin" if user.role == UserRole.ADMIN else "User"
    logger.info(f"Created {role_msg}: {user_in.email}")
    return {"msg": f"{role_msg} created successfully", "role": user.role.value}


@router.post("/login")
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalar_one_or_none()
    if not user:
        logger.warning(f"Login failed - user not found: {user_in.email}")
        raise HTTPException(status_code=400, detail="Invalid email or password")
    if not verify_password(user_in.password, user.password_hash):
        logger.warning(f"Login failed - wrong password: {user_in.email}")
        raise HTTPException(status_code=400, detail="Invalid email or password")

    access_token = create_access_token(user.id)
    logger.info(f"Login successful: {user_in.email}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "role": user.role},
    }
