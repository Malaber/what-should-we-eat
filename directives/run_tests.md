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

For persistence UI tests, activate SpringBoard and verify it reaches foreground
before terminating Onionary; verify `.notRunning` before relaunch. This detaches
the foreground accessibility session without sleeping or retrying the test.
Inspect XCTest's action timeline when a deadline expires: time spent waiting for
animation completion is distinct from an application main-thread hang. Preserve
spindumps and xcresults; do not increase deadlines to hide repeated idle waits.

Local TestFlight runs profiles sequentially and deletes each successful profile's
DerivedData. Its entry disk reserve therefore equals one test profile (8 GiB),
with another check before every profile and 6 GiB before archive. Do not sum the
space for all three device builds. Report decimal GB and binary GiB explicitly;
Finder may include purgeable capacity. Time Machine snapshots can retain blocks
from deleted caches; do not delete backups as part of build-cache cleanup.

Runtime installation is not runtime selection. CI must pass SIMULATOR_RUNTIME
from its matrix; the selector requires that exact compatible runtime and never
falls back to a newer installed release. Local defaults match the CI profiles
(27.0 phone/tablet, 27.1 Duo). Compile against the shutdown disposable device,
then boot and await bootstatus before XCTest, avoiding overlapping cold compiler
work and simulator first-boot indexing. Keep all device tests mandatory and
preserve bootstrap crashes separately from failures inside test methods.

Duo fold commands reuse one simulator-only IOKit helper process, with bounded
READY/angle acknowledgements. Timeout, exit or malformed acknowledgement kills
the session; never retry the command. Capture fold evidence using XCTest's app
screenshot connection, not a newly spawned simctl screenshot process per angle.
Marketing capture also separates build-for-testing, boot readiness and one bounded
test-without-building invocation. Keep UI assertions and artifact dimensions intact.

For a new shutdown simulator, call `simctl bootstatus <id> -b` once under the
boot deadline. Do not issue `simctl boot` first and only then attach the monitor:
that can take the "already booted" path before the first UI operation. Marketing
light appearance belongs to the Debug fixture's existing appearance preference;
avoid a global SpringBoard appearance RPC solely to render that fixture.

Screenshot fixtures set app appearance through the app preference, with an explicit
localized accessibility value on the picker. Do not assume SwiftUI menu pickers
expose their selected text as an accessibility value automatically. Capture the
real system status bar; do not make screenshots depend on cosmetic `simctl
status_bar` overrides. Validate captures and app behavior as before.

When an automatic activity assertion fails, inspect the recording and first
assert the triggering recipe change. A missed portion tap cannot start an activity;
do not diagnose ActivityKit from the final toggle value alone. Portion controls
need full rectangular hit areas of at least 44 points, including in scaling forms.

Native xcodebuild output goes directly to retained build.log/tests.log files via
run_bounded.py --log. Only a bounded tail reaches the console. Keep logs alongside
xcresults in CI artifacts, including failures before XCTest starts. Preserve
command exit status and the existing process/test deadlines; no test retries.
Use explicit app teardown between UI cases, keyboard readiness before typing,
and dismissal before navigating behind a sheet.

Local releases reuse one release-specific DerivedData directory across sequential
device profiles while keeping separate xcresults. This avoids repeated cold
compilation/deletion and APFS snapshot disk churn. Do not lower free-space guards
or delete Time Machine snapshots to force a release through.

Duo must resolve its test bundle from the exact `-derivedDataPath` supplied to
xcodebuild, including a shared release cache. Validate this before spawning the
helper. Run `run_duo_tests.py --prepare <results>` before boot, then start the
prepared helper after boot. A dispatched fold is not a completed display handoff:
wait for the expected active-display geometry before UI queries (Tracy PR 31).
Pull-to-refresh tests gesture on the named recipe list, not a recipe Button, and
wait for the list's accessible loaded state before selecting a row.

Backend/browser CI use Ubuntu 24.04 and configure_ci_apt.py. The canonical Ubuntu
archive serves noble-security as well as base/updates; keep signed keyring and
security suites, strict update errors and zero retries. Reference:
https://archive.ubuntu.com/ubuntu/dists/noble-security/Release

Duo control service starts the native helper on POST /ready only after XCTest
has launched Onionary and observed its initial UI. Bootstatus alone does not
establish that the simulator event system can start this helper. A failed READY
remains terminal; do not restart it. Give the HTTP request enough time to return
the existing 20-second native deadline's error, preserving XCTest deadlines.

Live Activity lifecycle decisions are unit-tested through CookingActivityBackend;
retain successful request handles independently of the platform discovery list,
serialize updates/stops, and keep real ActivityKit UI coverage. When the user
requests CI-only stabilization, run test.sh profiles without the archive/upload
wrapper. Defer release tags and TestFlight until requested again.
