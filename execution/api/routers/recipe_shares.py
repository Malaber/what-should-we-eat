"""Authenticated share creation and previews; bearer-link public resolution."""
from datetime import datetime, timedelta, timezone
import json
import secrets
import uuid
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from execution.api.auth import get_current_active_user
from execution.api.schemas import RecipeCreate, RecipeOut
from execution.api.routers.recipes import _recipe_query, _check_not_demo
from execution.api.routers.passkeys import origin
from execution.db.database import get_db
from execution.db.models import Recipe, RecipeShare, User
from execution.recipe_sharing import token_hash, fetch_snapshot, validate_snapshot, MAX_BYTES

router = APIRouter(prefix='/recipe-shares', tags=['recipe copies'])

class ShareRequest(BaseModel):
    recipe_id: int
    hours: int = Field(default=24, ge=1, le=168)

class ResolveRequest(BaseModel):
    token: str = Field(pattern=r'^[A-Za-z0-9_-]{43}$')

class PreviewRequest(BaseModel):
    url: str = Field(max_length=2048)

@router.post('', status_code=201)
def create_share(body: ShareRequest, response: Response, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    _check_not_demo(user)
    recipe = _recipe_query(db, user.active_household_id).filter(Recipe.id == body.recipe_id).first()
    if not recipe:
        raise HTTPException(404, 'Recipe not found')
    fields = RecipeOut.model_validate(recipe).model_dump(mode='json')
    fields['tags'] = [tag['name'] for tag in fields['tags']]
    payload = {'format': 'onionary.recipe.v1', 'recipe': RecipeCreate.model_validate(fields).model_dump(mode='json')}
    try:
        validate_snapshot(payload)
        snapshot = json.dumps(payload, allow_nan=False)
        if len(snapshot.encode()) > MAX_BYTES:
            raise ValueError('Recipe is too large to share')
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    token = secrets.token_urlsafe(32)
    row = RecipeShare(id=str(uuid.uuid4()), household_id=user.active_household_id,
                      token_hash=token_hash(token), snapshot=snapshot,
                      expires_at=datetime.now(timezone.utc) + timedelta(hours=body.hours))
    db.add(row); db.commit(); db.refresh(row)
    response.headers['Cache-Control'] = 'no-store'
    return {'id': row.id, 'url': f'{origin()}/share.html#{token}', 'expires_at': row.expires_at}

@router.get('')
def list_shares(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    rows = db.query(RecipeShare).filter(RecipeShare.household_id == user.active_household_id).order_by(RecipeShare.expires_at.desc()).all()
    return [{'id': row.id, 'name': json.loads(row.snapshot)['recipe']['name'], 'expires_at': row.expires_at, 'revoked': row.revoked_at is not None} for row in rows]

@router.delete('/{share_id}', status_code=204)
def revoke_share(share_id: str, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    row = db.query(RecipeShare).filter(RecipeShare.id == share_id, RecipeShare.household_id == user.active_household_id).first()
    if not row:
        raise HTTPException(404, 'Recipe link not found')
    row.revoked_at = datetime.now(timezone.utc); db.commit()

@router.post('/resolve')
def resolve_share(body: ResolveRequest, response: Response, db: Session = Depends(get_db)):
    row = db.query(RecipeShare).filter(RecipeShare.token_hash == token_hash(body.token), RecipeShare.revoked_at.is_(None), RecipeShare.expires_at > datetime.now(timezone.utc)).first()
    if not row:
        raise HTTPException(404, 'Recipe link is unavailable, expired, or revoked')
    response.headers.update({'Cache-Control':'no-store', 'Referrer-Policy':'no-referrer'})
    return json.loads(row.snapshot)

@router.post('/preview', response_model=RecipeCreate)
def preview_share(body: PreviewRequest, user: User = Depends(get_current_active_user)):
    try:
        return fetch_snapshot(body.url)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
