import os
import sys
import tempfile
from pathlib import Path
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db import init_db, get_db
from database.seed_data import seed
from app import create_app


@pytest.fixture(scope="session")
def app_instance():
    # Create temporary database file for the test session
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    os.environ["FLASK_ENV"] = "testing"
    os.environ["DATABASE_PATH"] = db_path
    os.environ["SECRET_KEY"] = "test-secret-key-libraflow-999"

    # Seed the test database
    seed(db_path)

    app = create_app("testing")
    app.config["DATABASE_PATH"] = db_path
    app.config["TESTING"] = True

    yield app

    # Cleanup temporary test database file
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def get_csrf_token(client):
    """Utility to extract CSRF token from session."""
    with client.session_transaction() as sess:
        if "_csrf_token" not in sess:
            sess["_csrf_token"] = "test-csrf-token-123456"
        return sess["_csrf_token"]


@pytest.fixture
def admin_client(app_instance, client):
    conn = get_db(app_instance.config["DATABASE_PATH"])
    user = conn.execute("SELECT id, username, full_name, role FROM users WHERE username = 'admin'").fetchone()
    with client.session_transaction() as sess:
        sess["user_id"] = user["id"]
        sess["username"] = user["username"]
        sess["full_name"] = user["full_name"]
        sess["role"] = user["role"]
        sess["_csrf_token"] = "test-csrf-token-123456"
    return client


@pytest.fixture
def member1_client(app_instance, client):
    conn = get_db(app_instance.config["DATABASE_PATH"])
    user = conn.execute("SELECT id, username, full_name, role FROM users WHERE username = 'student1'").fetchone()
    with client.session_transaction() as sess:
        sess["user_id"] = user["id"]
        sess["username"] = user["username"]
        sess["full_name"] = user["full_name"]
        sess["role"] = user["role"]
        sess["_csrf_token"] = "test-csrf-token-123456"
    return client


@pytest.fixture
def member2_client(app_instance, client):
    conn = get_db(app_instance.config["DATABASE_PATH"])
    user = conn.execute("SELECT id, username, full_name, role FROM users WHERE username = 'student2'").fetchone()
    with client.session_transaction() as sess:
        sess["user_id"] = user["id"]
        sess["username"] = user["username"]
        sess["full_name"] = user["full_name"]
        sess["role"] = user["role"]
        sess["_csrf_token"] = "test-csrf-token-123456"
    return client
