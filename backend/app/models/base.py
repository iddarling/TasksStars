import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Enum,
    ForeignKey,
    Boolean,
    DateTime,
    Float,
    Text,
)
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class TaskType(str, enum.Enum):
    DAILY = "daily"
    ONE_TIME = "one-time"


class TaskStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"  # Awaiting admin approval
    ACTIVE = "active"    # Approved and available for users
    IN_PROGRESS = "in_progress"  # User started the task
    COMPLETED = "completed"  # Finished, awaiting review (if required)
    APPROVED = "approved"  # Completion approved by admin
    REJECTED = "rejected"  # Rejected by admin


class RewardStatus(str, enum.Enum):
    PROPOSED = "proposed"
    ACTIVE = "active"


class NotificationType(str, enum.Enum):
    TASK_APPROVED = "task_approved"
    TASK_REJECTED = "task_rejected"
    COMPLETION_APPROVED = "completion_approved"
    COMPLETION_REJECTED = "completion_rejected"
    REWARD_APPROVED = "reward_approved"
    REWARD_REJECTED = "reward_rejected"
    DAILY_REMINDER = "daily_reminder"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Cached balance for fast retrieval
    cached_balance = Column(Integer, default=0, nullable=False)

    # Relationships
    completions = relationship("TaskCompletion", back_populates="user", lazy="dynamic")
    reward_requests = relationship("RewardRequest", back_populates="user", lazy="dynamic")
    points_history = relationship("PointsHistory", back_populates="user", lazy="dynamic")
    notifications = relationship("Notification", back_populates="user", lazy="dynamic")
    
    # Tasks suggested by this user
    suggested_tasks = relationship(
        "Task",
        foreign_keys="Task.suggested_by",
        back_populates="suggested_by_user",
        lazy="dynamic"
    )
    
    # Rewards suggested by this user
    suggested_rewards = relationship(
        "Reward",
        foreign_keys="Reward.suggested_by",
        back_populates="suggested_by_user",
        lazy="dynamic"
    )


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    type = Column(Enum(TaskType), nullable=False)
    points = Column(Integer, default=0)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)  # pending -> active
    
    # Who suggested this task (user or admin)
    suggested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who approved
    
    # Task settings
    requires_review = Column(Boolean, default=True)  # If True, admin must approve completions
    is_personal = Column(Boolean, default=False)  # If True, only visible to creator
    deadline = Column(DateTime, nullable=True)  # Optional deadline for the task
    
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    
    # Relationships
    suggested_by_user = relationship("User", foreign_keys=[suggested_by], back_populates="suggested_tasks")
    completions = relationship("TaskCompletion", back_populates="task", lazy="dynamic")


class TaskCompletion(Base):
    __tablename__ = "task_completions"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Timer and completion data
    started_at = Column(DateTime, nullable=True)  # When user pressed "Start"
    completed_at = Column(DateTime, nullable=True)  # When user pressed "Done"
    time_spent = Column(Integer, default=0)  # Time in seconds
    
    # Proof data
    proof = Column(Text)  # Text description
    proof_image_url = Column(String, nullable=True)  # URL to image if provided
    
    # Review status
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    admin_comment = Column(Text, nullable=True)  # Admin feedback on approval/rejection
    
    # Points
    points_awarded = Column(Integer, nullable=True)  # Actual points given
    
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Relationships
    task = relationship("Task", back_populates="completions")
    user = relationship("User", back_populates="completions")


class Reward(Base):
    __tablename__ = "rewards"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    cost = Column(Integer, nullable=False)
    status = Column(Enum(RewardStatus), default=RewardStatus.PROPOSED)
    
    # Who suggested this reward
    suggested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Personal vs shared reward
    is_personal = Column(Boolean, default=True)  # True = only visible to creator
    
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    
    # Relationships
    requests = relationship("RewardRequest", back_populates="reward", lazy="dynamic")
    suggested_by_user = relationship("User", foreign_keys=[suggested_by], back_populates="suggested_rewards")


class RewardRequest(Base):
    __tablename__ = "reward_requests"
    id = Column(Integer, primary_key=True)
    reward_id = Column(Integer, ForeignKey("rewards.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending")  # pending, approved, rejected
    admin_comment = Column(Text, nullable=True)
    points_spent = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Relationships
    reward = relationship("Reward", back_populates="requests")
    user = relationship("User", back_populates="reward_requests")


class PointsHistory(Base):
    __tablename__ = "points_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer, nullable=False)  # Positive for earned, negative for spent
    source = Column(String)  # e.g., "task_completion:123", "reward_redemption:456"
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="points_history")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(Enum(NotificationType))
    title = Column(String, nullable=False)
    message = Column(Text)
    related_id = Column(Integer, nullable=True)  # ID of related task/reward/etc
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="notifications")


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subscription_data = Column(String, nullable=False)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
