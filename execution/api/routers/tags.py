"""
tags.py — Endpoint to list all available tags.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from execution.api.schemas import TagOut
from execution.db.database import get_db
from execution.db.models import Tag

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagOut])
def list_tags(db: Session = Depends(get_db)):
    return db.query(Tag).order_by(Tag.name).all()
