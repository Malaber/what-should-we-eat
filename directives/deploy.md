# Deploy — Directive

## Goal
Build, push, and deploy the application as a Docker container.

## Docker Image

```bash
docker build -t what-should-we-eat .
```

The Dockerfile:
- Uses `python:3.12-slim`
- Installs Python deps, copies `alembic/`, `execution/`, and `frontend/`
- Runs `uvicorn execution.api.main:app --host 0.0.0.0 --port 8000`

## Required Environment Variables (Production)

| Variable | Notes |
|---|---|
| `DATABASE_URL` | Full PostgreSQL connection string |
| `SECRET_KEY` | Strong random key for JWT signing |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` (24h) recommended |
| `DEMO_HOUSEHOLD_ID` | ID of the read-only demo household |

## Database Initialization

The container does **not** auto-migrate on startup. Run:

```bash
docker exec <container> python -m execution.db.init_db
```

This applies all pending Alembic migrations.

## CI/CD (GitLab)

`.gitlab-ci.yml` defines three stages:

1. **test** — Unit tests (SQLite, `python:3.12-slim`)
2. **e2e** — Playwright e2e tests (desktop + mobile)
3. **build** — Docker build & push to `$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA`

Build stage runs only on `main`.

## Production Deployment (Hetzner)

The app is deployed via an Ansible role in a separate `ansible-deployment` repo:
- Uses Traefik for TLS certificates (Let's Encrypt via Hetzner DNS challenge)
- Docker Compose on the target host
- Subdomain: configured in the Ansible inventory

## Tools / Scripts
- `Dockerfile` — Container build spec
- `docker-compose.yml` — Local Postgres only (not used in production)
- `.gitlab-ci.yml` — CI/CD pipeline
- `alembic/` + `alembic.ini` — Schema migrations

## Edge Cases & Learnings
- The frontend is baked into the Docker image (no separate CDN/nginx needed).
- Alembic `init_db.py` auto-stamps legacy databases that predate migration tracking.
- The `{{ }}` placeholder guard in `database.py` and `auth.py` converts unresolved Ansible/template variables to safe defaults to prevent crashes.
