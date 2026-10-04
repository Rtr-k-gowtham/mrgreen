"""
MR.GREEN — Database Session Management

Provides async SQLAlchemy engine and session factory.
All database access flows through get_db_session().
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.is_development,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields a database session and handles cleanup."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables and apply incremental column migrations."""
    from app.database.models import Base
    from sqlalchemy import text

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Automatic schema synchronization for incremental columns added across milestones
        migrations = [
            "ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS goal TEXT;",
            "ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS current_step INTEGER DEFAULT 0;",
            "ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS total_steps INTEGER DEFAULT 0;",
            "ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS iterations INTEGER DEFAULT 0;",
            "ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS trigger_message_id VARCHAR(26);",
            "ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS error_message TEXT;",
            "ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';",
            "ALTER TABLE agent_steps ADD COLUMN IF NOT EXISTS input_data JSONB DEFAULT '{}';",
            "ALTER TABLE agent_steps ADD COLUMN IF NOT EXISTS output_data JSONB DEFAULT '{}';",
            "ALTER TABLE agent_steps ADD COLUMN IF NOT EXISTS tool_name VARCHAR(100);",
            "ALTER TABLE agent_steps ADD COLUMN IF NOT EXISTS success BOOLEAN;",
            "ALTER TABLE agent_steps ADD COLUMN IF NOT EXISTS duration_ms INTEGER;",
        ]

        for stmt in migrations:
            try:
                await conn.execute(text(stmt))
            except Exception:
                pass


async def close_db() -> None:
    """Dispose of the engine connection pool."""
    await engine.dispose()
