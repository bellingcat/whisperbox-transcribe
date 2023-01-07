from typing import Dict

from fastapi.testclient import TestClient

from app.shared.config import settings
from app.web.main import app

client = TestClient(app)


def auth_header(s: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {s}"}


def test_authorization_header_missing() -> None:
    res = client.get("/api/v1")
    assert res.status_code == 401


def test_authorization_header_malformed() -> None:
    res = client.get("/api/v1", headers={"Authorization": "Bearer"})
    assert res.status_code == 422


def test_incorrect_api_key() -> None:
    res = client.get("/api/v1", headers=auth_header("not_valid"))
    assert res.status_code == 401


def test_existing_api_key() -> None:
    res = client.get("/api/v1", headers=auth_header(settings.API_SECRET))
    assert res.status_code == 200
