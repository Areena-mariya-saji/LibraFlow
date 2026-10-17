import pytest


def test_health_endpoint(client):
    """Test the /health endpoint used by Docker/K8s liveness probes."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "LibraFlow Library Management System"
    assert "timestamp" in data


def test_csrf_protection_blocks_invalid_post(client):
    """Test that POST request with missing or incorrect CSRF token is rejected with 400."""
    response = client.post("/login", data={
        "identifier": "student1",
        "password": "Student@123",
        "csrf_token": "fraudulent_or_missing_token"
    })
    assert response.status_code == 400


def test_404_error_page(client):
    """Test custom 404 error handler."""
    response = client.get("/non-existent-route-xyz")
    assert response.status_code == 404
    assert b"Page Not Found" in response.data
