from .user import register_user_handlers
from .task import register_task_handlers
from .reward import register_reward_handlers
from .admin import register_admin_handlers


def register_handlers(dp):
    register_user_handlers(dp)
    register_task_handlers(dp)
    register_reward_handlers(dp)
    register_admin_handlers(dp)
