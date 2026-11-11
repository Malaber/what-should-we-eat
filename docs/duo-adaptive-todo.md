# MISC-12: adaptive Onionary workspace

Sources: [MISC-12](https://turniere.atlassian.net/browse/MISC-12) and
[Tracy PR 31](https://github.com/Malaber/tracy/pull/31).
Keep the current PR and release objective; implement each item separately, then
run integrated checks. No retries, quota resets, or overwritten release tags.

- [ ] Keep recovery banners outside native tab containers; expose reachable navigation on Duo/iPad.
- [ ] Use compatible runtime/device selection and explicit iPhone, Duo and iPad test coverage with Xcode 27.1.
- [ ] Cooking: adaptive coordinated ingredients/instructions panes, one adventure, retained active step and scroll context, accessible controls.
- [ ] Recipes: adaptive list/detail preview; selection never starts cooking; explicit Cook/Resume, Edit and Share; retained selection when collapsing.
- [ ] Kitchen: adaptive plan/shopping panes, stable shopping identities and checks, explicit refresh, local-state disclosure.
- [ ] Editor: adaptive metadata/ingredients and instructions, preserve draft/focus when resizing; functional sheets and keyboard.
- [ ] Duo fold/resize continuity tests and compact/iPad regression; use typed accessibility queries and avoid unnecessary terminate/relaunch.
- [ ] Review screenshots and accessibility in light/dark, EN/DE, large text and Reduce Motion; record any unverified pose matrix honestly.
- [ ] Run full regression, publish a fresh tag/build and launch signed TestFlight delivery after fixes.

Tracy lessons: safeAreaInset outside TabView can obscure adaptive navigation;
use dedicated banner layout space. Select hittable navigation buttons and assert
destination. Scope queries to typed lists/fields, avoid lazy whole-tree queries.
Use one launch for fold/marketing scenarios. Explicit termination only for actual
persistence tests, after backgrounding to SpringBoard. Hinge changes must never
modify domain state; layout is driven by local geometry, not device model.

Banner implementation follows Tracy #31: dedicated VStack space, never a safe-area
inset wrapped around TabView. Geometry drives workspace changes; session state
stays owned by the existing store/editor. Compatibility-aware simulator selection
supports explicit Duo and iPad device types rather than removing those targets.

## Integration checkpoint

Xcode 27.1 `build-for-testing` passes for arm64 and x86_64 simulator targets,
including the Duo test harness. Python 3.14 runtime selection regression tests:
2 passed. Shell syntax, Python compilation and `git diff --check` pass.

Implementation commits cover all four adaptive workspaces. Final UI validation
remains pending; the checklist above deliberately stays open until execution and
visual review. Duo tests exercise 0/90/180-degree folds, cooking undo/redo,
non-mutating previews, editor drafts, shopping refresh/checks and auth navigation.
They attach host-captured outer/inner display images for inspection. Full iPhone
and iPad regression suites run separately. No retries or weakened assertions.

Follow-up integration fixes split editor expressions for Swift type checking,
restore step ordering controls, retain step focus anchors, refresh selected recipe
previews from the store, and fix actor isolation in the fold test harness. Release
and screenshot jobs select Xcode 27.1 and compatible simulator runtimes. Local
TestFlight delivery runs all three device profiles before signing/uploading.

Still unverified: final UI results, visual fold screenshots, VoiceOver, large text,
Reduce Motion, the complete language/theme matrix, and accepted TestFlight upload.

## Build 16 / CI infrastructure follow-up

- [x] Match Tracy's `xcode-27` runner and verify exact Xcode 27.1 build in UI, archive and screenshot jobs (macos-26 only has Xcode 26.x).
- [x] Fail early with an actionable disk-space error before simulator/build creation; test the guard without allocating disk.
- [x] Disable build indexing for automation; preserve test results while removing disposable successful-build caches between release profiles.
- [ ] Re-run CI and start a fresh immutable TestFlight build after local disk space is available.

Build 16 failed before tests/archive/upload: `No space left on device`. All ten
reported CI failures stopped at Xcode selection, not app assertions. Backend,
browser and HTML checks passed. No retries or test suppression are appropriate.

Validation: four focused Python 3.14 tests passed (disk boundary, exact Xcode
version/build and compatible runtime selection). Local Xcode verification passed;
real disk preflight correctly refused at 0.8 GiB, before creating a simulator.
No local TestFlight restart is safe until at least 15 GiB is available. CI uses
Tracy's xcode-27 runner for all three native job types; final run remains pending.

## Native regression follow-up

- [ ] Remove duplicate Duo timeout flags and test constructed xcodebuild arguments.
- [ ] Select visible native navigation controls on iPad; assert destinations without assuming one accessibility match.
- [ ] Diagnose missing save confirmation from xcresult and exercise disabled AI creation after scrolling it into view.
- [ ] Fix creative dependency installation timeout without job retries.
- [ ] Remove only disposable test simulators/build caches; preserve logs, archives and user data. Restart a fresh TestFlight release after focused checks.

Failure evidence: xcresult showed the reload dialog as a popover containing only
its destructive action; the cancel-role keep-progress button was omitted. Use a
native alert so both choices remain explicit on every size class. iPad navigation
queries now select the hittable match; AI creation test scrolls the actual form
before asserting its empty-input disabled state. Duo timeout options are emitted
once; three shell-entry-point regression cases exercise each profile's arguments.
Seven focused Python tests pass.

Cleanup removed three shutdown test-only simulators (Planini E2E, Turniere iPad
verification, Tracy Duo review) and generated Xcode/Onionary build caches. Logs,
xcresult evidence, archives, normal simulators and app/source data were retained.
Free space rose from 1.8 to approximately 16 GiB after deletion settled.

Shared creative fix: https://github.com/Malaber/github-workflows/pull/4. Caller
pins its immutable commit for CI validation; PR is not merged automatically.

## Build 17 follow-up

- [ ] Use stage-specific disk reserves: full release start, one disposable simulator profile, and archive; test boundaries. Build 17 passed iPhone but incorrectly reapplied the initial 15 GiB reserve before iPad.
- [ ] Prevent keyboard dismissal from moving sheet controls during their tap; retain iPad deletion/import regressions with the keyboard open.
- [ ] Synchronize Duo navigation with hittable controls after fold transitions; split independent tag browsing and editor placeholder tests to keep each focused and bounded.
- [ ] Give cold compilation its own adequate budget; retain bounded test execution and no retries.
- [ ] Compile, push replacement CI and publish a new immutable TestFlight build.

Build 17 evidence: the local iPhone suite passed in 1092 seconds; the next profile
was rejected at 11.9 GiB because the initial 15 GiB reserve was reapplied. Reserve
checks now distinguish release start (12 GiB), one isolated test profile (8 GiB),
and archive (6 GiB), reflecting the observed roughly 4 GiB profile footprint. Each
profile still deletes its simulator/build cache and retains its xcresult. All
three profile suites remain required; iPad runs first and status names the profile.

CI evidence: one iPad cold build exhausted 600 seconds before app compilation
finished; its compile-only budget is now 1200 seconds, with enclosing job/step
budgets covering boot, compile and tests. One iPhone test reached its final Cancel
action at 180 seconds; split independent tag and placeholder scenarios instead of
increasing test allowance. Duo's fold controller returns before accessibility
layout is stable; navigation now waits for a hittable button, never retries taps.

Keyboard dismissal previously called endEditing synchronously inside the window
tap recognizer. Form sheet controls could move during touch delivery. UIControls
and semantic buttons are excluded, and background dismissal runs after the touch.
Existing deletion/import tests retain their keyboard-open assertions. Ten focused
Python tests pass; native validation and final delivery remain pending.

## Build 18 CI follow-up

- [x] Replace Add recipe and Cooking options toolbar menus with native action dialogs. Both failed iPhone runs spend two minutes waiting for menu animation completion; preserve actions and existing behavioral assertions.
- [x] Clamp fold pane dimensions when keyboard/reserved regions exceed available geometry; preserve scroll access in split panes.
- [x] Background before explicit persistence-test termination, following Tracy's lifecycle handling.
- [ ] Compile and start all device checks, push PR fixes, then attempt a fresh immutable TestFlight release. Do not retry failed tests or wait idle for suites.

Evidence: PR run 42211483335 stalls opening Add recipe; tag run 42211476153
stalls opening Cooking options. Local Duo spindump shows an idle application main
thread while XCTest waits for quiescence. These fixes require fresh device runs;
no all-green or TestFlight delivery claim until those complete.

Focused validation: 31 Swift tests (22 XCTest + 9 Swift Testing), including
keyboard-clipped/offscreen hinge cases, and 10 Python CI-harness tests passed.
Full simulator suites and the screenshot launch case remain pending.

## Release disk preflight correction

- [x] Align release entry reserve with the first sequential test stage (8 GiB), retaining per-profile checks, post-profile build cleanup and the 6 GiB archive check.
- [x] Test the 8 GiB boundary and the reported 12.53 GB available-space case (10 focused tests passed).
- [ ] Publish fresh rc.20/build 20 and complete background TestFlight delivery.

The initial 12 GiB check incorrectly blocks a release that satisfies every stage's
own reserve. Profiles execute serially and delete DerivedData before the next.
Three local Time Machine snapshots retain recently removed cache blocks; do not
remove backups as part of temporary build cleanup.

## Build 20 Duo failures

- [x] Select the declared simulator runtime exactly, including when a newer runtime is installed; cover incompatibility/missing-runtime failures without fallback.
- [x] Avoid booting/indexing a disposable simulator during compilation; boot after build-for-testing and before UI tests.
- [x] Include fold-controller error bodies in XCTest failures and host logs, so HTTP 500 cannot hide a spawn timeout.
- [ ] Run focused harness regressions, push PR fixes and start fresh rc.21/build 21; leave long device suites running.

CI run 42898506468 fails with HTTP 500 after a fold screenshot; the job declares
27.1 but selects installed 27.2. Local build 20 passed iPad, then its Duo runner
aborted in XCTest accessibility initialization: main thread loading UIKit's
accessibility bundle through dyld, before any test method. No archive or upload.
Do not hide this infrastructure failure by skipping Duo or retrying tests.

The local bootstrap mitigation requires a fresh full run; no claim that the
XCTest framework crash is proven resolved. Duo now runs first locally for earlier
feedback, with iPad and iPhone still required before archive/upload.

Integrated harness validation: 19 tests passed; shell syntax checks passed.
Actual installed selection verified as iPhone 17 Pro/iOS 27.0 and Duo/iOS 27.1.

Build 21's immediate startup verification found macOS Bash 3 rejecting an empty
runtime-argument array under `set -u`. Use a scalar optional runtime argument;
regression cases now run the shell entry point with both an explicit CI version
and an unset local override, with successful and failed builds. Build 21 never
reached simulator tests. Changed harness requires a fresh rc.22/build 22.

## Build 22 reliability follow-up

- [x] Diagnose failed iPhone share-link screen and preserve the full create/revoke regression.
- [x] Keep one simulator fold helper alive for the scenario instead of spawning/loading IOKit for every fold; bound acknowledgements and test failure propagation without retries.
- [x] Align screenshot capture with build-before-boot staging and bounded commands; retain real UI capture and exact asset validation.
- [ ] Check generated release artifacts/storage before the next immutable build; keep existing successful device evidence and all test requirements.

CI fold diagnostics now confirm repeated `simctl spawn` timeouts, plus a separate
`simctl io screenshot` timeout. Screenshot job fails launching Onionary via Xcode.
Local build 22 passed Duo and iPad, then correctly stopped at 7.17 GiB before the
8 GiB iPhone stage. No archive/upload occurred.

Failed iPhone hierarchy/video showed Create link still enabled, no error and no
link after its tap. Creation now uses an explicit full-width 44-point button,
inline sheet title and immediate busy state. Full create/revoke assertions remain.

Validation: 30 focused harness tests passed; native helper compiled and five real
Duo fold commands were acknowledged by one process. Full app UI/marketing runs
remain pending; these results do not prove every simulator launch issue resolved.

## Build 23 startup follow-up

- [x] Use one bounded `simctl bootstatus -b` operation to boot and monitor the disposable device; remove the separate unmonitored boot call from both harnesses.
- [x] Set screenshot appearance through the Debug marketing fixture instead of a global simulator appearance RPC; retain production appearance behavior.
- [x] Test boot/setup failure propagation and run a real cold-device readiness check before publishing a fresh release attempt.

Both failing runs printed "Device already booted, nothing to do" before their
first UI operation stalled. iPad capture timed out in `simctl ui appearance
light`; iPhone timed out launching Onionary before account-deletion actions.
These are startup failures, not failed account-deletion assertions. Do not relax
those assertions or the existing UI-test deadlines.

Validation: 33 focused harness tests passed; shell syntax and whitespace checks
passed. A fresh iPhone 17 Pro / iOS 27.0 reached terminal Finished in 40 seconds
using the single boot operation, then launched Settings successfully. The test
simulator was removed. Full app suites and TestFlight build 24 remain pending;
this readiness probe does not establish that all UI tests pass.
