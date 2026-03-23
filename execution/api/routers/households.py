"""
households.py — Endpoints for joining and leaving households.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from execution.db.database import get_db
from execution.db.models import Household, User
from execution.api.schemas import UserOut
from execution.api.auth import get_current_active_user

router = APIRouter(prefix="/households", tags=["households"])

@router.post("/join/{household_id}", response_model=UserOut)
def join_household(household_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # Verify the household exists
    household = db.query(Household).filter(Household.id == household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")
        
    current_user.active_household_id = household_id
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/leave", response_model=UserOut)
def leave_household(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # Revert active household to their personal one
    current_user.active_household_id = current_user.personal_household_id
    db.commit()
    db.refresh(current_user)
    return current_user
