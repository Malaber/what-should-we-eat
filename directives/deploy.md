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

The image runs only the Python application over HTTP on port 8000. It does not
terminate TLS or auto-migrate. `deploy/compose.test.yml` runs a one-shot migration
service after Postgres is healthy, and starts the API only after it succeeds.
`docker compose up -d` handles this ordering on initial deployment and updates.
Outside that Compose setup, run `python -m execution.db.init_db` using the app
image and database environment before starting the API.

## CI/CD (GitHub)

`.github/workflows/ci.yml` tests the backend, browsers, and iOS app before
publishing AMD64/ARM64 images to `ghcr.io/malaber/what-should-we-eat`.
The development branch publishes `development` and immutable `sha-<full commit>`
images. Git tags control release versions; PR checks never publish images.
See `docs/development-deployment.md` for deployment and release commands.

## Production Deployment (Hetzner)

The app is deployed via an Ansible role in a separate `ansible-deployment` repo:
- Uses Traefik for TLS certificates (Let's Encrypt via Hetzner DNS challenge)
- Docker Compose on the target host
- Subdomain: configured in the Ansible inventory

## Tools / Scripts
- `Dockerfile` — Container build spec
- `docker-compose.yml` — Local Postgres only (not used in production)
- `.github/workflows/ci.yml` — CI/CD pipeline
- `deploy/compose.test.yml` — Postgres, migrations, and HTTP API behind existing Traefik
- `alembic/` + `alembic.ini` — Schema migrations

## Edge Cases & Learnings
- The frontend is baked into the Docker image (no separate CDN/nginx needed).
- Alembic `init_db.py` auto-stamps legacy databases that predate migration tracking.
- The `{{ }}` placeholder guard in `database.py` and `auth.py` converts unresolved Ansible/template variables to safe defaults to prevent crashes.

- Match Planini's existing Traefik defaults: `traefik_external`, `websecure`,
  and `lets-encr`, configurable via `TRAEFIK_*` environment variables.
- Do not bundle another reverse proxy or publish host ports in the test stack.
  Traefik owns TLS; the API alone joins its external Docker network.
