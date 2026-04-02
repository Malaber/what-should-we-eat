"""
recipes.py — CRUD, filter, and random-selection endpoints for recipes.
"""

import os
import random as _random
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from execution.api.schemas import (
    RandomSelectionRequest,
    RecipeCreate,
    RecipeDraftOut,
    RecipeHtmlImportRequest,
    RecipeOut,
    RecipeUpdate,
    RecipeImportOut,
)
from execution.db.database import get_db
from execution.db.models import Ingredient, InstructionStep, Recipe, Tag, User, Household
from execution.api.auth import get_current_active_user
from execution.api.recipe_import import fetch_recipe_html, parse_recipe_html

router = APIRouter(prefix="/recipes", tags=["recipes"])


# ── helpers ──────────────────────────────────────────────────────────

def _check_not_demo(user: User):
    """Ensure the user is not trying to modify the demo household."""
    try:
        demo_household_id = int(os.getenv("DEMO_HOUSEHOLD_ID", "1"))
    except ValueError:
        demo_household_id = 0
        
    if user.active_household_id == demo_household_id:
        raise HTTPException(
            status_code=403, 
            detail="The demo household is read-only. You cannot modify its recipes."
        )


def _get_or_create_tags(db: Session, tag_names: list[str]) -> list[Tag]:
    """Return Tag objects, creating any that don't exist yet."""
    tags: list[Tag] = []
    for name in tag_names:
        tag = db.query(Tag).filter(func.lower(Tag.name) == name.lower()).first()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        tags.append(tag)
    return tags


def _apply_filters(
    query,
    db: Session,
    tag_names: list[str] | None = None,
    max_kcal: float | None = None,
    max_total_time: int | None = None,
):
    """Apply optional filters to a recipe query."""
    if tag_names:
        for tag_name in tag_names:
            query = query.filter(
                Recipe.tags.any(func.lower(Tag.name) == tag_name.lower())
            )
    if max_kcal is not None:
        query = query.filter(Recipe.kcal_per_serving <= max_kcal)
    if max_total_time is not None:
        query = query.filter(Recipe.total_time_min <= max_total_time)
    return query


def _recipe_query(db: Session, household_id: int):
    """Base query with eager-loaded relationships."""
    return db.query(Recipe).filter(Recipe.household_id == household_id).options(
        joinedload(Recipe.ingredients),
        joinedload(Recipe.instruction_steps),
        joinedload(Recipe.tags),
    )


# ── CREATE ───────────────────────────────────────────────────────────

@router.post("", response_model=RecipeOut, status_code=201)
def create_recipe(data: RecipeCreate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    _check_not_demo(current_user)
    
    recipe = Recipe(
        household_id=current_user.active_household_id,
        name=data.name,
        notes=data.notes,
        kcal_per_serving=data.kcal_per_serving,
        active_cooking_time_min=data.active_cooking_time_min,
        total_time_min=data.total_time_min,
    )
    recipe.ingredients = [
        Ingredient(**ing.model_dump()) for ing in data.ingredients
    ]
    recipe.instruction_steps = [
        InstructionStep(**step.model_dump()) for step in data.instruction_steps
    ]
    recipe.tags = _get_or_create_tags(db, data.tags)

    db.add(recipe)
    db.commit()
    db.refresh(recipe)

    # Re-query with eager loading to ensure full nested output
    return _recipe_query(db, current_user.active_household_id).filter(Recipe.id == recipe.id).first()


@router.post("/import/{invite_code}", response_model=RecipeImportOut, status_code=201)
def import_recipes_from_household(
    invite_code: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    _check_not_demo(current_user)
    
    source_household = db.query(Household).filter(Household.invite_code == invite_code.upper()).first()
    if not source_household:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    if source_household.id == current_user.active_household_id:
        raise HTTPException(status_code=400, detail="Cannot import from the currently active household")
        
    recipes_to_import = _recipe_query(db, source_household.id).all()
    count = 0
    
    for recipe in recipes_to_import:
        new_recipe = Recipe(
            household_id=current_user.active_household_id,
            name=recipe.name,
            notes=recipe.notes,
            kcal_per_serving=recipe.kcal_per_serving,
            active_cooking_time_min=recipe.active_cooking_time_min,
            total_time_min=recipe.total_time_min,
        )
        
        new_recipe.ingredients = [
            Ingredient(name=ing.name, quantity=ing.quantity, unit=ing.unit)
            for ing in recipe.ingredients
        ]
        
        new_recipe.instruction_steps = [
            InstructionStep(step_number=step.step_number, description=step.description, duration_min=step.duration_min)
            for step in recipe.instruction_steps
        ]
        
        new_recipe.tags = [t for t in recipe.tags]
        
        db.add(new_recipe)
        count += 1
        
    db.commit()
    return RecipeImportOut(imported_count=count)


@router.post("/import/parse/html", response_model=RecipeDraftOut)
def parse_recipe_import(
    body: RecipeHtmlImportRequest,
    current_user: User = Depends(get_current_active_user),
):
    # Authentication is enough here; parsed data is only used to prefill the form.
    _ = current_user
    try:
        html = body.html or fetch_recipe_html(source=body.source, url=body.url or "")
        return parse_recipe_html(source=body.source, html=html, url=body.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ── READ (list + single) ────────────────────────────────────────────

@router.get("", response_model=list[RecipeOut])
def list_recipes(
    tag: Optional[list[str]] = Query(None, description="Filter by tag names"),
    max_kcal: Optional[float] = Query(None),
    max_total_time: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    q = _recipe_query(db, current_user.active_household_id)
    q = _apply_filters(q, db, tag_names=tag, max_kcal=max_kcal, max_total_time=max_total_time)
    return q.all()


@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    recipe = _recipe_query(db, current_user.active_household_id).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, "Recipe not found")
    return recipe


# ── UPDATE ─────────x──────────────────────────────────────────────────

@router.put("/{recipe_id}", response_model=RecipeOut)
def update_recipe(recipe_id: int, data: RecipeUpdate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    _check_not_demo(current_user)
    
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id, Recipe.household_id == current_user.active_household_id).first()
    if not recipe:
        raise HTTPException(404, "Recipe not found")

    # scalar fields
    for field in ("name", "notes", "kcal_per_serving", "active_cooking_time_min", "total_time_min"):
        if field in data.model_fields_set:
            setattr(recipe, field, getattr(data, field))

    # replace ingredients if provided
    if data.ingredients is not None:
        recipe.ingredients = [
            Ingredient(**ing.model_dump()) for ing in data.ingredients
        ]

    # replace instruction steps if provided
    if data.instruction_steps is not None:
        recipe.instruction_steps = [
            InstructionStep(**step.model_dump()) for step in data.instruction_steps
        ]

    # replace tags if provided
    if data.tags is not None:
        recipe.tags = _get_or_create_tags(db, data.tags)

    db.commit()
    db.refresh(recipe)

    # Clean up orphaned tags
    db.query(Tag).filter(~Tag.recipes.any()).delete()
    db.commit()

    return _recipe_query(db, current_user.active_household_id).filter(Recipe.id == recipe.id).first()


# ── DELETE ───────────────────────────────────────────────────────────

@router.delete("/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    _check_not_demo(current_user)
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id, Recipe.household_id == current_user.active_household_id).first()
    if not recipe:
        raise HTTPException(404, "Recipe not found")
    db.delete(recipe)
    db.commit()

    # Clean up orphaned tags
    db.query(Tag).filter(~Tag.recipes.any()).delete()
    db.commit()

# ── RANDOM SELECTION ─────────────────────────────────────────────────

@router.post("/random", response_model=list[RecipeOut])
def random_recipes(body: RandomSelectionRequest, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    q = _recipe_query(db, current_user.active_household_id)
    q = _apply_filters(
        q, db,
        tag_names=body.tag_names or None,
        max_kcal=body.max_kcal,
        max_total_time=body.max_total_time,
    )
    # Exclude already-selected recipe IDs (used for single-reroll)
    if body.exclude_ids:
        q = q.filter(Recipe.id.notin_(body.exclude_ids))

    candidates = q.all()

    if len(candidates) <= body.count:
        return candidates

    return _random.sample(candidates, body.count)
