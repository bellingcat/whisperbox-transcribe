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


@pytest.fixture(scope="function")
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.API_SECRET}"}


@pytest.fixture(scope="function", autouse=True)
def db_session():
    models.Base.metadata.create_all(engine)
    connection = engine.connect()

    with SessionLocal(bind=connection) as session:
        yield session
        connection.close()

    models.Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    app = app_factory(lambda: db_session)
    client = TestClient(app)
    return client


@pytest.fixture(scope="function", autouse=False)
def mock_job(db_session):
    job = models.Job(
        url="https://example.com",
        type=models.JobType.transcript,
        status=models.JobStatus.create,
    )
    db_session.add(job)
    db_session.flush()
    return job


@pytest.fixture(scope="function", autouse=False)
def mock_artifact(db_session, mock_job):
    artifact = models.Artifact(
        data=None, job_id=str(mock_job.id), type=models.ArtifactType.raw_transcript
    )
    db_session.add(artifact)
    db_session.flush()
    return artifact


@pytest.fixture(scope="function")
def sharing_enabled():
    settings.ENABLE_SHARING = True
    yield
    settings.ENABLE_SHARING = False
