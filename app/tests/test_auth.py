def test_authorization_header_missing(client):
    res = client.get("/api/v1/jobs")
    assert res.status_code == 401


def test_authorization_header_malformed(client):
    res = client.get("/api/v1/jobs", headers={"Authorization": "Bearer"})
    assert res.status_code == 401


def test_incorrect_api_key(client):
    res = client.get("/api/v1/jobs", headers={"Authorization": "Bearer incorrect"})
    assert res.status_code == 401


def test_existing_api_key(client, auth_headers):
    res = client.get("/api/v1/jobs", headers=auth_headers)
    assert res.status_code == 200
