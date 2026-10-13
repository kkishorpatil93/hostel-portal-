"""Tests for health check endpoint."""


def test_healthz_endpoint_healthy(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["database"] == "ok"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data
