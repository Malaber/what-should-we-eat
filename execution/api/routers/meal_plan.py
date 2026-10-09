"""
meal_plan.py — Endpoints for managing the household's meal plan.

The meal plan stores which recipes a household has selected for the week,
and tracks cooked status for the kitchen view.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from execution.api.auth import get_current_active_user
from execution.api.schemas import MealPlanAdd, MealPlanItemOut, MealPlanOut
from execution.db.database import get_db
from execution.db.models import MealPlanItem, Recipe, User

router = APIRouter(prefix="/meal-plan", tags=["meal plan"])


def _plan_query(db: Session, household_id: int):
    """Base query with eager-loaded recipe relationships."""
    return (
        db.query(MealPlanItem)
        .filter(MealPlanItem.household_id == household_id)
        .options(
            joinedload(MealPlanItem.recipe)
            .joinedload(Recipe.ingredients),
            joinedload(MealPlanItem.recipe)
            .joinedload(Recipe.instruction_steps),
            joinedload(MealPlanItem.recipe)
            .joinedload(Recipe.tags),
        )
    )


def _validate_recipes(db: Session, household_id: int, ids: list[int]):
    owned = {row.id for row in db.query(Recipe.id).filter(Recipe.household_id == household_id, Recipe.id.in_(ids))}
    if set(ids) - owned:
        raise HTTPException(404, "Recipe not found in your kitchen")


# ── GET meal plan ────────────────────────────────────────────────────

@router.get("", response_model=MealPlanOut)
def get_meal_plan(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    hid = current_user.active_household_id
    items = _plan_query(db, hid).order_by(MealPlanItem.added_at).all()
    return MealPlanOut(items=items)


# ── PUT meal plan (replace entirely) ─────────────────────────────────

@router.put("", response_model=MealPlanOut)
def replace_meal_plan(
    body: MealPlanAdd,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    hid = current_user.active_household_id
    _validate_recipes(db, hid, body.recipe_ids)
    db.query(MealPlanItem).filter(MealPlanItem.household_id == hid).delete()
    db.flush()

    for rid in dict.fromkeys(body.recipe_ids):
        db.add(MealPlanItem(household_id=hid, recipe_id=rid))
    db.commit()

    items = _plan_query(db, hid).order_by(MealPlanItem.added_at).all()
    return MealPlanOut(items=items)


# ── POST add recipes ─────────────────────────────────────────────────

@router.post("/add", response_model=MealPlanOut, status_code=201)
def add_to_meal_plan(
    body: MealPlanAdd,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    hid = current_user.active_household_id
    _validate_recipes(db, hid, body.recipe_ids)
    existing_ids = {
        row.recipe_id
        for row in db.query(MealPlanItem.recipe_id)
        .filter(MealPlanItem.household_id == hid)
        .all()
    }
    for rid in dict.fromkeys(body.recipe_ids):
        if rid not in existing_ids:
            db.add(MealPlanItem(household_id=hid, recipe_id=rid))
    db.commit()

    items = _plan_query(db, hid).order_by(MealPlanItem.added_at).all()
    return MealPlanOut(items=items)


# ── DELETE single recipe from plan ───────────────────────────────────

@router.delete("/{recipe_id}", status_code=204)
def remove_from_meal_plan(
    recipe_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    hid = current_user.active_household_id
    deleted = (
        db.query(MealPlanItem)
        .filter(MealPlanItem.household_id == hid, MealPlanItem.recipe_id == recipe_id)
        .delete()
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Recipe not in meal plan")
    db.commit()


# ── DELETE entire plan ───────────────────────────────────────────────

@router.delete("", status_code=204)
def clear_meal_plan(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    hid = current_user.active_household_id
    db.query(MealPlanItem).filter(MealPlanItem.household_id == hid).delete()
    db.commit()


# ── POST mark cooked ────────────────────────────────────────────────

@router.post("/{recipe_id}/cooked", response_model=MealPlanItemOut)
def mark_cooked(
    recipe_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    hid = current_user.active_household_id
    item = (
        _plan_query(db, hid)
        .filter(MealPlanItem.recipe_id == recipe_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Recipe not in meal plan")
    item.is_cooked = True
    db.commit()
    db.refresh(item)
    return item


# ── DELETE undo cooked ───────────────────────────────────────────────

@router.delete("/{recipe_id}/cooked", response_model=MealPlanItemOut)
def unmark_cooked(
    recipe_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    hid = current_user.active_household_id
    item = (
        _plan_query(db, hid)
        .filter(MealPlanItem.recipe_id == recipe_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Recipe not in meal plan")
    item.is_cooked = False
    db.commit()
    db.refresh(item)
    return item
