"""Account-scoped recipe URLs and text for review on another device."""
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import re
from typing import Annotated, Literal
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, StringConstraints, ValidationError, model_validator
from sqlalchemy.orm import Session

from execution.api.auth import get_current_active_user
from execution.api.routers.passkeys import same_origin, session_user
from execution.db.database import get_db
from execution.db.models import RecipeInboxItem, User

router = APIRouter(tags=["recipe inbox"])
templates = Jinja2Templates(directory=Path(__file__).resolve().parents[2] / "templates")
private = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}


class RecipeSource(BaseModel):
    kind: Literal["url", "text"]
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=12_000)]

    @model_validator(mode="after")
    def validate_url(self):
        if self.kind == "text":
            return self
        try:
            parts = urlsplit(self.content)
            hostname = (parts.hostname or "").encode("idna").decode("ascii").lower()
            valid = (len(self.content) <= 2048 and not re.search(r"[\s\x00-\x1f\x7f\\]", self.content)
                     and parts.scheme == "https" and parts.username is None and parts.password is None
                     and parts.port in (None, 443)
                     and bool(re.fullmatch(r"(?:[a-z0-9-]+\.)+[a-z][a-z0-9-]*", hostname))
                     and not hostname.endswith((".localhost", ".local", ".internal")))
        except (ValueError, UnicodeError):
            valid = False
        if not valid:
            raise ValueError("Enter a public HTTPS recipe URL.")
        return self


class InboxItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: Literal["url", "text"]
    content: str
    created_at: datetime


def save_source(db, user, source):
    fingerprint = sha256(f"{source.kind}\0{source.content}".encode()).hexdigest()
    # Serialize inserts for the same account, including repeats from multiple tabs.
    db.query(User).filter_by(id=user.id).with_for_update().one()
    items = db.query(RecipeInboxItem).filter_by(user_id=user.id)
    previous = items.filter_by(fingerprint=fingerprint).first()
    if previous is not None:
        return previous
    if items.count() >= 100:
        raise HTTPException(409, "Remove a saved import before adding another.")
    item = RecipeInboxItem(user_id=user.id, kind=source.kind, content=source.content, fingerprint=fingerprint)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/recipe-inbox", response_model=list[InboxItem])
def list_inbox(response: Response, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    response.headers.update(private)
    return db.query(RecipeInboxItem).filter_by(user_id=user.id).order_by(
        RecipeInboxItem.created_at.desc(), RecipeInboxItem.id.desc()).all()


@router.post("/recipe-inbox", response_model=InboxItem)
def add_inbox(source: RecipeSource, response: Response, user: User = Depends(get_current_active_user),
              db: Session = Depends(get_db)):
    response.headers.update(private)
    return save_source(db, user, source)


@router.delete("/recipe-inbox/{item_id}", status_code=204)
def delete_inbox(item_id: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not db.query(RecipeInboxItem).filter_by(user_id=user.id, id=item_id).delete():
        raise HTTPException(404, "Saved import not found.")
    db.commit()


def inbox_page(request, *, form=None, error=None, saved=False, status=200):
    language = "de" if request.headers.get("accept-language", "").lower().startswith("de") else "en"
    return templates.TemplateResponse(request, "recipe-inbox.html", {
        "language": language, "form": form or {}, "error": error, "saved": saved,
    }, status_code=status, headers=private)


@router.get("/import-later", include_in_schema=False)
def browser_inbox(request: Request, saved: bool = False, db: Session = Depends(get_db)):
    try:
        session_user(request, db)
    except HTTPException as error:
        if error.status_code != 401:
            raise
        return RedirectResponse("/auth/login", headers=private)
    return inbox_page(request, saved=saved)


@router.post("/import-later", include_in_schema=False, dependencies=[Depends(same_origin)])
def browser_save(request: Request, kind: Annotated[str, Form(max_length=4)],
                 content: Annotated[str, Form(max_length=12_000)], db: Session = Depends(get_db)):
    user = session_user(request, db)
    form = {"kind": kind, "content": content}
    try:
        source = RecipeSource(**form)
    except ValidationError:
        return inbox_page(request, form=form, error="input", status=422)
    try:
        save_source(db, user, source)
    except HTTPException as error:
        if error.status_code != 409:
            raise
        return inbox_page(request, form=form, error="full", status=409)
    return RedirectResponse("/import-later?saved=1", status_code=303, headers=private)
