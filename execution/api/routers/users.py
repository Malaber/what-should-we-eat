"""
users.py — Endpoints for user registration, login, and profile.
"""

import os
from typing import Annotated
from unicodedata import normalize

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, StrictBool, StringConstraints
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from execution.db.database import get_db
from execution.db.models import AccountEquipment, User, Household, HouseholdMember, generate_unique_invite_code
from execution.api.schemas import UserCreate, UserOut, Token, HouseholdMembershipOut
from execution.api.auth import get_password_hash, verify_password, create_access_token, get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])


def require_legacy_auth():
    if os.getenv("ALLOW_LEGACY_PASSWORD_AUTH", "false").lower() != "true":
        raise HTTPException(410, "Password sign-in is disabled. Use a passkey.")


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
    require_legacy_auth()
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    
    # Create the user's default household with collision-safe invite code
    code = generate_unique_invite_code(db)
    household = Household(name=f"{user_data.name or 'New User'}'s Kitchen", invite_code=code)
    db.add(household)
    db.flush()
    
    user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False,
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
    require_legacy_auth()
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



from execution.account_deletion import DeleteAccount, delete_account


@router.post("/me/delete", status_code=204)
def delete_my_account(body: DeleteAccount, current_user: User = Depends(get_current_active_user),
                      db: Session = Depends(get_db)):
    delete_account(db, current_user, body.email)


ToolName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=320)]


class EquipmentUpdate(BaseModel):
    changes: dict[ToolName, StrictBool] = Field(default_factory=dict)
    legacy_owned: list[ToolName] = Field(default_factory=list)


class EquipmentInventory(BaseModel):
    owned: list[str]


def equipment_key(name: str) -> str:
    return normalize("NFC", " ".join(name.split()).lower())


def equipment_inventory(db: Session, user_id: int) -> EquipmentInventory:
    rows = db.query(AccountEquipment.name).filter_by(user_id=user_id, owned=True).order_by(AccountEquipment.name)
    return EquipmentInventory(owned=[name for (name,) in rows])


@router.get("/me/equipment", response_model=EquipmentInventory)
def read_my_equipment(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return equipment_inventory(db, user.id)


@router.put("/me/equipment", response_model=EquipmentInventory)
def update_my_equipment(body: EquipmentUpdate, user: User = Depends(get_current_active_user),
                        db: Session = Depends(get_db)):
    user_id = user.id
    if db.query(User.id).filter_by(id=user_id).with_for_update().one_or_none() is None:
        raise HTTPException(401, "Sign in again to sync equipment.")
    insert = postgres_insert if db.get_bind().dialect.name == "postgresql" else sqlite_insert
    changes = {equipment_key(name): owned for name, owned in body.changes.items()}
    legacy = {equipment_key(name) for name in body.legacy_owned} - changes.keys()
    key = [AccountEquipment.user_id, AccountEquipment.name]
    # A stored false prevents a legacy client from reviving a removed tool.
    if legacy:
        statement = insert(AccountEquipment.__table__).on_conflict_do_nothing(index_elements=key)
        db.execute(statement, [
            {"user_id": user_id, "name": name, "owned": True} for name in sorted(legacy)
        ])
    if changes:
        statement = insert(AccountEquipment.__table__)
        db.execute(statement.on_conflict_do_update(index_elements=key, set_={"owned": statement.excluded.owned}), [
            {"user_id": user_id, "name": name, "owned": owned} for name, owned in sorted(changes.items())
        ])
    current = equipment_inventory(db, user_id)
    db.commit()
    return current
