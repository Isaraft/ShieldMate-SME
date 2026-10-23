from fastapi.testclient import TestClient


def test_health_contract(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"


def test_missing_business_endpoints(client: TestClient) -> None:
    for path in ["/api/v1/domains", "/api/v1/auth/login", "/api/v1/scans", "/docs"]:
        response = client.get(path)
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "http_404"


def test_method_not_allowed(client: TestClient) -> None:
    response = client.post("/api/v1/health")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "http_405"


def test_no_credentialed_or_permissive_cors(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"Origin": "https://untrusted.example"})
    assert "access-control-allow-origin" not in response.headers
    assert "access-control-allow-credentials" not in response.headers


def test_reject_unrecognized_host(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"Host": "untrusted.example"})
    assert response.status_code == 400
