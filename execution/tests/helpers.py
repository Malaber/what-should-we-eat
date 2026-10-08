"""
helpers.py — Shared test helpers and data factories.
"""


def make_recipe_payload(
    name: str = "Test Recipe",
    kcal: float = 400,
    tags: list[str] | None = None,
) -> dict:
    """Build a valid RecipeCreate payload."""
    return {
        "name": name,
        "kcal_per_serving": kcal,
        "active_cooking_time_min": 15,
        "total_time_min": 30,
        "ingredients": [
            {"name": "chicken", "quantity": 300, "unit": "g"},
            {"name": "rice", "quantity": 200, "unit": "g"},
        ],
        "instruction_steps": [
            {"step_number": 1, "description": "Cook chicken", "duration_min": 10},
            {"step_number": 2, "description": "Cook rice", "duration_min": 15},
        ],
        "tags": tags or ["quick", "protein"],
    }
