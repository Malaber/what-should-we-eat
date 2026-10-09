# Run Tests — Directive

## Goal
Run unit tests, end-to-end tests, and code coverage against the application.

## Prerequisites
- Dependencies installed (`pip install -r requirements.txt`)
- For e2e: Playwright browsers installed (`playwright install`)
- No running database required — tests use in-memory SQLite

## Unit Tests

```bash
# Standard run
make test

# With coverage report
make test-cov
```

Equivalent to:
```bash
python3 -m pytest execution/tests/ -v --tb=short
python3 -m pytest execution/tests/ -v --tb=short --cov=execution --cov-report=term-missing --cov-report=html
```

Coverage output goes to `htmlcov/`.

### Test Configuration
- `pytest.ini` — Sets `testpaths = execution/tests` and ignores `execution/tests/e2e/` by default
- `execution/tests/conftest.py` — Sets `DATABASE_URL=sqlite://`, creates/drops all tables per test, provides `client`, `auth_headers`, and `second_user_headers` fixtures

### Unit Test Files
| File | Covers |
|---|---|
| `test_health.py` | `/health` endpoint |
| `test_recipes.py` | Recipe CRUD, filters, random selection |
| `test_recipe_import.py` | HTML parsing, Chefkoch import, household-to-household import |
| `test_users.py` | Registration, login, `/users/me` |
| `test_households.py` | Create, join, switch, leave, cleanup |
| `test_meal_plan.py` | Meal plan add/replace/delete, cooked status |
| `test_shopping_list.py` | Ingredient aggregation |
| `test_tags.py` | Tag listing, case-insensitivity |

## End-to-End Tests (Playwright)

```bash
# Desktop browser
make test-e2e

# Mobile (iPhone 13 viewport)
make test-e2e-mobile
```

Equivalent to:
```bash
python3 -m pytest execution/tests/e2e/ -v --tb=short --screenshot=only-on-failure --video=retain-on-failure --output=test-results
python3 -m pytest execution/tests/e2e/ -v --tb=short --device="iPhone 13" --screenshot=only-on-failure --video=retain-on-failure --output=test-results
```

### E2E Architecture
- `execution/tests/e2e/conftest.py` — Starts a uvicorn server in a background thread on a random port, resets DB tables per test
- Tests use Playwright to interact with the actual frontend in a real browser
- Failures produce screenshots and videos in `test-results/`

### E2E Test Files
| File | Covers |
|---|---|
| `test_e2e_auth.py` | Sign up, log in, logout via UI |
| `test_e2e_households.py` | Create/join/switch households in UI |
| `test_e2e_kitchen.py` | Kitchen/cooking flow |
| `test_e2e_meals.py` | Meal picking and planning flow |
| `test_e2e_recipes.py` | Recipe management via Manage Recipes page |

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs Python 3.14 backend tests,
desktop/mobile Chromium tests, packaged PostgreSQL smoke tests, and native iOS
simulator tests. Native tests include a Debug-only deterministic API transport;
release builds exclude it. Test fixtures set required IMPRESSUM operator values.

Do not poll GitHub jobs while idle; the user will return with results. Complete
local checks and record their evidence in the PR first.

Run native tests once with `bash ios/Onionary/Scripts/test.sh`; do not enable
test retries. The script uses isolated DerivedData and writes an xcresult bundle.
CI sets `TEST_RESULTS_DIR` and uploads that bundle even when tests fail.
Keyboard tests must first assert that the keyboard is visible, then wait for
the expected dismissal state; an immediate `exists` check can race the animation.
Outside-tap handlers must survive SwiftUI view replacement and attach when their
view actually enters a window, rather than relying on a single queued callback.

## Tools / Scripts
- `execution/tests/conftest.py` — Unit test fixtures and auth helpers
- `execution/tests/e2e/conftest.py` — E2E server setup and DB reset
- `execution/tests/helpers.py` — Shared test utilities
- `Makefile` — All test commands
- `.github/workflows/ci.yml` — CI pipeline definition

## Edge Cases & Learnings
- Unit tests are isolated: tables are created and dropped per test, so test order doesn't matter.
- E2e tests spin up a real uvicorn server with `port=0` (OS-assigned port) to avoid conflicts.
- `DEMO_HOUSEHOLD_ID=99999` in tests prevents accidental collision with test-created households.
- SQLite in-memory uses `StaticPool` so all sessions share the same DB instance across threads.
