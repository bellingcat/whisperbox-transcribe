from fastapi.testclient import TestClient

import app.shared.db.models as models
from app.web.main import app_factory


# POST /api/v1/jobs
# ---
def test_create_job_pass(client, auth_headers: dict[str, str]):
    res = client.post(
        "/api/v1/jobs",
        headers=auth_headers,
        json={"url": "https://example.com", "type": models.JobType.transcript},
    )
    assert res.status_code == 201
    assert isinstance(res.json()["id"], str)


def test_create_job_missing_body(client, auth_headers: dict[str, str]):
    res = client.post("/api/v1/jobs", headers=auth_headers, json={})
    assert res.status_code == 422


def test_create_job_malformed_url(client, auth_headers: dict[str, str]):
    res = client.post(
        "/api/v1/jobs",
        headers=auth_headers,
        json={"url": "example.com", "type": models.JobType.transcript},
    )
    assert res.status_code == 422


# GET /api/v1/jobs
# ---
def test_get_jobs_pass(client, auth_headers: dict[str, str], mock_job: models.Job):
    res = client.get(
        "/api/v1/jobs?type=transcribe",
        headers=auth_headers,
    )
    assert len(res.json()) == 1
    assert res.status_code == 200


# GET /api/v1/jobs/:id
# ---
def test_get_job_pass(client, auth_headers: dict[str, str], mock_job: models.Job):
    res = client.get(
        f"/api/v1/jobs/{mock_job.id}",
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["id"] == str(mock_job.id)


def test_get_job_not_found(client, auth_headers: dict[str, str], mock_job):
    res = client.get(
        "/api/v1/jobs/c8ecf5ea-77cf-48a2-9ecd-199ef35e0ccb",
        headers=auth_headers,
    )

    assert res.status_code == 404


def test_get_job_sharing_disabled(client, mock_job):
    res = client.get(
        f"/api/v1/jobs/{mock_job.id}",
        headers={},
    )
    assert res.status_code == 401


def test_get_job_sharing_enabled(db_session, mock_job, sharing_enabled):
    # HACK: delay construction until settings are patched.
    client = TestClient(app_factory(lambda: db_session))

    res = client.get(
        f"/api/v1/jobs/{mock_job.id}",
        headers={},
    )

    assert res.status_code == 200


# GET /api/v1/jobs/:id/artifacts
# ---
def test_get_artifacts_pass(client, auth_headers, db_session, mock_job, mock_artifact):
    res = client.get(
        f"/api/v1/jobs/{mock_job.id}/artifacts",
        headers=auth_headers,
    )

    assert res.status_code == 200
    assert res.json()[0]["job_id"] == str(mock_job.id)
    assert res.json()[0]["id"] == str(mock_artifact.id)


def test_get_artifacts_not_found(client, auth_headers, mock_job):
    res = client.get(
        f"/api/v1/jobs/{mock_job.id}/artifacts",
        headers=auth_headers,
    )

    assert len(res.json()) == 0
    assert res.status_code == 200


# DELETE /api/v1/jobs
# ---
def test_delete_job_pass(client, auth_headers, mock_job, db_session):
    res_job = client.get(
        f"/api/v1/jobs/{mock_job.id}",
        headers=auth_headers,
    )

    assert res_job.status_code == 200

    client.delete(
        f"/api/v1/jobs/{mock_job.id}",
        headers=auth_headers,
    )

    # HACK: this catches a missed .commit().
    # TODO: clean up pytest database handling.
    db_session.rollback()

    res_job_missing = client.get(
        f"/api/v1/jobs/{mock_job.id}",
        headers=auth_headers,
    )

    assert res_job_missing.status_code == 404
