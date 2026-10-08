"""Onionary passkeys using the same fastpasskey library as Planini and Tracy.

Only opaque random tokens enter cookies or native callbacks. Ceremonies and PKCE
codes are atomically consumed in SQL, so replay protection works across workers.
"""
import base64
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastpasskey import FastPasskey, PasskeyUser
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from webauthn.helpers import bytes_to_base64url

from execution.api.auth import create_access_token, get_current_active_user
from execution.db.database import get_db
from execution.db.models import User, Household, HouseholdMember, generate_unique_invite_code
from execution.db.passkeys import AuthFlow, AuthSession, Passkey

router = APIRouter(prefix="/auth", tags=["passkeys"])
COOKIE = "onionary_session"
FLOW_COOKIE = "onionary_ceremony"


def now():
    return datetime.now(timezone.utc)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def origin():
    value = os.getenv("APP_BASE_URL", "http://localhost:8000").rstrip("/")
    parts = urlsplit(value)
    if (parts.scheme != "https" and not (parts.scheme == "http" and parts.hostname == "localhost")) or parts.path or parts.query or parts.fragment or parts.username:
        raise HTTPException(503, "Configure APP_BASE_URL as the public HTTPS origin.")
    return value


def service():
    return FastPasskey(rp_name="Onionary", rp_id=urlsplit(origin()).hostname, origin=origin())


def same_origin(request: Request):
    # JSON endpoints are same-origin only, including browser session revocation.
    if request.headers.get("origin") != origin():
        raise HTTPException(403, "Untrusted origin")


def save_flow(db, kind, payload, lifetime=300):
    db.execute(delete(AuthFlow).where(AuthFlow.expires_at <= now()))
    token = secrets.token_urlsafe(32)
    db.add(AuthFlow(token_hash=digest(token), kind=kind, payload=payload,
                    expires_at=now() + timedelta(seconds=lifetime)))
    db.commit()
    return token


def take_flow(db, token, kind):
    payload = db.execute(delete(AuthFlow).where(
        AuthFlow.token_hash == digest(token), AuthFlow.kind == kind,
        AuthFlow.expires_at > now()).returning(AuthFlow.payload)).scalar_one_or_none()
    db.commit()
    if payload is None:
        raise HTTPException(401, "Sign-in expired. Please try again.")
    return payload


def set_cookie(response, name, token, seconds):
    response.set_cookie(name, token, max_age=seconds, httponly=True,
                        secure=origin().startswith("https:"), samesite="strict", path="/auth")
    response.headers["Cache-Control"] = "no-store"


def session_user(request, db):
    token = request.cookies.get(COOKIE, "")
    session = db.query(AuthSession).filter(AuthSession.token_hash == digest(token), AuthSession.expires_at > now()).first()
    user = db.get(User, session.user_id) if session else None
    if not user or not user.is_active:
        raise HTTPException(401, "Sign in with a passkey")
    return user


def authenticate(user, response, db, request):
    if not user.is_active:
        raise HTTPException(401, "Account inactive")
    db.execute(delete(AuthSession).where(AuthSession.token_hash == digest(request.cookies.get(COOKIE, ""))))
    db.execute(delete(AuthSession).where(AuthSession.expires_at <= now()))
    token = secrets.token_urlsafe(32)
    db.add(AuthSession(token_hash=digest(token), user_id=user.id, expires_at=now() + timedelta(days=30)))
    db.commit()
    set_cookie(response, COOKIE, token, 30 * 86400)
    response.delete_cookie(FLOW_COOKIE, path="/auth")
    return {"access_token": create_access_token({"sub": user.email, "sid": digest(token)}), "token_type": "bearer"}


class Registration(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=255)


class Finish(BaseModel):
    credential: dict


@router.get("/assets/fastpasskey.js", include_in_schema=False)
def browser_library():
    return Response(files("fastpasskey").joinpath("static/fastpasskey.js").read_text(), media_type="text/javascript")


@router.get("/login", include_in_schema=False)
def login_page():
    return FileResponse(Path(__file__).parents[3] / "frontend/passkey.html", headers={
        "Cache-Control": "no-store", "Referrer-Policy": "no-referrer",
        "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'"})


@router.post("/register/options", dependencies=[Depends(same_origin)])
def register_options(body: Registration, request: Request, response: Response, db: Session = Depends(get_db)):
    handle = secrets.token_bytes(32)
    start = service().begin_registration(user=PasskeyUser(id=handle, name=str(body.email), display_name=body.display_name),
        request_host=None, request_base_url=origin(), state_payload={"email": str(body.email), "name": body.display_name})
    token = save_flow(db, "register", start.state)
    set_cookie(response, FLOW_COOKIE, token, 300)
    return start.options


@router.post("/register/verify", dependencies=[Depends(same_origin)])
def register_verify(body: Finish, request: Request, response: Response, db: Session = Depends(get_db)):
    state = take_flow(db, request.cookies.get(FLOW_COOKIE, ""), "register")
    try:
        result = service().verify_registration(credential=body.credential, state=state)
    except Exception as exc:
        raise HTTPException(400, "Passkey registration failed") from exc
    if db.query(User).filter(User.email == state["email"]).first():
        raise HTTPException(400, "Account already exists. Sign in or ask your administrator for an enrollment link.")
    household = Household(name=f"{state['name']}'s Kitchen", invite_code=generate_unique_invite_code(db))
    db.add(household)
    db.flush()
    user = User(email=state["email"], name=state["name"], hashed_password="!passkey-only",
                is_active=True, is_admin=False, personal_household_id=household.id, active_household_id=household.id)
    db.add(user)
    try:
        db.flush()
        db.add(HouseholdMember(user_id=user.id, household_id=household.id))
        db.add(Passkey(credential_id=bytes_to_base64url(result.credential_id), user_id=user.id,
                       public_key=result.credential_public_key, sign_count=result.sign_count))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(400, "Account or passkey already exists") from exc
    return authenticate(user, response, db, request)


@router.post("/login/options", dependencies=[Depends(same_origin)])
def login_options(response: Response, db: Session = Depends(get_db)):
    start = service().begin_authentication(request_host=None, request_base_url=origin())
    set_cookie(response, FLOW_COOKIE, save_flow(db, "login", start.state), 300)
    return start.options


@router.post("/login/verify", dependencies=[Depends(same_origin)])
def login_verify(body: Finish, request: Request, response: Response, db: Session = Depends(get_db)):
    state = take_flow(db, request.cookies.get(FLOW_COOKIE, ""), "login")
    key = db.get(Passkey, body.credential.get("id", ""))
    if key is None or not key.user.is_active:
        raise HTTPException(401, "Invalid passkey")
    previous_count = key.sign_count
    try:
        result = service().verify_authentication(credential=body.credential, state=state,
            credential_public_key=key.public_key, credential_current_sign_count=previous_count)
    except Exception as exc:
        raise HTTPException(401, "Invalid passkey") from exc
    updated = db.execute(update(Passkey).where(Passkey.credential_id == key.credential_id,
        Passkey.sign_count == previous_count).values(sign_count=result.new_sign_count))
    if updated.rowcount != 1:
        db.rollback()
        raise HTTPException(401, "Passkey changed. Try again.")
    db.commit()
    return authenticate(key.user, response, db, request)


class Enrollment(BaseModel):
    token: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")


@router.post("/enroll/options", dependencies=[Depends(same_origin)])
def enroll_options(body: Enrollment, response: Response, db: Session = Depends(get_db)):
    # Enrollment link is consumed before starting the ceremony, never by a GET.
    data = take_flow(db, body.token, "enrollment")
    user = db.get(User, data["user_id"])
    if not user or not user.is_active:
        raise HTTPException(401, "Account unavailable")
    start = service().begin_registration(user=PasskeyUser(id=str(user.id).encode(), name=user.email, display_name=user.name or user.email),
        request_host=None, request_base_url=origin(), state_payload={"user_id": user.id},
        exclude_credential_ids=[p.credential_id for p in db.query(Passkey).filter_by(user_id=user.id)])
    set_cookie(response, FLOW_COOKIE, save_flow(db, "enroll", start.state), 300)
    return start.options


@router.post("/enroll/verify", dependencies=[Depends(same_origin)])
def enroll_verify(body: Finish, request: Request, response: Response, db: Session = Depends(get_db)):
    state = take_flow(db, request.cookies.get(FLOW_COOKIE, ""), "enroll")
    user = db.get(User, state["user_id"])
    if not user or not user.is_active:
        raise HTTPException(401, "Account unavailable")
    try:
        result = service().verify_registration(credential=body.credential, state=state)
        db.add(Passkey(credential_id=bytes_to_base64url(result.credential_id), user_id=user.id,
                       public_key=result.credential_public_key, sign_count=result.sign_count))
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(400, "Passkey enrollment failed. Request a new link.") from exc
    return authenticate(user, response, db, request)


@router.get("/mobile/authorize")
def authorize(request: Request, state: str = Query(pattern=r"^[A-Za-z0-9_-]{43,128}$"),
              code_challenge: str = Query(pattern=r"^[A-Za-z0-9_-]{43}$"), db: Session = Depends(get_db)):
    try:
        user = session_user(request, db)
    except HTTPException:
        return RedirectResponse("/auth/login?" + urlencode({"state": state, "code_challenge": code_challenge}), status_code=303)
    code = save_flow(db, "mobile", {"user_id": user.id, "challenge": code_challenge}, lifetime=120)
    return RedirectResponse("de.malaber.onionary://auth?" + urlencode({"code": code, "state": state}), status_code=303,
        headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})


class Exchange(BaseModel):
    code: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")
    code_verifier: str = Field(pattern=r"^[A-Za-z0-9._~-]{43,128}$")


@router.post("/mobile/token")
def exchange(body: Exchange, request: Request, response: Response, db: Session = Depends(get_db)):
    data = take_flow(db, body.code, "mobile")
    challenge = base64.urlsafe_b64encode(hashlib.sha256(body.code_verifier.encode()).digest()).decode().rstrip("=")
    if not secrets.compare_digest(data["challenge"], challenge):
        raise HTTPException(401, "Invalid sign-in proof")
    user = db.get(User, data["user_id"])
    if not user:
        raise HTTPException(401, "Account unavailable")
    result = authenticate(user, response, db, request)
    return {**result, "user_id": str(user.id)}


@router.post("/logout", dependencies=[Depends(same_origin)])
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    db.execute(delete(AuthSession).where(AuthSession.token_hash == digest(request.cookies.get(COOKIE, ""))))
    db.commit()
    response.delete_cookie(COOKIE, path="/auth")
    return {"status": "ok"}


@router.post("/mobile/logout", status_code=204)
def mobile_logout(request: Request, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    import jwt
    from execution.api.auth import SECRET_KEY, ALGORITHM
    token = request.headers["authorization"].split(" ", 1)[1]
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    db.execute(delete(AuthSession).where(AuthSession.token_hash == payload.get("sid"), AuthSession.user_id == user.id))
    db.commit()
    return Response(status_code=204)
