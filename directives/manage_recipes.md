# Manage Recipes — Directive

## Goal
Create, read, update, delete, filter, and randomly select recipes via the API. All recipe operations are scoped to the user's active household and require authentication.

## Prerequisites
- Stack running (see `directives/local_development.md`)
- Authenticated user with a valid JWT token

## Key Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/recipes` | Create recipe (with ingredients, steps, tags) |
| `GET` | `/recipes` | List recipes, optional filters: `?tag=…&max_kcal=…&max_total_time=…` |
| `GET` | `/recipes/{id}` | Get single recipe |
| `PUT` | `/recipes/{id}` | Update recipe (partial — only sent fields are changed) |
| `DELETE` | `/recipes/{id}` | Delete recipe |
| `POST` | `/recipes/random` | Randomly pick *n* recipes from filtered set |
| `POST` | `/recipes/import/{invite_code}` | Copy all recipes from another household into the active one |
| `POST` | `/recipes/import/parse/html` | Parse a Chefkoch URL/HTML into a recipe draft for review |

## Tools / Scripts
- `execution/api/routers/recipes.py` — CRUD and random-selection router
- `execution/api/recipe_import.py` — HTML parsing and fetching for external imports (Chefkoch)
- `execution/api/schemas.py` — Pydantic models (`RecipeCreate`, `RecipeUpdate`, `RecipeOut`, etc.)
- `execution/db/models.py` — SQLAlchemy models (`Recipe`, `Ingredient`, `InstructionStep`, `Tag`)
- `execution/db/seed_recipes.py` — Bulk seed recipes from generated insert chunks

## Edge Cases & Learnings
- **Household scoping**: All recipe queries filter by `active_household_id`. Users see only their active household's recipes.
- **Demo household**: The household matching `DEMO_HOUSEHOLD_ID` is read-only; create/update/delete returns 403.
- **Tags**: Matched case-insensitively and created on-the-fly if they don't exist. Orphaned tags are cleaned up after recipe update/delete.
- **Shopping list**: Merges ingredients by `(name, unit)`. Ingredients without a quantity are listed but not summed.
- **Random selection**: Returns all candidates if fewer than `count` are available. Supports `exclude_ids` for re-rolling without duplicates.
- **Recipe import (Chefkoch)**: Parses JSON-LD `@type: Recipe` from HTML. Supports Unicode fractions and German units in ingredient parsing. Only `chefkoch.de` domains are allowed; redirect targets are validated.
- **Household import**: Copies recipes including ingredients, steps, and tags. Tags are shared by reference (not duplicated).
