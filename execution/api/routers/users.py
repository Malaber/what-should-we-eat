"""
users.py — Endpoints for user registration, login, and profile.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from execution.db.database import get_db
from execution.db.models import User, Household, HouseholdMember
from execution.api.schemas import UserCreate, UserOut, Token, HouseholdMembershipOut
from execution.api.auth import get_password_hash, verify_password, create_access_token, get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])


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


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    
    # Create the user's default household
    household = Household(name=f"{user_data.name or 'New User'}'s Kitchen")
    db.add(household)
    db.flush()
    
    user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
        is_active=user_data.is_active,
        is_admin=user_data.is_admin,
        personal_household_id=household.id,
        active_household_id=household.id
    )
    db.add(user)
    db.flush()

    # Auto-add the user to their personal household
    db.add(HouseholdMember(user_id=user.id, household_id=household.id))
    db.commit()
    db.refresh(user)
    return _build_user_out(user, db)

@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return _build_user_out(current_user, db)

