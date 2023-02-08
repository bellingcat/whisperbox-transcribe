from typing import Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.shared.db.dtos as dtos
import app.shared.db.models as models
from app.shared.db.dtos import JobStatus, JobType
from app.web.main import app, celery

client = TestClient(app)

@pytest.fixture(name="mock_job", scope="function", autouse=False)
def mock_job(db_session: Session) -> models.Job:
    job = models.Job(
        url="https://example.com", type=JobType.transcript, status=JobStatus.create
    )

    db_session.add(job)
    db_session.flush()

    return job


# POST /api/v1/jobs
# ---
def test_create_job_pass(auth_headers: Dict[str, str]) -> None:
    res = client.post(
        "/api/v1/jobs",
        headers=auth_headers,
        json={"url": "https://example.com", "type": JobType.transcript},
    )
    assert res.status_code == 201
    assert isinstance(res.json()["id"], str)


def test_create_job_missing_body(auth_headers: Dict[str, str]) -> None:
    res = client.post("/api/v1/jobs", headers=auth_headers, json={})
    assert res.status_code == 422


def test_create_job_malformed_url(auth_headers: Dict[str, str]) -> None:
    res = client.post(
        "/api/v1/jobs",
        headers=auth_headers,
        json={"url": "example.com", "type": JobType.transcript},
    )
    assert res.status_code == 422


# GET /api/v1/jobs
# ---
def test_get_jobs_pass(auth_headers: Dict[str, str], mock_job: models.Job) -> None:
    res = client.get(
        "/api/v1/jobs?type=transcript",
        headers=auth_headers,
    )
    assert len(res.json()) == 1
    assert res.status_code == 200


# GET /api/v1/jobs/:id
# ---
def test_get_job_pass(auth_headers: Dict[str, str], mock_job: models.Job) -> None:
    res = client.get(
        f"/api/v1/jobs/{mock_job.id}",
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["id"] == str(mock_job.id)


def test_get_job_not_found(auth_headers: Dict[str, str], mock_job: models.Job) -> None:
    res = client.get(
        "/api/v1/jobs/c8ecf5ea-77cf-48a2-9ecd-199ef35e0ccb",
        headers=auth_headers,
    )
    assert res.status_code == 404


# GET /api/v1/jobs/:id/artifacts
# ---
def test_get_artifact_pass(
    auth_headers: Dict[str, str], db_session: Session, mock_job: models.Job
) -> None:
    artifact = models.Artifact(
        data=[], job_id=mock_job.id, type=dtos.ArtifactType.raw_transcript
    )

    db_session.add(artifact)
    db_session.flush()

    res = client.get(
        f"/api/v1/jobs/{mock_job.id}/artifacts",
        headers=auth_headers,
    )

    assert res.status_code == 200
    assert res.json()[0]["job_id"] == str(mock_job.id)
    assert res.json()[0]["id"] == str(artifact.id)


def test_get_artifact_not_found(
    auth_headers: Dict[str, str], mock_job: models.Job
) -> None:
    res = client.get(
        f"/api/v1/jobs/{mock_job.id}/artifacts",
        headers=auth_headers,
    )
    assert res.status_code == 404


# DELETE /api/v1/jobs
# ---
def test_delete_job_pass(
    auth_headers: Dict[str, str], mock_job: models.Job, db_session: Session
) -> None:
    res = client.delete(
        f"/api/v1/jobs/{mock_job.id}",
        headers=auth_headers,
    )
    assert db_session.query(models.Job).count() == 0
    assert res.status_code == 204
