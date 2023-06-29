from typing import Generator

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


def pytest_unconfigure() -> None:
    if database_exists(engine.url):
        drop_database(engine.url)


@pytest.fixture(scope="function")
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.API_SECRET}"}


@pytest.fixture(scope="function", autouse=True)
def db_session() -> Generator[Session, None, None]:
    models.Base.metadata.create_all(engine)

    connection = engine.connect()

    with SessionLocal(bind=connection) as session:
        app.dependency_overrides[get_session] = lambda: session
        yield session
        app.dependency_overrides.clear()
        connection.close()

    models.Base.metadata.drop_all(bind=engine)
