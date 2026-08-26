from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def ensure_database() -> None:
    """Create the target MySQL database if it doesn't exist yet."""
    import aiomysql

    url = make_url(settings.database_url)
    dbname = url.database
    admin = await aiomysql.connect(
        host=url.host or "localhost",
        port=url.port or 3306,
        user=url.username,
        password=url.password,
    )
    try:
        async with admin.cursor() as cursor:
            await cursor.execute(
                "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA "
                "WHERE SCHEMA_NAME = %s",
                (dbname,),
            )
            exists = await cursor.fetchone()
            if not exists and dbname:
                await cursor.execute(
                    f"CREATE DATABASE `{dbname}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
    finally:
        admin.close()


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        yield session