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

Ordinary UI fixtures also isolate ActivityKit through UITestCookingActivityBackend
and the existing CookingActivityBackend protocol. They still execute the real
CookingActivitySession, automatic starts, updates and toggle logic. Do not start
OS Live Activities for every recipe checklist/portion test: their system state
outlives an app-process reset and can animate SpringBoard during unrelated UI.
The mandatory testLiveActivityStartAndStop explicitly launches with
--system-live-activity and uses real ActivityKit, including automatic start and
the final Off assertion. testCookingModeWithFixtureBackend runs the same full
cycle against the fixture separately. Both cases must pass on ordinary profiles;
neither is skipped or accepted as a replacement for the other. Release builds
exclude the fixture and always construct the Apple backend. There are 27 ordinary
UI cases and six Duo cases after adding this coverage.

Follow the global GitHub CI Monitoring and Automatic Fixes workflow. Complete
local checks, commit/push, then use an attached, bounded shell watcher:
`gh pr checks --watch --fail-fast --interval 15`. Capture the PR URL/head SHA,
wait for check registration in the shell, and verify the same SHA plus every
expected downstream check before reporting success. Never treat missing checks
as success or use repeated model queries/polling agents. The primary model reads
failure logs and fixes underlying problems; the shell handles waits. Repeat for
each new commit until green or a concrete blocker needs user input. Do not merge.
Feature branches run the complete workflow through pull_request, avoiding a
second identical push pipeline. main, codex/onionary-ios-companion and v* tags
retain push validation/publication; workflow_dispatch remains available. All
three native profiles, backend/browser/HTML/archive and screenshot gates remain.

The headless build-for-testing command uses ENABLE_DEBUG_DYLIB=NO; test execution
uses its validated compiled manifest directly. Developer previews and Release archive settings stay
independent. Validate the actual built app before boot: executable Mach-O,
bundle-local entry point, no Preview/debug-dylib artifacts. This avoids the extra
Preview stub loader in repeated native cold launches; it is not a launch retry,
longer timeout or substitute for a successful native run. The b2f7503 Duo failure
occurred in dyld dependency loading before app initialization, while the Xcode
launch-status reply arrived after XCTest's internal deadline. Preserve those
diagnostics rather than calling it a shopping-list assertion failure. All cases,
runtime pins and crash checks remain mandatory.
https://developer.apple.com/documentation/xcode/build-settings-reference

Use native app.typeText after explicitly focusing a text field and verifying the
keyboard. Keep exact value assertions. This applies to portion inputs as well as
recipe names: b2f7503 iPad's retained stack identified multiplier.typeText in
enterFractionalPortions as the remaining field re-resolution stall. Keep both
fractional-keyboard/stepper and cold cooking-restoration scenarios intact; do not
remove keyboard visibility checks or replace input with direct value injection.
The same focused app-level input applies to pantry, account email, manual draft,
search and import fields; retain their real taps and exact value checks. Before
cold-restoring an offline draft, wait for Cancel to remove its editor and for the
saved row to appear. Keep the full Home/termination/relaunch flow. Verify the
restored name with waitForValue's native `value == expected` predicate: that
single query requires both field existence and complete string equality, rather
than an existence query followed by a redundant broad value RPC during sheet
presentation. Keep the offline error, enabled Save and 180-second case bound.
For tag results, use tag-recipes-list/close-tag-recipes to identify the presented
native sheet. Wait for the list to disappear after Done, then resolve new tag and
result-row elements on reopening. Do not retain their remote handles across
sheet dismissal/recreation. Keep both presentations, the final result selection,
actual dismissal checks and the original waits/case budget; no repeated taps.

Run native tests once with `bash ios/Onionary/Scripts/test.sh`; do not enable
test retries. The script uses isolated DerivedData and writes an xcresult bundle.
Build-for-testing emits one validated arm64 .xctestrun file. Run that artifact
with -xctestrun and the existing full-profile selector, not -project/-scheme:
the latter reopens project/package resolution even with test-without-building.
Validate the UI target, screenshot policy and compiled app/runner/bundle paths;
missing, ambiguous or filtered plans fail before boot.
Runner initialization has a separate 600-second limit. The unchanged
1800-second UI-suite budget begins at the first literal "Test Suite 'Selected
tests' started at " log line. Missing suite registration never counts as success;
failed command statuses are preserved and either phase terminates its process
group on timeout. Total command time is bounded by 2400 seconds plus termination.
Per-case 180/360-second limits and workflow timeouts remain unchanged. This keeps
platform startup out of the UI budget without retrying or skipping a test.
Reference: https://developer.apple.com/library/archive/technotes/tn2339/_index.html
CI sets `TEST_RESULTS_DIR` and uploads that bundle even when tests fail.
The generated Xcode scheme explicitly selects preferredScreenCaptureFormat:
screenshots. Apple's default is video, and collect-test-diagnostics=never does
not disable its per-test recording lifecycle. Keep normal crash detection and
automatic failure screenshots, plus all explicit keepAlways screenshots used by
marketing and fold diagnostics. Do not disable crash detection, remove feature
assertions or replace them with a recorder workaround. After xcodegen, validate
the actual generated scheme with check_ios_build_environment.py --test-scheme;
missing capture mode, disabled screenshots or filtered/skipped UI targets must
fail before simulator work. XcodeGen omits the default automatic-capture flag;
that absence means captures remain enabled, not disabled.
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
For the editing-progress scenario, read the original name before focusing. Tap
the actual field and verify the keyboard, then use app.typeText to dispatch real
key events to that focused descendant. Re-resolving a field during typeText can
stall while the keyboard's remote AX process transitions. Keep the exact committed
field value, save/keep-progress choice, retained checks and updated list entry.
Never inject the field value directly or accept typing without focus.
The folded draft uses the same app.typeText contract after tapping Name and
awaiting the keyboard; its full expected text remains asserted after every fold.
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

All UI profiles inherit `OnionaryUITestCase`. Each UI scenario calls launch()
with its own reset fixture; XCTest terminates any existing app instance before
that clean launch. Do not insert another global Home/terminate transaction in
teardown. Explicit Home/termination/relaunch remains inside persistence cases,
with every saved-state assertion. The outer script still deletes its owned
simulator on success/failure. Keep feature scenarios independent: tag filtering,
pantry matching and Intelligence
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
combined scenario or raise its timeout. Use the shared XCTest launch contract.
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
Ordinary navigation resolves a single indexed accessible button, waits for
existence and taps that actual element once. Standard element.tap() synchronizes
and computes its own hittable point. Do not add a second computed isHittable
preflight before the action or use coordinate/forced-tap fallbacks. All resulting
navigation/state assertions remain mandatory. Duo resolves a unique button
through the primary window (retaining named recipe/shopping-list scopes), not
through application-root bounds. After hinge injection/orientation, require both
the expected natural app viewport and the primary window's actual orientation
within the existing 15-second geometry allowance. Correct edge lengths alone do
not prove the receiving window finished rotating. Capture the window through
XCTest for fold diagnostics: application-root captures can be entirely black on
the inner display. A black capture does not itself prove touches targeted the
wrong display; inspect the retained synthesized event's displayID and coordinates.
Keep native value readiness and an independent exact state assertion after
Undo/Redo. On mismatch retain the window capture and full hierarchy; do not retry
the action or substitute a coordinate tap.
Duo actions resolve through their actual containing window. Native menus and
sheets may have another window; do not assume every action belongs to index zero.
Cooking options uses a native Menu in the toolbar. Its non-destructive actions
do not need a toolbar-owned confirmationDialog; only restart asks for destructive
confirmation on the stable cooking view. Keep the real folded options → Edit
route, with no direct-editor fixture shortcut. Intelligence queries stay within
intelligence-form and its navigation bar; Cancel uses cancel-intelligence and
must remove the form and return to Recipe book.
Transient recent-action feedback owns its state/timer in CookingHistoryBar,
not CookingView. Expiring that banner must not update the view owning an open
toolbar menu. Keep its four-second lifetime, animation/reduced-motion handling
and Undo/Redo/History unchanged. Native coverage includes both immediate edit
selection and an open menu surviving feedback expiry, followed by one Edit tap,
editor cancellation and the original checked ingredient. Await actual feedback
disappearance; never retry a lost menu tap or bypass the menu to open the editor.
That one regression opts into ActionFeedbackClock's Debug-only manual signal
with a unique ONIONARY_TEST_FEEDBACK_CLOCK notification name. The real banner
stays visible until the test opens the native menu, then one notification expires
it through the normal state/animation path. Keep every assertion and the same
eight-second disappearance wait. Slow AX queries must not race the production
four-second wall clock. Other fixtures and Release use the real cancellable
four-second delay. Unit tests cover notification completion, observer disposal,
replacement cancellation and default cancellation. No server or file polling.
The ordinary profile now contains 27 required cases; Duo retains six.
Do not enumerate windows and all matching controls inside
a short predicate wait: those AX RPCs can consume the budget before evaluation.
iPad's floating navigation is not exposed as an XCTest `TabBar` in this SDK.
Recipe selection waits for the exact actionable row inside the named list;
cached recipes must remain selectable without waiting for a refresh-state RPC.
Pull-to-refresh verifies its exact Recipes loaded value through the scoped
native query. Live Activity On/Off checks use the same native-value query and
retain independent exact-value assertions; do not wrap them in a client-side
expectation. Use the named recipe-list for recovered draft rows, wait for the
exact row, then tap. Avoid global lazy firstMatch queries across the whole suite.
Text entry must commit its full expected value before a dependent action.
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

On disposable GitHub-hosted macOS runners, ensure_ios_runtimes.py also prepares
the exact installed runtime's dyld shared cache before any device is created.
Use simctl runtime dyld_shared_cache update for the validated pinned bundle,
without --force/--all. An existing cache is a no-op; a failed or timed-out cache
operation fails setup once. Never generate or remove developer/self-hosted
caches. This is host runtime preparation, not a post-boot guest RPC, app warm-up,
test retry or replacement for real cold launches. Keep native execution limits.
The 2dd04d2 Duo launch failed before the app existed in its retained system
sample, with the launch-status reply missing XCTest's internal deadline; merely
removing the Preview stub did not resolve that platform startup failure.
Supported operation reference: xcrun simctl help runtime.

Duo injects its simulator-only HID event directly in the XCTest bundle using
DuoHinge.m, following the in-process approach documented by Appium's
XCUIDevice+FBHinge. It is never linked into the app/extensions. No host helper,
HTTP server, port file or startup handshake. Initialization uses dispatch_once;
a failure is terminal. Wait for active-display geometry after each dispatch and
retain all fold/checklist/draft/navigation assertions. Duo's app-level frame
can remain 669×951 while rotated window/control frames are 951×669. Check
physical-display edge lengths separately from control visibility: compare button
frames with the persistent primary window's frame, reject empty/nonfinite/
offscreen controls, then perform a standard native element tap. Keyboard-window indices can
change during folding: never enumerate and re-query them by array index inside
the readiness wait. Resolve a control directly with
`buttons.matching(identifier: title).element(boundBy: 0)` and use XCTest's native
existence wait, then check geometry once and tap the element once. At 1a1680b
the additional isHittable property wait itself raised an activation-point error
before any touch, despite normal bounds in the shopping-list. Native tap owns
the synchronized hit test and scrolling; a failed native touch still fails the
case. Do not substitute repeated taps, raw coordinates, fallback queries or a
longer deadline. Keep all fold/checklist/navigation/shopping outcomes. Geometry
failures retain an active-app screenshot/hierarchy; XCTest retains native action
failure attachments. Outer-screen recordings can be black on the inner display.
Scope recipe rows to recipe-list and shopping controls to shopping-list.
Resolve a Duo button directly through the app/scoped list, then resolve its
receiving window only for geometry validation. Do not nest the button query
under app.windows.containing(that same button): d40fc76's shopping case timed
out recursively expanding Window → contains ingredient-1 → Button. Preserve
the unique .element query, frame validation and one native tap; menus/sheets
still use their actual receiving window rather than primary-window geometry.
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

For shared native-harness changes, focused cases are diagnosis, not a publish
gate. Use execution/verify_ios_pr.py on a clean, committed codex/ branch. It
creates a detached checkout of the exact commit and runs complete iPhone/iPad
profiles sequentially through test.sh, with separate results and one build cache.
Its --push-branch option is explicit opt-in: only after both suites pass may it
fast-forward the development branch to the tested SHA. A failed profile, changed
HEAD/branch, dirty source or rejected push prevents a published-success status.
It never pushes main/tags, retries tests, merges, archives or uploads TestFlight.
Read --status with the same --output path. Do not edit the candidate branch while
this gate runs; changes invalidate publishing. Full stable-runtime Duo CI is
still required after publication; the local gate does not substitute an RC.
CI sets Python 3.14 before native preflight/tests and archive validation; the
local verifier puts its own interpreter directory first in child PATH.

Primary XCTest contracts:
https://developer.apple.com/documentation/xcuiautomation/xcuiapplication/launch()
https://developer.apple.com/documentation/xcuiautomation/xcuielement/tap()
