from app.models.base import Base
from app.db.session import engine
import asyncio


async def init_db():
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(init_db())
    print("Database tables created successfully!")
