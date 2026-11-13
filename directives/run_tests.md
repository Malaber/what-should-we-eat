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
Resolve a multiline input by its identifier and supported text roles in one
query. Do not enumerate all TextFields/TextViews and retain a global array index
while a sheet is being presented. Verify keyboard focus and the actual entered
value before checking derived results.
Derive expected editor text before typing, then await that exact accessible
value before folding, saving or checking persistence. `typeText` can return
while the field is still committing characters; reading the field immediately
afterwards must not define the expected value. Keep the exact-value assertions
after each display transition as well.
For committed text, add `value == expected` to the already scoped native field
query and use its normal five-second `waitForExistence`. Keep an independent
exact `field.value` assertion afterward. Do not wrap `field.value` in an outer
XCTNSPredicateExpectation: on a slow host, that timer can expire while the nested
AX lookup is still in flight. At 50c7361 the failed iPhone edit's recording and
app-side accessibility snapshots both showed the correct "Edited pasta" value.
The native query avoids that additional client-side timer without increasing a
deadline, removing a value assertion, bypassing keyboard/fold behavior or retrying
input. Pantry text and Duo draft entry use the same contract.
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

For persistence UI tests, press the system Home button and verify SpringBoard
reaches foreground. Resolve a fresh `XCUIApplication` for the background process,
terminate it once if still running and verify `.notRunning`. Create another
fresh `XCUIApplication` for the relaunched process. Copy arguments/environment without
`--reset`; reuse device data and keep every restoration assertion. Do not reuse
an automation handle whose process was terminated.

All UI profiles inherit `OnionaryUITestCase` and share synchronous process
cleanup in `tearDownWithError`. XCTest's synchronous UI lifecycle hooks run on
the main thread; `MainActor.assumeIsolated` enforces that contract. An actor hop
from async teardown stalled after an async case failed; the synchronous hook
was verified to return to SpringBoard and terminate the failed app. Keep
feature scenarios independent: tag filtering, pantry matching and Intelligence
options each have their own case, fixture and unchanged per-case deadline.
Editing with preserved cooking progress and temporary share-link lifecycle also
have independent cases. Keep their complete user outcomes and assertions;
do not combine unrelated flows until cleanup consumes the case's deadline.
Step placeholder insertion/keyboard-toolbar dismissal and contextual help are
separate native cases, each using the normal editor route and cleanup. At
64e39f4 the combined test completed every feature assertion but reached teardown
at 179.149 seconds of its 180-second allowance. Keep all assertions, including
the exact placeholder value, toolbar disappearance, help presentation/dismissal
and editor cancellation. Do not infer a product failure from that exhausted
combined scenario, raise its timeout or remove shared lifecycle cleanup.
Checklist undo/redo, fractional input/outside-tap dismissal/steppers and cold
restoration likewise have separate cases. The restoration case still enters
1.583945 through the keyboard, creates a checked/undo history, terminates and
relaunches the real process, then verifies checked state, 1.58× display and
persisted `Undo · Checked`. The dedicated fractional case retains outside-tap
keyboard dismissal and plus/minus checks. Use the `apply-portions` identifier
for sheet confirmation; a keyboard Done button is a different action. Await the
exact field value before confirming and use a directly indexed keyboard query.
Duo preview/checklist folding, editor draft folding and kitchen shopping folding
also have independent cases. Establish the starting hinge pose for each fixture:
resetting app data does not reset physical device posture. Keep the full
checklist 0/180/90/180/0/180 sequence, draft 0/90/180 sequence and shopping
0/180 sequence, plus exact values and real undo/redo/cancel/refresh interactions.
Do not grow one end-to-end scenario until host speed determines whether it fits
its deadline. Keep the 360-second Duo case and 1800-second suite limits.
Address the reload choice through the presented native alert, and verify an
actual checked ingredient survives choosing to keep cooking progress.
Ordinary navigation resolves a single indexed accessible button, then checks
existence/hittability. Do not enumerate windows and all matching controls inside
a short predicate wait: those AX RPCs can consume the budget before evaluation.
iPad's floating navigation is not exposed as an XCTest `TabBar` in this SDK.
Recipe selection waits for the exact actionable row inside the named list;
cached recipes must remain selectable without waiting for a refresh-state RPC.
Pull-to-refresh still verifies refresh completion. Avoid global lazy `firstMatch`
queries during split-view navigation.
Use synchronous MainActor test methods for native UI scenarios. Do not mix
blocking XCTest control queries/waits with async test methods: a Duo preview
query stalled in that execution model. Pure async core tests are unaffected.

Session renewal has its own foreground lifecycle contract. The Debug backend
accepts the initial access token, records a real didEnterBackground notification,
then rejects that token after willEnterForeground. The production foreground
refresh must renew it while retaining cooking progress. This fixture is driven
by lifecycle events, never elapsed time or request counts. Use Home followed by
activate on the same running application; verify checked progress before/after,
renewed expiry, account/email and no passkey prompt, then return to Cooking and
verify the check again after renewal completed. Full termination/disk restoration
and offline-draft relaunch remain separate native scenarios. Do not add a second
cold launch to foreground renewal: the old fixture renewed before progress was
entered, then a slow CI terminate/relaunch consumed its three-minute deadline.

Inspect XCTest action timelines and retain logs/xcresults. Do not add retries,
sleeps or skip feature failures. Run xcodebuild with `-collect-test-diagnostics
never`: it disables verbose simulator-wide sysdiagnose, not XCTest results,
failure attachments or command logs. That collector stalls after passed tests
and consumes disk. Request a separate OS diagnostic explicitly when needed.
On failure, test.sh invokes collect_ios_test_diagnostics.py before disposing its
owned device. The collector records CPU/RAM, VM/swap state, device/runtime
inventory and recent CoreSimulator events. Every read command runs once with a
five-second deadline and a 64 KiB retained tail; the collector has a separate
60-second wall-clock cap. Its failure cannot replace the test's original exit
code. It never restarts a simulator/test or mutates unrelated devices.
Keep host evidence distinct from feature failures: at 282aa5a one CI simulator
entered Shutdown and terminated runner/app together before any hinge injection;
the other CI case finished its feature assertions but exceeded six minutes.
The host sample had 3 CPUs and 7 GB RAM. That establishes capacity, not the cause
of the shutdown. Do not claim memory pressure without evidence, or enable a
billable larger runner without user approval.

Do not edit a shell script while a local process is executing it. Bash may read
later commands using stale file offsets. Freeze local script copies before
launch or finish the run before editing. CI checkouts are immutable during tests.

Local release/test profiles run sequentially and reuse one build cache while
retaining separate xcresults. Keep the 8 GiB test-entry and 6 GiB archive guards;
report GB/GiB accurately. Finder may include purgeable capacity, and APFS/Time
Machine can retain deleted blocks. Do not delete backups to force tests through.
Wait for the previous test command to return, including disposable-device
cleanup, before starting the next profile. A finalized xcresult alone does not
mean its simulator has been deleted or its disk reserve has been released.

Runtime installation is not selection. Pass SIMULATOR_RUNTIME from the matrix;
require the exact compatible runtime/build from execution/ios_runtime.py:
27.0/24A434 for phone/tablet and stable 27.1/24A94425 for Duo. Apple's catalog
identifies 24A94232 as the 27.1 RC; do not silently substitute it. RC/stable can
coexist under one OS identifier. Select the compatible build's absolute runtime
bundle path when creating the disposable device, regardless of inventory order.
For matching SDK versions, ensure_ios_runtimes.py checks CoreSimulator's SDK
mapping too. It may set `simctl runtime match set iphoneos27.1 24A94425 --sdkBuild
<sdk-build>` only on disposable GitHub-hosted runners, then verifies the result.
Local/self-hosted preferences are never changed automatically: a mismatch fails
with the explicit command for a developer to review. Never delete runtimes to
force selection. Catalog reference:
https://devimages-cdn.apple.com/downloads/xcode/simulators/index2.dvtdownloadableindex

Before creating a device, resolve_simulator.py validates ProductVersion and
ProductBuildVersion in the selected bundle's
Contents/Resources/RuntimeRoot/System/Library/CoreServices/SystemVersion.plist.
Missing or mismatched metadata is terminal before any device is created.
Compile against the shutdown disposable simulator, then call bounded
`simctl bootstatus <id> -b` once, followed directly by XCTest. Do not insert
`simctl getenv` or `simctl spawn` readiness/metadata probes after boot: the added
getenv gate at 2bb8b14 stalled on all six cold CI guests before any UI test ran,
despite passing on a warm local simulator. Native runner class setup records
ProcessInfo.operatingSystemVersionString in the retained test log, in-process
after XCTest initializes. This log is evidence, not a host-side boot gate.
Preserve original command failures and owned-device cleanup. Caller-supplied
devices are neither booted nor deleted by test.sh. Keep all profiles mandatory,
with no latest/RC fallback or new test retries/deadlines.

Duo injects its simulator-only HID event directly in the XCTest bundle using
DuoHinge.m, following the in-process approach documented by Appium's
XCUIDevice+FBHinge. It is never linked into the app/extensions. No host helper,
HTTP server, port file or startup handshake. Initialization uses dispatch_once;
a failure is terminal. Wait for active-display geometry after each dispatch and
retain all fold/checklist/draft/navigation assertions. Duo's app-level frame
can remain 669×951 while rotated window/control frames are 951×669. Check
physical-display edge lengths separately from control visibility: compare button
frames with the persistent primary window's frame, reject empty/nonfinite/
offscreen controls, then require real hittability. Keyboard-window indices can
change during folding: never enumerate and re-query them by array index inside
the readiness wait. Resolve a control directly with
`buttons.matching(identifier: title).element(boundBy: 0)` and use XCTest's native
existence wait, then check geometry once. Existence, geometry and native
`wait(for: \.isHittable, toEqual: true, timeout: remaining)` share one monotonic
ten-second control-readiness deadline. Existence/valid frames can precede touch
readiness after a fold. Never substitute repeated taps, fallback queries or a
longer case deadline. If still unreachable, retain one active-app screenshot
and hierarchy before failing; an outer-display recording can be black while
the inner display is active. Scope recipe rows to the named recipe list.
Do not put window/snapshot/frame RPCs or
`allElementsBoundByAccessibilityElement` inside a short custom visibility
predicate: the predicate's first evaluation alone can consume its deadline.
The current Duo SDK dropped TabContent accessibility identifiers after folding
in a local experiment, while retaining native tab labels. Keep the existing
app tab rendering and query those labels; do not add ID/label fallback retries.
A failed wait captures one coherent hierarchy and normal XCTest attachments.
Source reference:
https://github.com/appium/appium-ios/blob/main/packages/webdriveragent/WebDriverAgentLib/Categories/XCUIDevice%2BFBHinge.m

Marketing capture runs once per device inside the normal UI suite. After that
suite passes, export its four attachments with marketing_screenshots.py
--result-bundle. Reject missing/duplicate/unknown scenes, bad dimensions and
undecodable PNGs. The CI caller then invokes screenshots.yml as a reusable
workflow to render with Malaber/github-workflows, bundle and attach main-release
assets. Never start another simulator/test run just to obtain the same images.
Keep the app's fixture appearance preference and actual system status bar;
avoid cosmetic SpringBoard RPCs. Screenshot controls expose localized values.

Pull-to-refresh gestures target the named recipe list and await its accessible
loaded state. Portion buttons have full 44-point hit areas. For automatic
activity failures, first verify the triggering recipe change. Lifecycle policy
is tested through CookingActivityBackend; retain requested handles independently
of system discovery, serialize updates/stops and keep real ActivityKit UI tests.

Native output goes directly to retained build.log/tests.log via run_bounded.py
--log, with a bounded console tail. Keep exit codes and process/test deadlines.

Backend/browser CI use Ubuntu 24.04 and configure_ci_apt.py, with signed keyring,
security suites, strict updates and zero retries. Archive reference:
https://archive.ubuntu.com/ubuntu/dists/noble-security/Release

During CI-only stabilization, run test profiles without archive/upload. Defer
release tags and TestFlight until the user requests them again.
