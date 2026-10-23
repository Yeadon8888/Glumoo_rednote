"""Health endpoint regression tests for Railway deployments."""


def test_health_reports_api_and_storage(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["status"] == "healthy"
    assert payload["version"] == "1.4.3-glumoo"
    assert payload["checks"]["api"] == "ok"
    assert payload["checks"]["storage"] == "ok"
    assert payload["checks"]["storage_free_mb"] >= 0
