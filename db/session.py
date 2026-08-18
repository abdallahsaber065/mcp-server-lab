"""
Async-First Database Session Management & Concurrency Configuration (db/session.py)
Supports SQLite (with WAL mode & busy_timeout concurrency) and seamless PostgreSQL production deployment.
"""

import os
import logging
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine, event
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from db.models import Base

# Automatically load .env file if present
load_dotenv(override=False)

logger = logging.getLogger("db.session")

# 1. Resolve Raw Database URL or Default SQLite Path
DEFAULT_DB_FILE = os.path.join(os.path.dirname(__file__), "realty_mcp.db")
RAW_DB_URL = os.getenv("DATABASE_URL") or os.getenv("MCP_DB_FILE") or DEFAULT_DB_FILE

# 2. Format URLs for Async & Sync Drivers
if RAW_DB_URL.startswith("postgres://") or RAW_DB_URL.startswith("postgresql://") or RAW_DB_URL.startswith("postgresql+"):
    # Production PostgreSQL
    CLEAN_URL = RAW_DB_URL.replace("postgres://", "postgresql://", 1)
    if "+asyncpg" in CLEAN_URL:
        ASYNC_DATABASE_URL = CLEAN_URL
        SYNC_DATABASE_URL = CLEAN_URL.replace("+asyncpg", "", 1)
    elif "+psycopg2" in CLEAN_URL:
        SYNC_DATABASE_URL = CLEAN_URL
        ASYNC_DATABASE_URL = CLEAN_URL.replace("+psycopg2", "+asyncpg", 1)
    else:
        SYNC_DATABASE_URL = CLEAN_URL
        ASYNC_DATABASE_URL = CLEAN_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    IS_SQLITE = False
elif RAW_DB_URL.startswith("sqlite"):
    if "sqlite+aiosqlite" in RAW_DB_URL:
        ASYNC_DATABASE_URL = RAW_DB_URL
        SYNC_DATABASE_URL = RAW_DB_URL.replace("sqlite+aiosqlite://", "sqlite://", 1)
    else:
        SYNC_DATABASE_URL = RAW_DB_URL
        ASYNC_DATABASE_URL = RAW_DB_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)
    IS_SQLITE = True
else:
    # File path given directly
    normalized_path = os.path.abspath(RAW_DB_URL).replace("\\", "/")
    SYNC_DATABASE_URL = f"sqlite:///{normalized_path}"
    ASYNC_DATABASE_URL = f"sqlite+aiosqlite:///{normalized_path}"
    IS_SQLITE = True

def get_db_url(is_async: bool = False) -> str:
    """Retrieve formatted async or sync database URL."""
    return ASYNC_DATABASE_URL if is_async else SYNC_DATABASE_URL

logger.info("DB Engine initialized. IS_SQLITE: %s | Async URL: %s", IS_SQLITE, ASYNC_DATABASE_URL.split("@")[-1])

# 3. Create Async Engine & Async SessionMaker
if IS_SQLITE:
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 15},
        echo=False
    )
    sync_engine = create_engine(
        SYNC_DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 15},
        echo=False
    )

    # Enable WAL mode & concurrency pragmas on SQLite connections
    @event.listens_for(sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

else:
    # PostgreSQL production configuration
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        poolclass=NullPool,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False
    )
    sync_engine = create_engine(
        SYNC_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False
    )

# Session factories
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


# 4. Initialization & Dependency Injection
async def init_async_db():
    """Create all ORM tables asynchronously."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if IS_SQLITE:
            # Set WAL mode asynchronously
            await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
            await conn.exec_driver_sql("PRAGMA busy_timeout=5000;")


def init_sync_db():
    """Create all ORM tables synchronously."""
    Base.metadata.create_all(bind=sync_engine)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI async dependency yielding an AsyncSession."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_db() -> Generator[Session, None, None]:
    """Sync context manager / dependency yielding a Session."""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()
