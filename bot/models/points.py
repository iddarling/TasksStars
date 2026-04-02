from datetime import datetime
from sqlalchemy import BigInteger, Integer, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PointsHistory(Base):
    __tablename__ = 'points_history'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)  # task_completion, reward_redemption
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
