"""
shopping_list.py — Aggregate ingredients from selected recipes into a shopping list.
"""

from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from execution.api.schemas import ShoppingListItem, ShoppingListOut
from execution.db.database import get_db
from execution.db.models import Recipe

router = APIRouter(prefix="/shopping-list", tags=["shopping list"])


@router.post("", response_model=ShoppingListOut)
def generate_shopping_list(
    recipe_ids: list[int],
    db: Session = Depends(get_db),
):
    """
    Accepts a list of recipe IDs. Returns a merged shopping list that
    aggregates ingredient quantities by (name, unit).
    """
    recipes = db.query(Recipe).filter(Recipe.id.in_(recipe_ids)).all()
    found_ids = {r.id for r in recipes}
    missing = set(recipe_ids) - found_ids
    if missing:
        raise HTTPException(404, f"Recipes not found: {sorted(missing)}")

    # Aggregate by (lowercase name, unit)
    aggregated: dict[tuple[str, str | None], float | None] = defaultdict(lambda: None)
    for recipe in recipes:
        for ing in recipe.ingredients:
            key = (ing.name.lower(), ing.unit)
            if ing.quantity is not None:
                if aggregated[key] is None:
                    aggregated[key] = 0.0
                aggregated[key] += ing.quantity
            # if quantity is None we leave the aggregate as None (unquantified)

    items = [
        ShoppingListItem(name=name, total_quantity=qty, unit=unit)
        for (name, unit), qty in sorted(aggregated.items())
    ]

    return ShoppingListOut(items=items, recipe_ids=sorted(found_ids))
