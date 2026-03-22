# Manage Recipes — Directive

## Goal
Run the recipe management stack (PostgreSQL + FastAPI) and use the API to create, edit, filter, and plan weekly meals.

## Prerequisites
- Docker + Docker Compose installed
- Python 3.11+

## Setup (one-time)

```bash
# 1. Start PostgreSQL
docker compose up -d

# 2. Copy env template and install deps
cp .env.template .env
pip install -r requirements.txt

# 3. Create database tables
python -m execution.db.init_db
```

## Running the API

```bash
uvicorn execution.api.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

## Key Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/recipes` | Create recipe (with ingredients, steps, tags) |
| `GET` | `/recipes` | List recipes, optional filters: `?tag=…&max_kcal=…&max_total_time=…` |
| `GET` | `/recipes/{id}` | Get single recipe |
| `PUT` | `/recipes/{id}` | Update recipe |
| `DELETE` | `/recipes/{id}` | Delete recipe |
| `POST` | `/recipes/random` | Randomly pick *n* recipes from filtered set |
| `GET` | `/tags` | List all tags |
| `POST` | `/shopping-list` | Generate aggregated shopping list from recipe IDs |

## Tools / Scripts
- `execution/db/init_db.py` — create/reset database tables
- `execution/api/main.py` — FastAPI application entry point
- `execution/tests/test_api.py` — smoke tests

## Edge Cases & Learnings
- Tags are matched case-insensitively and created on-the-fly if they don't exist.
- Shopping list merges ingredients by `(name, unit)`. Ingredients without a quantity are listed but not summed.
- The `/recipes/random` endpoint returns all candidates if fewer than `count` are available.
