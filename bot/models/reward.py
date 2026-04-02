from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Reward(Base):
    __tablename__ = 'rewards'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    cost: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='proposed')
    proposed_by: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.telegram_id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    requests: Mapped[list['RewardRequest']] = relationship('RewardRequest', back_populates='reward')


class RewardRequest(Base):
    __tablename__ = 'reward_requests'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    reward_id: Mapped[int] = mapped_column(ForeignKey('rewards.id'), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.telegram_id'), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='pending')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    reward: Mapped[Reward] = relationship('Reward', back_populates='requests')
