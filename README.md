# Onionary

Meal planning app with a FastAPI backend, PostgreSQL database, and a static frontend served by the same FastAPI process.

## How it works

This repo follows the 3-layer structure described in [AGENTS.md](./AGENTS.md):

| Layer | Location | Purpose |
|---|---|---|
| Directive | `directives/` | SOPs and workflows |
| Orchestration | AI agent | Decision-making and routing |
| Execution | `execution/` | Deterministic Python code |

For day-to-day feature work, the runtime is simpler than the architecture docs might suggest:

- PostgreSQL stores users, households, recipes, meal plans, and shopping lists.
- FastAPI exposes the API under routes like `/users`, `/recipes`, `/meal-plan`, and `/households`.
- The frontend lives in `frontend/` and is mounted by FastAPI at `/`, so one backend process serves both API and UI.
- Authentication is JWT-based. You sign up in the UI, then the frontend stores the token in `localStorage`.
- Each user gets a personal household on signup, and the active household determines which recipes and meal plans you see.

## Local development

### Prerequisites

- Python 3.11+
- Docker Desktop or another local PostgreSQL setup
- A running Postgres database reachable at the `DATABASE_URL` in your env file

### 1. Create a virtualenv and install dependencies

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.template .env
```

Default local values:

```env
DATABASE_URL=postgresql://recipes_user:recipes_pass@localhost:5432/recipes_db
SECRET_KEY=yoursecretkeyhere
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DEMO_HOUSEHOLD_ID=1
```

Notes:

- The backend loads `.env.local` and then `.env`.
- If the same variable exists in both files, `.env.local` effectively wins with the current `load_dotenv()` usage, so keep them aligned to avoid confusion.

### 3. Start PostgreSQL

This repo includes a Compose file for Postgres:

```bash
docker compose up -d
```

If your Docker installation uses the older standalone command, use:

```bash
docker-compose up -d
```

That starts:

- database: `recipes_db`
- username: `recipes_user`
- password: `recipes_pass`
- port: `5432`

### 4. Initialize or migrate the database

```bash
./venv/bin/python -m execution.db.init_db
```

What this does:

- runs Alembic migrations up to the latest revision
- automatically adopts legacy local databases that were created before Alembic was added

The app no longer mutates schema automatically on startup. Run this whenever you set up a fresh database or pull schema changes.

### 5. Start the app

```bash
./venv/bin/uvicorn execution.api.main:app --reload --port 8000
```

Open:

- app UI: [http://localhost:8000](http://localhost:8000)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- health check: [http://localhost:8000/health](http://localhost:8000/health)

## First-time usage

1. Open the app at `http://localhost:8000`
2. Sign up with a new account
3. The app creates your personal household automatically
4. Use `Manage Recipes` to create recipes
5. Use `Pick Meals` to build a meal plan and shopping list

## Development notes

### Frontend

- `frontend/index.html`: meal picker
- `frontend/recipes.html`: recipe management UI
- `frontend/kitchen.html`: kitchen/cooking flow
- `frontend/households.html`: household management
- `frontend/auth.js`: shared login/signup logic

The frontend uses same-origin requests, so there is no separate frontend dev server.

### Backend

- `execution/api/main.py`: FastAPI entry point
- `execution/api/routers/users.py`: signup, login, current user
- `execution/api/routers/recipes.py`: CRUD and random recipe selection
- `execution/api/routers/meal_plan.py`: saved meal plan for the active household
- `execution/api/routers/households.py`: create, join, switch, and leave households
- `execution/api/routers/shopping_list.py`: merged shopping list generation
- `execution/db/models.py`: SQLAlchemy models

### Tests

There are lightweight smoke tests in:

- `execution/tests/test_api.py`
- `execution/tests/test_users.py`

Run them after the app is up:

```bash
./venv/bin/python -m execution.tests.test_api
./venv/bin/python -m execution.tests.test_users
```

### Migrations

To inspect or apply migrations directly:

```bash
./venv/bin/alembic history
./venv/bin/alembic current
./venv/bin/alembic upgrade head
```

## Common gotchas

- The app requires authentication for most useful flows, including recipe and meal-plan actions.
- Household scoping matters: recipes and meal plans are tied to the currently active household.
- The configured demo household is treated as read-only for recipe mutations.
- The frontend is served by FastAPI, so if the backend is down, the UI is also down.

## Directory structure

```text
.
├── AGENTS.md
├── directives/
├── execution/
│   ├── api/
│   ├── db/
│   └── tests/
├── frontend/
├── .tmp/
├── .env.template
├── docker-compose.yml
└── requirements.txt
```

## Onionary iOS companion

The native cooking companion lives in [`ios/Onionary`](ios/Onionary/README.md).
The guide covers passkey migration, custom backends, simulator tests, GitHub
Actions, and background TestFlight uploads. Run migrations and enroll existing
accounts before disabling legacy password authentication.

## Fork development

Development branch: `codex/onionary-ios-companion`. See [test-backend deployment and release guide](docs/development-deployment.md) for GitHub Actions, GHCR images, Git tags, App Store screenshots, and the separate Onionary website.

## Instance administration and App Review

See [administrator setup and App Review passkey links](docs/passkey-review-accounts.md)
for granting an existing account admin access, opening SQLAdmin, and issuing
one-use enrollment links for reviewers.
