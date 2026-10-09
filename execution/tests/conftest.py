"""
conftest.py — Shared pytest fixtures for unit tests.

Sets DATABASE_URL=sqlite:// before any app code is imported, so database.py
creates an in-memory SQLite engine with StaticPool (all sessions share one DB).
"""

import os

# ── Must happen before any app import ────────────────────────────────
os.environ["ALLOW_LEGACY_PASSWORD_AUTH"] = "true"
os.environ["APP_BASE_URL"] = "http://localhost:8000"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-tests-minimum-32-bytes"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
os.environ["DEMO_HOUSEHOLD_ID"] = "99999"

import pytest
from sqlalchemy import event
from fastapi.testclient import TestClient

# Now import app code — database.py will see DATABASE_URL="sqlite://"
# and use StaticPool so all sessions share the same in-memory database.
from execution.db.database import Base, engine
from execution.api.main import app


# Enable SQLite foreign key enforcement (off by default)
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ── Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _reset_tables():
    """Create all tables before each test, drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    """FastAPI TestClient — uses the app as-is (already wired to SQLite)."""
    with TestClient(app) as c:
        yield c


# ── Auth helpers ─────────────────────────────────────────────────────

def _register_and_login(client: TestClient, email: str, name: str, password: str) -> dict:
    """Register a user and return Authorization headers."""
    r = client.post("/users/register", json={
        "email": email,
        "name": name,
        "password": password,
    })
    assert r.status_code == 201, f"Registration failed: {r.text}"

    r = client.post("/users/token", data={
        "username": email,
        "password": password,
    })
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def auth_headers(client) -> dict:
    """Register 'alice@test.com' and return auth headers."""
    return _register_and_login(client, "alice@test.com", "Alice", "alice-password-123")


@pytest.fixture()
def second_user_headers(client) -> dict:
    """Register 'bob@test.com' and return auth headers."""
    return _register_and_login(client, "bob@test.com", "Bob", "bob-password-456")
