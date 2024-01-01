import pytest
from fastapi.testclient import TestClient
from sqlalchemy_utils import create_database, database_exists, drop_database

import app.shared.db.models as models
from app.shared.db.base import make_engine, make_session_local
from app.shared.settings import Settings
from app.web.injections.db import get_session
from app.web.injections.settings import get_settings
from app.web.main import app_factory


@pytest.fixture()
def settings():
    return Settings(_env_file=".env.test")  # type: ignore


@pytest.fixture()
def auth_headers(settings) -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.API_SECRET}"}


@pytest.fixture()
def test_db(settings):
    engine = make_engine(settings.DATABASE_URI)

    if not database_exists(engine.url):
        create_database(engine.url)

    models.Base.metadata.create_all(engine)

    connection = engine.connect()
    yield connection
    connection.close()

    models.Base.metadata.drop_all(bind=engine)
    drop_database(engine.url)


@pytest.fixture()
def db_session(test_db):
    session_local = make_session_local(test_db)
    with session_local() as session:
        yield session


@pytest.fixture()
def app(db_session, settings):
    app = app_factory()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_session] = lambda: db_session
    return app


@pytest.fixture()
def client(app):
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
