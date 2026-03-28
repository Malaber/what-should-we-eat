"""
households.py — Endpoints for managing household memberships.

Users can belong to multiple households but only one is active at a time.
The active household determines which recipes and meal plan are visible.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from execution.db.database import get_db
from execution.db.models import Household, HouseholdMember, User
from execution.api.schemas import HouseholdCreate, HouseholdOut, UserOut, HouseholdMembershipOut
from execution.api.auth import get_current_active_user

router = APIRouter(prefix="/households", tags=["households"])


def _build_user_out(user: User, db: Session) -> UserOut:
    """Build a UserOut with the user's household memberships."""
    memberships = (
        db.query(HouseholdMember, Household.name)
        .join(Household, HouseholdMember.household_id == Household.id)
        .filter(HouseholdMember.user_id == user.id)
        .all()
    )
    households = [
        HouseholdMembershipOut(household_id=m.household_id, household_name=name)
        for m, name in memberships
    ]
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        personal_household_id=user.personal_household_id,
        active_household_id=user.active_household_id,
        created_at=user.created_at,
        updated_at=user.updated_at,
        households=households,
    )


# ── List my households ───────────────────────────────────────────────

@router.get("", response_model=list[HouseholdOut])
def list_my_households(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return all households the current user belongs to."""
    return (
        db.query(Household)
        .join(HouseholdMember, HouseholdMember.household_id == Household.id)
        .filter(HouseholdMember.user_id == current_user.id)
        .order_by(Household.name)
        .all()
    )


# ── Create a new household ──────────────────────────────────────────

@router.post("", response_model=HouseholdOut, status_code=201)
def create_household(
    body: HouseholdCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new household and auto-join the creator."""
    household = Household(name=body.name)
    db.add(household)
    db.flush()

    membership = HouseholdMember(user_id=current_user.id, household_id=household.id)
    db.add(membership)
    db.commit()
    db.refresh(household)
    return household


# ── Join an existing household ───────────────────────────────────────

@router.post("/join/{household_id}", response_model=UserOut)
def join_household(
    household_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Join a household (adds membership) and switch to it."""
    household = db.query(Household).filter(Household.id == household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")

    # Check if already a member
    existing = (
        db.query(HouseholdMember)
        .filter(HouseholdMember.user_id == current_user.id, HouseholdMember.household_id == household_id)
        .first()
    )
    if not existing:
        db.add(HouseholdMember(user_id=current_user.id, household_id=household_id))

    current_user.active_household_id = household_id
    db.commit()
    db.refresh(current_user)
    return _build_user_out(current_user, db)


# ── Switch active household ─────────────────────────────────────────

@router.post("/switch/{household_id}", response_model=UserOut)
def switch_household(
    household_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Switch to a household the user is already a member of."""
    membership = (
        db.query(HouseholdMember)
        .filter(HouseholdMember.user_id == current_user.id, HouseholdMember.household_id == household_id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="You are not a member of this household")

    current_user.active_household_id = household_id
    db.commit()
    db.refresh(current_user)
    return _build_user_out(current_user, db)


# ── Leave a household ───────────────────────────────────────────────

@router.post("/leave/{household_id}", response_model=UserOut)
def leave_household(
    household_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Leave a household. Cannot leave your personal household."""
    if household_id == current_user.personal_household_id:
        raise HTTPException(status_code=400, detail="Cannot leave your personal household")

    deleted = (
        db.query(HouseholdMember)
        .filter(HouseholdMember.user_id == current_user.id, HouseholdMember.household_id == household_id)
        .delete()
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Not a member of this household")

    # If leaving the active household, switch back to personal
    if current_user.active_household_id == household_id:
        current_user.active_household_id = current_user.personal_household_id

    db.commit()
    db.refresh(current_user)
    return _build_user_out(current_user, db)
