"""
schemas.py — Pydantic models for request / response validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Instruction Steps ────────────────────────────────────────────────

class InstructionStepBase(BaseModel):
    step_number: int
    description: str
    duration_min: Optional[int] = None


class InstructionStepCreate(InstructionStepBase):
    pass


class InstructionStepOut(InstructionStepBase):
    id: int

    class Config:
        from_attributes = True


# ── Ingredients ──────────────────────────────────────────────────────

class IngredientBase(BaseModel):
    name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None


class IngredientCreate(IngredientBase):
    pass


class IngredientOut(IngredientBase):
    id: int

    class Config:
        from_attributes = True


# ── Tags ─────────────────────────────────────────────────────────────

class TagBase(BaseModel):
    name: str


class TagCreate(TagBase):
    pass


class TagOut(TagBase):
    id: int

    class Config:
        from_attributes = True


# ── Recipes ──────────────────────────────────────────────────────────

class RecipeBase(BaseModel):
    name: str
    kcal_per_serving: Optional[float] = None
    active_cooking_time_min: Optional[int] = None
    total_time_min: Optional[int] = None


class RecipeCreate(RecipeBase):
    ingredients: list[IngredientCreate] = Field(default_factory=list)
    instruction_steps: list[InstructionStepCreate] = Field(default_factory=list)
    tags: list[str] = Field(
        default_factory=list,
        description="Tag names — existing tags are reused, new ones created automatically.",
    )


class RecipeUpdate(BaseModel):
    """All fields optional for partial updates."""
    name: Optional[str] = None
    kcal_per_serving: Optional[float] = None
    active_cooking_time_min: Optional[int] = None
    total_time_min: Optional[int] = None
    ingredients: Optional[list[IngredientCreate]] = None
    instruction_steps: Optional[list[InstructionStepCreate]] = None
    tags: Optional[list[str]] = None


class RecipeOut(RecipeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    ingredients: list[IngredientOut] = []
    instruction_steps: list[InstructionStepOut] = []
    tags: list[TagOut] = []

    class Config:
        from_attributes = True


# ── Random selection request ─────────────────────────────────────────

class RandomSelectionRequest(BaseModel):
    count: int = Field(ge=1, description="Number of recipes to select")
    tag_names: list[str] = Field(default_factory=list)
    max_kcal: Optional[float] = None
    max_total_time: Optional[int] = None
    exclude_ids: list[int] = Field(
        default_factory=list,
        description="Recipe IDs to exclude (for re-rolling without duplicates).",
    )


# ── Shopping list ────────────────────────────────────────────────────

class ShoppingListItem(BaseModel):
    name: str
    total_quantity: Optional[float] = None
    unit: Optional[str] = None


class ShoppingListOut(BaseModel):
    items: list[ShoppingListItem]
    recipe_ids: list[int]
