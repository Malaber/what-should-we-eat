# Manage Meal Plan — Directive

## Goal
Build and manage a household's weekly meal plan: add recipes, track cooking status, generate shopping lists, and clear/replace the whole plan.

## Prerequisites
- Stack running (see `directives/local_development.md`)
- Authenticated user with recipes in their active household

## Key Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/meal-plan` | Get the current household's meal plan |
| `PUT` | `/meal-plan` | Replace the entire plan with a new set of recipe IDs |
| `POST` | `/meal-plan/add` | Add recipes to the existing plan (skips duplicates) |
| `DELETE` | `/meal-plan/{recipe_id}` | Remove a single recipe from the plan |
| `DELETE` | `/meal-plan` | Clear the entire plan |
| `POST` | `/meal-plan/{recipe_id}/cooked` | Mark a recipe as cooked |
| `DELETE` | `/meal-plan/{recipe_id}/cooked` | Unmark a recipe as cooked |
| `POST` | `/shopping-list` | Generate shopping list from a list of recipe IDs |

## Typical User Flow
1. **Pick Meals** — On the main page (`index.html`), user filters by tags/calories/time, randomizes, and selects recipes
2. **Save to Plan** — Selected recipes are saved via `PUT /meal-plan` (replaces) or `POST /meal-plan/add` (appends)
3. **Kitchen View** — On `kitchen.html`, user sees the plan, marks recipes as cooked, and views individual recipes for cooking
4. **Shopping List** — Generated from recipe IDs aggregating all ingredients by `(name, unit)`

## Data Model
- `MealPlanItem` — `id`, `household_id`, `recipe_id`, `is_cooked`, `added_at`
- Unique constraint: one recipe per household per plan (`uq_household_recipe_plan`)

## Frontend Pages
- `frontend/index.html` + `frontend/app.js` — Meal picker (filter, randomize, save plan)
- `frontend/kitchen.html` + `frontend/kitchen.js` — Kitchen view (cook, mark done, shopping list)

## Tools / Scripts
- `execution/api/routers/meal_plan.py` — All meal plan endpoints
- `execution/api/routers/shopping_list.py` — Shopping list generation
- `execution/api/schemas.py` — `MealPlanAdd`, `MealPlanItemOut`, `MealPlanOut`, `ShoppingListOut`
- `execution/db/models.py` — `MealPlanItem`

## Edge Cases & Learnings
- Adding a recipe that's already in the plan is silently skipped (no error, no duplicate).
- `PUT /meal-plan` wipes and replaces — useful for the "save new selection" flow.
- Shopping list merges ingredients by `(lowercase name, unit)`. Unquantified ingredients appear in the list but with `null` quantity.
- Each meal plan item eagerly loads the full recipe (ingredients, steps, tags) to power the kitchen view.
- Cooked status is per-plan-item, not per-recipe — re-adding a recipe after clearing creates a fresh uncooked entry.
