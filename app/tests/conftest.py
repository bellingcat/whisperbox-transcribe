from typing import Dict, Generator

import pytest
from sqlalchemy.orm import Session
from sqlalchemy_utils import create_database, database_exists, drop_database

import app.shared.db.models as models
from app.shared.db.base import SessionLocal, engine, get_session
from app.shared.settings import settings
from app.web.main import app


def pytest_configure() -> None:
    if not database_exists(engine.url):
        create_database(engine.url)
        models.Base.metadata.create_all(engine)


def pytest_unconfigure() -> None:
    if database_exists(engine.url):
        drop_database(engine.url)


@pytest.fixture(name="auth_headers", scope="function")
def auth_header() -> Dict[str, str]:
    return {"Authorization": f"Bearer {settings.API_SECRET}"}


@pytest.fixture(name="db_session", scope="function", autouse=True)
def db_session() -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()

    with SessionLocal(bind=connection) as session:
        app.dependency_overrides[get_session] = lambda: session
        yield session
        app.dependency_overrides.clear()
        transaction.rollback()
        connection.close()
