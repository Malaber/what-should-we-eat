# what-should-we-eat — Tasks

## Backend: PostgreSQL + FastAPI
- [x] Database layer
  - [x] `docker-compose.yml` — PostgreSQL service
  - [x] `execution/db/models.py` — SQLAlchemy ORM models
  - [x] `execution/db/database.py` — engine, session, base
  - [x] `execution/db/init_db.py` — table creation script
- [x] API layer
  - [x] `execution/api/main.py` — FastAPI app
  - [x] `execution/api/schemas.py` — Pydantic models
  - [x] `execution/api/routers/recipes.py` — CRUD + filter + random
  - [x] `execution/api/routers/tags.py` — list tags
  - [x] `execution/api/routers/shopping_list.py` — aggregate ingredients
- [x] Config & dependencies
  - [x] `requirements.txt`
  - [x] `.env.template` update
- [x] Directive
  - [x] `directives/manage_recipes.md`
- [x] Cleanup
  - [x] Remove example scaffold files
- [x] Verification
  - [x] Smoke test script — all 20 tests passed ✅
