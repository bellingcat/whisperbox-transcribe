import pytest
from fastapi.testclient import TestClient
from sqlalchemy_utils import create_database, database_exists, drop_database

import app.shared.db.models as models
from app.shared.db.base import SessionLocal, engine
from app.shared.settings import settings
from app.web.main import app_factory


def pytest_configure() -> None:
    if not database_exists(engine.url):
        create_database(engine.url)


def pytest_unconfigure() -> None:
    if database_exists(engine.url):
        drop_database(engine.url)


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.API_SECRET}"}


@pytest.fixture()
def test_db():
    models.Base.metadata.create_all(engine)
    connection = engine.connect()
    yield connection
    connection.close()
    models.Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(test_db):
    with SessionLocal(bind=test_db) as session:
        yield session


@pytest.fixture()
def client(db_session):
    app = app_factory(lambda: db_session)
    client = TestClient(app)
    return client


@pytest.fixture()
def mock_job(db_session):
    job = models.Job(
        url="https://example.com",
        type=models.JobType.transcript,
        status=models.JobStatus.processing,
        meta={"task_id": "5c790c76-2cc1-4e91-a305-443df55a4a4c"},
    )
    db_session.add(job)
    db_session.commit()
    return job


@pytest.fixture()
def mock_artifact(db_session, mock_job):
    artifact = models.Artifact(
        data=None, job_id=str(mock_job.id), type=models.ArtifactType.raw_transcript
    )
    db_session.add(artifact)
    db_session.commit()
    return artifact


@pytest.fixture()
def sharing_enabled():
    settings.ENABLE_SHARING = True
    yield
    settings.ENABLE_SHARING = False
