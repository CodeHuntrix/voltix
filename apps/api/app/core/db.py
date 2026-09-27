from collections.abc import AsyncGenerator

from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()


_ALLOWED_ASYNCPG_KEYS = {
    "ssl",
    "timeout",
    "statement_cache_size",
    "command_timeout",
    "server_settings",
}


def _sanitize_db_url(raw_url: str) -> str:
    url = raw_url.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    parts = urlsplit(url)
    new_query = ""
    if parts.query:
        query_params = parse_qs(parts.query, keep_blank_values=True)
        sslmode = query_params.get("sslmode", [""])[0].lower()
        if sslmode and sslmode != "disable":
            query_params["ssl"] = ["require"]

        flat_query = []
        for k, v_list in query_params.items():
            if k in _ALLOWED_ASYNCPG_KEYS:
                for v in v_list:
                    flat_query.append((k, v))
        new_query = urlencode(flat_query)

    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, new_query, parts.fragment)
    )



engine = create_async_engine(
    _sanitize_db_url(settings.database_url),
    echo=False,
    pool_pre_ping=True,
)


SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
