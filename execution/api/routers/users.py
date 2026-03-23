"""
users.py — Endpoints for user registration, login, and profile.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from execution.db.database import get_db
from execution.db.models import User, Household
from execution.api.schemas import UserCreate, UserOut, Token
from execution.api.auth import get_password_hash, verify_password, create_access_token, get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    
    # Create the user's default household
    household = Household(name=f"{user_data.name or 'New User'}'s Kitchen")
    db.add(household)
    db.flush() # flush to get the household.id without committing
    
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
    db.commit()
    db.refresh(user)
    return user

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
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
