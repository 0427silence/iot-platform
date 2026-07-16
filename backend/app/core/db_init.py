"""Auto-create tables for SQLite mode on startup."""
from app.core.config import settings
from app.core.database import Base, engine


async def init_db() -> None:
    if settings.DB_TYPE != "sqlite":
        return
    import os
    os.makedirs("data", exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
