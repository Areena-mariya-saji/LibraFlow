import pytest
from tests.conftest import get_csrf_token


def test_homepage_loads(client):
    """Test that the homepage loads successfully with HTTP 200."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"LibraFlow" in response.data
    assert b"Featured Catalog Books" in response.data


def test_registration_works(client):
    """Test that a new member can register successfully."""
    csrf = get_csrf_token(client)
    response = client.post("/register", data={
        "csrf_token": csrf,
        "full_name": "Test Student",
        "username": "teststudent",
        "email": "teststudent@college.edu",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Registration successful" in response.data


def test_registration_rejects_duplicate_user(client):
    """Test that duplicate registration with same username or email is rejected."""
    csrf = get_csrf_token(client)
    response = client.post("/register", data={
        "csrf_token": csrf,
        "full_name": "Duplicate Student",
        "username": "student1",  # already exists
        "email": "diff@college.edu",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"already exists" in response.data


def test_login_and_logout_works(client):
    """Test login with valid credentials and subsequent logout."""
    csrf = get_csrf_token(client)
    login_res = client.post("/login", data={
        "csrf_token": csrf,
        "identifier": "student1",
        "password": "Student@123"
    }, follow_redirects=True)

    assert login_res.status_code == 200
    assert b"Welcome back" in login_res.data

    logout_res = client.get("/logout", follow_redirects=True)
    assert logout_res.status_code == 200
    assert b"safely logged out" in logout_res.data


def test_invalid_password_rejected(client):
    """Test that wrong password fails authentication."""
    csrf = get_csrf_token(client)
    response = client.post("/login", data={
        "csrf_token": csrf,
        "identifier": "student1",
        "password": "WrongPassword999"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Invalid credentials" in response.data


def test_unauthorized_access_blocked(client, member1_client):
    """Test that members cannot access the admin dashboard (HTTP 403)."""
    response = member1_client.get("/admin/dashboard")
    assert response.status_code == 403
    assert b"Forbidden" in response.data or b"Access denied" in response.data
