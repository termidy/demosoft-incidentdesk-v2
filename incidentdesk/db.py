"""The database: one engine per process, a session per request."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from incidentdesk.config import settings


class Base(DeclarativeBase):
    pass


_engine = None


def engine():
    global _engine
    if _engine is None:
        url = settings().database_url
        if not url:
            raise RuntimeError("DATABASE_URL is not set")
        _engine = create_engine(url)
    return _engine


def session() -> Session:
    return sessionmaker(engine(), expire_on_commit=False)()


def get_session():
    """FastAPI dependency."""
    with session() as s:
        yield s
