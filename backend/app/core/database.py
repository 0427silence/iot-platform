from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

_engine_kwargs: dict = {
    "echo": settings.DB_ECHO,
    "pool_size": settings.DB_POOL_SIZE,
    "pool_recycle": settings.DB_POOL_RECYCLE,
}

if settings.DB_SSL:
    _engine_kwargs["connect_args"] = {"ssl": True}

engine = create_async_engine(settings.database_url, **_engine_kwargs)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
