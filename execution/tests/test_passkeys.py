import base64
import hashlib
import secrets
from datetime import timedelta
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest
from fastpasskey import FastPasskey

from execution.api.routers import passkeys
from execution.db.database import SessionLocal
from execution.db.models import User
from execution.db.passkeys import AuthFlow, Passkey

ORIGIN = {"Origin": "http://localhost:8000"}


@pytest.fixture
def verified_registration(monkeypatch):
    monkeypatch.setattr(FastPasskey, "verify_registration", lambda *args, **kwargs: SimpleNamespace(
        credential_id=b"test-credential", credential_public_key=b"public-key", sign_count=0))


def register(client):
    options = client.post("/auth/register/options", headers=ORIGIN,
                          json={"email": "chef@example.com", "display_name": "Chef"})
    assert options.status_code == 200
    assert options.json()["authenticatorSelection"]["userVerification"] == "required"
    return client.post("/auth/register/verify", headers=ORIGIN, json={"credential": {"id": "test"}})


def test_default_disables_password_endpoints(client, monkeypatch):
    monkeypatch.delenv("ALLOW_LEGACY_PASSWORD_AUTH")
    assert client.post("/users/token", data={"username": "a", "password": "b"}).status_code == 410
    assert client.post("/users/register", json={"email": "a@example.com", "password": "secret"}).status_code == 410


def test_registration_creates_kitchen_and_cannot_replay(client, verified_registration):
    response = register(client)
    assert response.status_code == 200
    profile = client.get("/users/me", headers={"Authorization": "Bearer " + response.json()["access_token"]})
    assert profile.status_code == 200
    assert profile.json()["is_admin"] is False
    assert len(profile.json()["households"]) == 1
    assert client.post("/auth/register/verify", headers=ORIGIN, json={"credential": {}}).status_code == 401
    with SessionLocal() as db:
        assert db.query(Passkey).count() == 1
        assert db.query(User).one().hashed_password == "!passkey-only"


def test_cross_origin_and_missing_origin_rejected(client):
    assert client.post("/auth/login/options", json={}).status_code == 403
    assert client.post("/auth/login/options", headers={"Origin": "https://evil.example"}, json={}).status_code == 403
    assert client.post("/auth/logout", headers={"Origin": "https://evil.example"}).status_code == 403


def test_invalid_webauthn_proof_fails_and_consumes_ceremony(client):
    assert client.post("/auth/register/options", headers=ORIGIN,
        json={"email": "chef@example.com", "display_name": "Chef"}).status_code == 200
    cookie = client.cookies.get(passkeys.FLOW_COOKIE)
    assert client.post("/auth/register/verify", headers=ORIGIN, json={"credential": {"id": "bad"}}).status_code == 400
    client.cookies.set(passkeys.FLOW_COOKIE, cookie)
    assert client.post("/auth/register/verify", headers=ORIGIN, json={"credential": {"id": "bad"}}).status_code == 401


def mobile_code(client, challenge):
    response = client.get("/auth/mobile/authorize", params={"state": "s" * 43, "code_challenge": challenge}, follow_redirects=False)
    assert response.status_code == 303
    url = urlsplit(response.headers["location"])
    assert url.scheme == "de.malaber.onionary" and url.netloc == "auth"
    values = parse_qs(url.query)
    assert values["state"] == ["s" * 43]
    assert "access_token" not in values
    return values["code"][0]


def test_mobile_pkce_exchange_replay_and_revocation(client, verified_registration):
    assert register(client).status_code == 200
    verifier = secrets.token_urlsafe(32)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    code = mobile_code(client, challenge)
    body = {"code": code, "code_verifier": verifier}
    response = client.post("/auth/mobile/token", json=body)
    assert response.status_code == 200
    headers = {"Authorization": "Bearer " + response.json()["access_token"]}
    assert client.get("/recipes", headers=headers).status_code == 200
    assert client.post("/auth/mobile/token", json=body).status_code == 401
    assert client.post("/auth/mobile/logout", headers=headers).status_code == 204
    assert client.get("/recipes", headers=headers).status_code == 401


def test_wrong_pkce_and_expired_code_fail(client, verified_registration):
    register(client)
    code = mobile_code(client, "c" * 43)
    assert client.post("/auth/mobile/token", json={"code": code, "code_verifier": "v" * 43}).status_code == 401
    code = mobile_code(client, "c" * 43)
    with SessionLocal() as db:
        db.query(AuthFlow).filter_by(token_hash=passkeys.digest(code)).update({"expires_at": passkeys.now() - timedelta(seconds=1)})
        db.commit()
    assert client.post("/auth/mobile/token", json={"code": code, "code_verifier": "v" * 43}).status_code == 401


def test_inactive_user_cannot_exchange_code(client, verified_registration):
    register(client)
    verifier = "v" * 43
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    code = mobile_code(client, challenge)
    with SessionLocal() as db:
        db.query(User).update({"is_active": False}); db.commit()
    assert client.post("/auth/mobile/token", json={"code": code, "code_verifier": verifier}).status_code == 401


def test_enrollment_preserves_existing_account_and_is_single_use(client, auth_headers, verified_registration):
    profile = client.get("/users/me", headers=auth_headers).json()
    with SessionLocal() as db:
        token = passkeys.save_flow(db, "enrollment", {"user_id": profile["id"]})
    assert client.post("/auth/enroll/options", headers=ORIGIN, json={"token": token}).status_code == 200
    assert client.post("/auth/enroll/options", headers=ORIGIN, json={"token": token}).status_code == 200
    response = client.post("/auth/enroll/verify", headers=ORIGIN, json={"credential": {}})
    assert response.status_code == 200
    assert client.post("/auth/enroll/options", headers=ORIGIN, json={"token": token}).status_code == 401
    headers = {"Authorization": "Bearer " + response.json()["access_token"]}
    assert client.get("/users/me", headers=headers).json()["id"] == profile["id"]


def test_login_verifies_and_updates_counter(client, verified_registration, monkeypatch):
    register(client)
    monkeypatch.setattr(FastPasskey, "verify_authentication", lambda *args, **kwargs: SimpleNamespace(new_sign_count=1))
    assert client.post("/auth/login/options", headers=ORIGIN, json={}).status_code == 200
    credential = {"id": base64.urlsafe_b64encode(b"test-credential").decode().rstrip("=")}
    assert client.post("/auth/login/verify", headers=ORIGIN, json={"credential": credential}).status_code == 200
    with SessionLocal() as db:
        assert db.query(Passkey).one().sign_count == 1
    assert client.post("/auth/login/verify", headers=ORIGIN, json={"credential": credential}).status_code == 401


def test_mobile_authorization_requires_login_and_fixed_callback(client):
    response = client.get("/auth/mobile/authorize", params={"state": "s" * 43, "code_challenge": "c" * 43,
        "redirect_uri": "https://evil.example"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/auth/login?")
    assert "evil" not in response.headers["location"]
    assert client.get("/auth/mobile/authorize?state=bad&code_challenge=bad").status_code == 422


def test_existing_email_cannot_be_taken_over(client, auth_headers, verified_registration):
    client.post("/auth/register/options", headers=ORIGIN, json={"email": "alice@test.com", "display_name": "Imposter"})
    response = client.post("/auth/register/verify", headers=ORIGIN, json={"credential": {}})
    assert response.status_code == 400
    with SessionLocal() as db:
        assert db.query(Passkey).count() == 0
