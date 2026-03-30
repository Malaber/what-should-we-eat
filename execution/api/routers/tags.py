"""
tags.py — Endpoint to list all available tags.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from execution.api.schemas import TagOut
from execution.db.database import get_db
from execution.db.models import Tag, User, Recipe
from execution.api.auth import get_current_active_user

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagOut])
def list_tags(
    current_user: User = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    """
    Return only tags that are actually used by recipes 
    within the current user's active household.
    """
    return (
        db.query(Tag)
        .join(Recipe, Tag.recipes) # Explicitly join Tag to Recipe
        .filter(Recipe.household_id == current_user.active_household_id)
        .distinct()
        .order_by(Tag.name)
        .all()
    )