# Local Development — Directive

## Goal
Set up and run the full stack locally: PostgreSQL, FastAPI backend, and frontend.

## Prerequisites
- Python 3.11+
- Docker Desktop (or a local PostgreSQL setup)

## Setup (one-time)

```bash
# 1. Create virtualenv and install deps
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# 2. Copy env template
cp .env.template .env

# 3. Start PostgreSQL via Docker Compose
docker compose up -d

# 4. Initialize / migrate the database
./venv/bin/python -m execution.db.init_db
```

## Running the App

```bash
# Option A: Makefile shortcut
make dev

# Option B: Direct uvicorn
./venv/bin/uvicorn execution.api.main:app --reload --port 8000
```

Access points:
- App UI: http://localhost:8000
- API docs (Swagger): http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Environment Variables

Loaded from `.env.local` first, then `.env` (first wins for duplicate keys).

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql://recipes_user:recipes_pass@localhost:5432/recipes_db` | Database connection string |
| `SECRET_KEY` | `fallbacksecret` | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token lifetime in minutes |
| `DEMO_HOUSEHOLD_ID` | `1` | Household ID treated as read-only |

For tests, `DATABASE_URL=sqlite://` is set automatically by conftest; you never need to configure it.

## Database Management

```bash
# Start Postgres
make db

# Init / migrate
make init

# View migration history
./venv/bin/alembic history
./venv/bin/alembic current
./venv/bin/alembic upgrade head
```

`init_db.py` runs Alembic migrations and auto-adopts legacy databases that predate Alembic.

## Tools / Scripts
- `execution/db/database.py` — Engine, session factory, `get_db` dependency
- `execution/db/init_db.py` — Alembic migration runner
- `execution/db/models.py` — All SQLAlchemy ORM models
- `execution/api/main.py` — FastAPI entry point (mounts routers + serves frontend)
- `docker-compose.yml` — Local PostgreSQL container
- `Makefile` — Shortcuts: `dev`, `db`, `init`, `test`, `test-cov`, `test-e2e`, `test-e2e-mobile`

## Architecture Notes
- FastAPI serves both the API and the static frontend (mounted at `/`). No separate frontend dev server.
- The frontend lives in `frontend/` (pure HTML/JS/CSS, no build step).
- CORS is wide open (`*`) during development.
- Database uses SQLAlchemy with Alembic for schema migrations.

## Edge Cases & Learnings
- If Docker uses the older standalone command, use `docker-compose` instead of `docker compose`.
- The `{{ }}` placeholder guard in `database.py` and `auth.py` converts unresolved template variables to safe defaults.
- The app does **not** auto-migrate on startup. Always run `make init` after pulling schema changes.
