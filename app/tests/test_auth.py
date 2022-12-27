from typing import Dict

from fastapi.testclient import TestClient

from app.db.models import Account
from app.main import app

client = TestClient(app)


def auth_header(s: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {s}"}


def test_authorization_header_missing() -> None:
    res = client.get("/api/v1")
    assert res.status_code == 401


def test_authorization_header_malformed() -> None:
    res = client.get("/api/v1", headers=auth_header("not_a_uuid"))
    assert res.status_code == 422


def test_inexistent_api_key(test_account: Account) -> None:
    res = client.get("/api/v1", headers=auth_header(str(test_account.id)))
    assert res.status_code == 401


def test_existing_api_key(test_account: Account) -> None:
    res = client.get("/api/v1", headers=auth_header(str(test_account.api_key)))
    assert res.status_code == 200
