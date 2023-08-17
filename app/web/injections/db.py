from functools import lru_cache
from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.shared.db.base import make_engine, make_session_local
from app.shared.settings import Settings
from app.web.injections.settings import get_settings


@lru_cache
def session_local(database_url: str):
    engine = make_engine(database_url)
    return make_session_local(engine)


def get_session_local(settings: Settings = Depends(get_settings)):
    return session_local(settings.DATABASE_URI)


def get_session(
    session_local=Depends(get_session_local),
) -> Generator[Session, None, None]:
    with session_local() as session:
        yield session
