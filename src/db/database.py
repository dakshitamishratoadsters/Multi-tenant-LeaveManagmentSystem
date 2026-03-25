from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.core.config import config

DATABASE_URL = config.DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
)

async_session= sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session():
    async with async_session() as session:
        yield session
