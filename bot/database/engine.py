from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from bot.models import Base


async def init_db(database_config):
    engine = create_async_engine(database_config.url)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    return engine


def get_session(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
