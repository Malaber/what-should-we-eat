"""
test_users.py — User registration, login, and profile tests.
"""


class TestUserRegistration:
    def test_register_user(self, client):
        r = client.post("/users/register", json={
            "email": "new@test.com",
            "name": "New User",
            "password": "strongpassword",
        })
        assert r.status_code == 201
        body = r.json()
        assert body["email"] == "new@test.com"
        assert body["name"] == "New User"
        assert "password" not in body
        assert "hashed_password" not in body
        assert "personal_household_id" in body
        assert "active_household_id" in body
        assert body["personal_household_id"] == body["active_household_id"]

    def test_register_creates_household_membership(self, client):
        r = client.post("/users/register", json={
            "email": "member@test.com",
            "name": "Member",
            "password": "pw",
        })
        body = r.json()
        assert len(body["households"]) == 1
        assert body["households"][0]["household_id"] == body["personal_household_id"]

    def test_register_duplicate_email_returns_400(self, client):
        payload = {"email": "dup@test.com", "name": "Dup", "password": "pw"}
        client.post("/users/register", json=payload)
        r = client.post("/users/register", json=payload)
        assert r.status_code == 400
        assert "already registered" in r.json()["detail"]


class TestAuth:
    def test_login_returns_token(self, client):
        client.post("/users/register", json={
            "email": "login@test.com", "name": "Login", "password": "mypassword",
        })
        r = client.post("/users/token", data={
            "username": "login@test.com", "password": "mypassword",
        })
        assert r.status_code == 200
        assert "access_token" in r.json()
        assert r.json()["token_type"] == "bearer"

    def test_login_wrong_password_returns_401(self, client):
        client.post("/users/register", json={
            "email": "wrong@test.com", "name": "Wrong", "password": "correct",
        })
        r = client.post("/users/token", data={
            "username": "wrong@test.com", "password": "incorrect",
        })
        assert r.status_code == 401

    def test_login_nonexistent_user_returns_401(self, client):
        r = client.post("/users/token", data={
            "username": "ghost@test.com", "password": "anything",
        })
        assert r.status_code == 401


class TestCurrentUser:
    def test_me_authenticated(self, client, auth_headers):
        r = client.get("/users/me", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["email"] == "alice@test.com"

    def test_me_unauthenticated_returns_401(self, client):
        r = client.get("/users/me")
        assert r.status_code == 401

    def test_me_invalid_token_returns_401(self, client):
        r = client.get("/users/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert r.status_code == 401


def test_account_equipment_sync_and_legacy_import(client, auth_headers, second_user_headers):
    path = "/users/me/equipment"
    assert client.get(path).status_code == 401
    assert client.put(path, json={"changes": {"Knife": True}}).status_code == 401
    assert client.get(path, headers=auth_headers).json() == {"owned": []}
    update = client.put(path, headers=auth_headers, json={
        "changes": {" Springform  Pan ": True, "THERMOMIX": False},
        "legacy_owned": ["Thermomix", "Wooden spoon"],
    })
    assert update.json() == {"owned": ["springform pan", "wooden spoon"]}
    second_device = client.post("/users/token", data={
        "username": "alice@test.com", "password": "alice-password-123",
    }).json()["access_token"]
    other_device = {"Authorization": f"Bearer {second_device}"}
    assert client.get(path, headers=other_device).json() == update.json()
    assert client.get(path, headers=second_user_headers).json() == {"owned": []}
    assert client.put(path, headers=other_device, json={"changes": {"Springform pan": False}}).status_code == 200
    assert client.put(path, headers=auth_headers, json={"legacy_owned": ["SPRINGFORM PAN"]}).json() == {
        "owned": ["wooden spoon"],
    }
    assert client.put(path, headers=auth_headers, json={"changes": {"Knife": "false"}}).status_code == 422
    assert client.post("/users/me/delete", headers=auth_headers, json={"email": "alice@test.com"}).status_code == 204
    from execution.db.database import SessionLocal
    from execution.db.models import AccountEquipment

    with SessionLocal() as db:
        assert db.query(AccountEquipment).count() == 0
