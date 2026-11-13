# CI stabilization before TestFlight

User requested CI-only work. Do not create release tags, archive/upload locally,
or start a TestFlight worker until separately requested. Preserve all feature
assertions and current deadlines; no retries, sleeps or skipped failures.

- [x] Fix Duo helper startup ordering: both failed jobs time out waiting for READY before XCTest even starts. Initialize the single helper on the first fold request after the app is running, with failure cleanup and no retries.
- [x] Diagnose/fix iPhone Live Activity and silent-renewal failures from the full result log and recording, with focused native regressions.
- [ ] Test orchestration, run affected native cases, update PR with evidence and push CI fixes. Full CI remains pending until GitHub results arrive; do not poll while idle.

Build 27 completed its local device suites/archive but failed Apple account
access during export. That is recorded only as context; upload work is deferred.

Earlier implementation (superseded where noted by the structural follow-up below):

- Duo uses an explicit /ready handshake after the first app screen exists. One
  helper session starts once; failed startup cannot retry. The HTTP deadline
  allows the existing bounded native acknowledgement to return diagnostics;
  native test deadlines stay unchanged.
- Live Activity retains the actual successful request object rather than relying
  on immediate system-list discovery. Six deterministic lifecycle regressions
  cover delayed discovery, no duplicates, denial, recipe/account changes, external
  ending and a delayed update followed by stop. Real ActivityKit UI tests remain.
- Silent renewal waits for the named recipe list and exact row before selecting
  it. Renewal/persistence assertions remain unchanged.
- 45 Python harness tests and 37 Swift core tests passed. Native app/UI-test
  targets compiled after a scoped ActivityKit Swift 6 interop correction.
- Full iPhone/Duo/iPad runtime verification and fresh GitHub checks remain pending.
  No release tag or TestFlight upload is authorized in this CI-only round.

## Structural follow-up after recurring failures

- [x] Remove the Duo host process/HTTP sidecar. Inject folds inside the XCTest runner using the existing simulator-only HID event format; preserve all continuity checks and device geometry waits.
- [x] Use a fresh XCUIApplication object after each intentional termination/relaunch; retain the same on-device files, arguments and progress assertions.
- [x] Export marketing captures from the normal UI suite's xcresult. Remove the second screenshot simulator/test launch and its inconsistent outer deadline; preserve all four captures, dimension checks, shared renderer, bundles and release attachments.
- [ ] Validate actual native folds/relaunch, artifact export and workflow wiring before push. No TestFlight or new release tag.

Evidence: both previous/current Duo failures are in the host helper startup/RPC,
not fold assertions. iPad renewal now fails at app.launch after termination with
"does not have a process ID". The screenshot case is killed by a 300-second
outer deadline after long XCTest startup, while its own test has not reached its
180-second deadline. The same marketing case already runs in the normal suite.
Local full iPhone suite passed; the local batch stopped on disk reserve before
Duo, so it never established Duo/iPad runtime success.

- [x] Disable verbose simulator-wide sysdiagnose collection (not test results or attachments). A successful three-case Duo run still launched `simctl diagnose --timeout=600` and device `log collect`, consuming time/disk after XCTest passed. Retain normal xcresults, failure screenshots, command logs and all test deadlines/assertions.

Structural verification in progress:

- Direct native Duo: three cases passed on a fresh simulator. A frozen-script
  rerun with verbose diagnostics disabled also passed all three, exit 0; it did
  not invoke the post-success sysdiagnose collector. No fold/state assertion was
  removed. The obsolete sidecar and its transport-only unit tests were retired.
- Actual xcresult export produced all four original iPhone captures and the
  marketing composite without starting another simulator. Eight exporter tests
  cover device dimensions, missing/duplicate scenes, PNG decoding and preserving
  existing outputs. Workflow calls/dependencies validated with actionlint 1.7.7.
- Current harness/export regression suite: 41 passed. Swift core: 37 passed.
- Native symbol check: hinge injection is present only in the XCTest bundle,
  absent from the app binary. Expanded Duo diagnostic screenshots can be blank
  in this SDK; functional geometry/interaction assertions remain the CI gate.
  This does not claim a physical-device visual review.
- Local wrapper mutation was corrected by freezing the executing shell script.
  Never edit a running script; the frozen run above is the clean harness result.
- iPad targeted native restoration: all three cases passed, exit 0 (cooking
  scaling/checks/history, offline draft recovery, silent session renewal).
- Export also rejects failed, skipped and empty native suites before rendering.
  The real successful-result export and workflow lint both passed. Main releases
  upload this run's verified bundles directly; no capture redispatch.
- Final GitHub checks remain pending until the pushed revision completes. No
  TestFlight run or release tag was created. Full CI success is still required.

## Remaining query/readiness failures

- [x] Split the combined tag/pantry/AI test into independent feature cases, retaining its assertions. CI completed its actions at 178.9 seconds then exceeded the 180-second allowance during teardown; keep the allowance unchanged.
- [x] Centralize recipe selection through the named list and indexed identifier query, replacing global firstMatch lookups that can stall during navigation.
- [x] Inspect Duo navigation snapshot frames and prevent probing hidden/invalid activation points while retaining real hittability checks and all navigation assertions.
- [ ] Verify these exact cases locally, lint workflows and push CI-only fixes. Full GitHub gates remain required; no tags/uploads.

Current diagnosis uses both branch and PR runs at b49ddec. The iPhone PR job
passed; the branch job reached AI cancellation at 178.9 seconds, then hit the
180-second limit during teardown. iPad PR stalled resolving a global recipe row;
Duo branch failed probing an invalid navigation activation point after a fold.
All three have separate regression targets; no feature assertion is removed.

Harness/export checks: 41 passed. Workflow lint and whitespace checks passed.
Native verification remains in progress; do not treat compilation alone as a
passed scenario. New local geometry checks caught a too-strict axis assumption
and an unreachable folded toolbar control before push. Preserve those results
and inspect actual accessibility frames before changing geometry policy again.

Measured Duo correction: after rotation, application bounds were 669×951,
window bounds 951×669 and the visible toolbar control was at x=884. Visibility
now compares coordinates with actual windows; the display-edge check remains
separate. A native regression covers this exact geometry plus hidden/invalid
frames. All real hittability and fold/state assertions remain. The deliberate
failed diagnostic also proved synchronous cleanup finishes immediately instead
of stalling in async teardown.

Current native app/test targets compile. Full four-case Duo verification runs
locally, followed sequentially by iPad edit/share + silent renewal and the three
split iPhone features. Status: `.tmp/ci30-local-status.json`; results/logs stay in
`.tmp/ci30-*-verified` and `.tmp/ci30-*-focused`. This batch has no retries,
archive/upload steps or release tags. It stops if Duo fails or test sources
change. Native results and fresh full GitHub gates remain pending at push.

## Snapshot cost and process lifecycle follow-up

- [x] Replace the generic multi-snapshot visibility poll in ordinary tab navigation with one indexed accessible-button query; retain actual hittability and existing deadlines. The five-second predicate spent its budget obtaining window and button snapshots before checking candidates.
- [x] Resolve recipe-list readiness without a second full-list accessibility snapshot; inspect expired-session state and keep offline cooking/reauthentication assertions.
- [x] Diagnose the iPad termination error from the recorded app/process sequence, implement one deterministic lifecycle transition, and keep all persisted progress assertions.
- [ ] Run focused native regressions, update evidence and push without tags/TestFlight. Leave longer suites running rather than polling GitHub.

At d8ac7f7, Duo passed both full CI jobs and all four local cases. The local
iPad follow-up never started: its disk guard observed 7.75 GiB while the Duo
device was still being disposed. Current CI failures are ordinary navigation,
expired-session list readiness and one iPad termination RPC. Both iPad edit/share
scenarios now pass. Full gates remain required.

Verification at 0d146d7 (no app functionality or feature-case bodies changed):

- Native iPad 27.0: all four affected cases passed, zero failed/skipped. Covers
  multiple-tag filtering, tag navigation, offline cooking with passkey renewal,
  and silent session renewal with restored checked progress. Full command exited
  0 and disposed its own simulator before the following profile started.
- Local verification rejected an XCTest TabBar-only selector: iPad's floating
  navigation has a different accessibility role. The final selector resolves
  the indexed accessible button directly and still requires hittability.
- All 21 ordinary feature scenarios and their assertions are byte-identical to
  d8ac7f7. Only shared query/process helpers changed; existing deadlines remain.
- Navigation avoids window enumeration and bulk matching snapshots inside the
  short wait. Recipe selection requires the exact hittable cached row, while
  pull-to-refresh retains its completion assertion.
- Lifecycle sends one system Home action, resolves a fresh background process,
  terminates once if still running and verifies it stopped. The old automation
  handle is not queried again after termination. Relaunch preserves device data.
- 37 Swift core tests and 41 Python harness/export tests passed. Actionlint and
  whitespace checks passed. No retries, skipped feature cases or deadline changes.
- Focused iPhone Intelligence/expired-session/renewal checks run in background;
  status is `.tmp/ci31-local-status.json`. Full fresh GitHub gates remain pending.
  No TestFlight work, archive or release tag is part of this CI-only round.

## Remaining dynamic keyboard/window lookups

- [x] Replace pantry input's enumeration of every TextField/TextView with a direct identifier query; keep quantity/missing-ingredient assertions and the 180-second limit.
- [x] Remove dynamic window-index enumeration from Duo readiness. Read coordinates from one stable primary window and resolve controls directly; retain geometry/hittability gates and all fold/draft/shopping assertions.
- [ ] Exercise pantry entry and the complete Duo fold/edit/cancel flow locally; update evidence, push and leave full CI running. No retries, skipped tests, larger deadlines, tags or uploads.

At 30e995e all three branch native jobs and both screenshot render/bundle jobs
passed. Both iPhone CI runs passed, and all three local focused iPhone cases
passed. The PR iPad pantry case spent roughly 100 seconds resolving a previously
enumerated multiline input before completing its feature assertions at 179
seconds. Duo failed cancelling the editor after a keyboard/fold transition:
window indices became stale while enumerating three windows. The saved
hierarchy shows the enabled Cancel control inside the visible landscape window.

Verification at 42b300b:

- Native iPad pantry: passed, zero failures/skips. Resolves the multiline input
  by identifier plus text role, verifies keyboard focus and exact input, retains
  both missing/insufficient quantity assertions and sheet dismissal.
- Native Duo: all four cases passed, zero failures/skips. The complete cooking
  case passed in 124.1 seconds, including preview, repeated folds, undo/redo,
  editor keyboard/fold/cancel with preserved draft, and shopping checks.
- Duo reads the persistent primary window rather than a changing window array.
  Candidate controls bind to AX identity; the first usable candidate is retained
  and tapped without repeating the scan. Failure diagnostics capture one full
  hierarchy. No index-bound bulk enumeration remains in UI tests.
- 37 Swift core tests and 41 harness/export tests passed; workflow lint and
  whitespace checks passed. Existing feature assertions and deadlines remain;
  pantry adds focus and exact-input assertions.
- The previous branch/PR test trees were identical (9bab7fb8cee24781dbb2d4da3b1a34dd8397f5ef),
  excluding merge-content differences as the source of those failures. Prior
  iPhone focused verification completed successfully: all three cases passed.
- An additional local settings→pantry pair runs in background to exercise the
  exact preceding language/appearance scenario from CI. Status:
  `.tmp/ci32-local-status.json`. Full fresh GitHub gates remain pending.
- No retries, skips, increased deadlines, local archive, TestFlight or tag.

## Edit/share scenario scope

- [x] Split editing and link creation/revocation into independent native cases, preserving existing assertions and the 180-second allowance. The combined branch-iPad case finished assertions at 177.48 seconds, then timed out during cleanup.
- [x] Scope the keep-progress action to the presented reload alert and verify an actual checked ingredient survives saving the edited recipe.
- [ ] Verify both cases locally, update PR evidence and push CI-only changes; leave longer suites running. No retries, skipped behavior, release tags or TestFlight.

At 0803b92 every PR check passed, including all native profiles, archives and
screenshot render/bundle jobs. The only branch failure is the combined
edit/share case. The previous background settings→pantry pair also passed both
cases. The combined case spent over 40 seconds resolving the global
keep-progress button before completing edit, sharing and revocation assertions.

Current verification:

- iPad: both independent cases passed, zero failures/skips, command exit 0.
  Editing/preserved progress took 71.3 seconds; sharing/revocation took 29.1.
- Existing editor labels, old cooking snapshot, persisted edited name, actionable
  link creation/revocation and sheet-dismissal assertions remain. Editing adds
  keyboard/typed-value checks, alert dismissal and a checked ingredient verified
  before and after saving. The keep action is scoped to the native reload alert.
- Ordinary native suite now has 22 cases; each retains the 180-second allowance.
  No retry, skipped behavior or increased deadline. Other feature cases and
  all Duo cases are unchanged.
- 37 Swift core and 41 harness/export tests passed; workflow lint and whitespace
  checks passed. The earlier background settings→pantry sequence passed both cases.
- Additional iPhone edit/share cross-check runs in background; status is
  `.tmp/ci33-local-status.json`. Fresh full CI remains the merge gate.
  No TestFlight, local archive or version tag was created.

Local cross-check follow-up: the extra iPhone process stopped at preflight,
before compiling or running tests, because 7.76 GiB was below the 8 GiB guard.
Removed redundant downloaded CI zip files and four old generated test-result
directories; current logs/results, build cache and archives were retained.
Available capacity remained below the guard. No native test was retried or
counted as passed. The additional local phone result is unverified; full fresh
GitHub native gates remain mandatory. The verified iPad pair is unaffected.

## Native Duo selection contract

- [x] Evaluate explicit TabContent identifiers. Local Duo inspection proved this SDK drops those IDs after folding while retaining labels; reject the app-side experiment before push and retain existing native tab rendering.
- [x] Replace Duo's custom visibility predicate/bulk snapshots with direct identifier queries and native existence waits. Retain frame validity, real hittability, physical-display geometry and every feature assertion.
- [x] Run Duo test methods synchronously, matching ordinary UI tests, rather than mixing async MainActor methods with blocking XCTest waits. Keep existing case/step deadlines and all fold sequences.
- [x] Await the complete intended editor input before starting folds. The local synchronous run captured an expected suffix of "Du" while typing was still committing; after folding, the actual field correctly contained the complete "Duo draft" suffix. Derive the expected value before typing and verify it, rather than treating a partial snapshot as expected data.
- [ ] Validate actual Duo behavior and ordinary navigation locally; record results and push CI-only fixes. No retries, skipped behavior, timeout increases, local archives, tags or TestFlight.

At 0d74733 both iPhone and iPad jobs passed in branch and PR runs. Both Duo
jobs failed in the custom visibility layer despite visible navigation controls;
its window/snapshot/frame RPCs consumed the ten-second predicate allowance.
The PR cooking case also stalled at a synchronous preview query inside its async
test method and was terminated. There is no failed recipe/checklist assertion
in that trace. These observations motivate direct native selectors and one
synchronous UI execution model, rather than another timing adjustment.

Current verification:

- The corrected app and native test target compile successfully with Xcode 27.1.
  The final diff leaves app tab rendering unchanged. Direct native queries replace
  the entire custom visibility scan; geometry and hittability remain required.
- 37 Swift core and 41 Python harness/export tests passed; workflow lint and
  whitespace checks passed. Existing feature assertions and case/step limits
  remain. Exact committed-input waits also cover ordinary editing and pantry entry.
- The first local experiment exposed both the dropped TabContent identifiers and
  the partial expected-input snapshot. It failed and is not counted as a passed
  run. The following attempt stopped at the disk guard before building or testing.
  Removed only the regenerable task build cache; source, logs, results, user data,
  backups and signed archives were retained.
- Corrected full Duo verification completed successfully on a fresh disposable
  simulator: all four cases passed, zero failures/skips, in 182.0 seconds.
  Logs/result: `.tmp/ci34-duo-final-labels/`. The boot tool returned zero but
  logged a data-migration warning. Both ordinary native profiles subsequently
  passed in branch and PR CI; the remaining Duo host/scope failures are below.
- No retries, skipped feature cases, deadline increases, tags or TestFlight.

## Duo scenario isolation and host evidence

- [x] Separate preview/checklist folding, editor draft folding and kitchen shopping folding into independent native cases. Keep every current feature assertion, the full angle sequences, native interactions and the 360-second per-case / 1800-second batch limits.
- [x] Capture bounded host/simulator evidence on native failure before disposing the owned simulator. Include CPU/RAM, VM statistics, exact device inventory and CoreSimulator shutdown messages; never restart tests, modify unrelated devices or replace the original failing exit code.
- [ ] Verify the diagnostics tool with deterministic subprocess fixtures, compile/run the changed native cases and update PR evidence. Leave long verification running with an estimate; no idle GitHub polling, archive, tag or TestFlight.

At 282aa5a all four local Duo cases passed (182.0 seconds total, zero failures),
and both CI runs passed every ordinary iPhone/iPad, backend/browser and archive
job. The two remaining failures are distinct:

- Branch: runner and app received SIGTERM together during the first Recipes tap.
  Xcode's session log confirms the simulator entered Shutdown, then failed to
  read TESTMANAGERD_SIM_SOCK. No feature assertion or hinge dispatch had failed.
  The available artifacts do not identify who initiated the shutdown.
- PR: the combined case completed preview, checklist folds, editor/draft folds
  and shopping assertions at 399.9 seconds, then failed during cleanup. The
  result reports the unchanged six-minute limit. UI reads took up to 17 seconds.
  The retained sample shows a 3-core, 7 GB VM; the app's main thread was servicing
  its run loop, not stuck in application code. Resource pressure is a hypothesis,
  not a proven cause of the separate simulator shutdown.

The combined scenario's scope is too broad for a useful, bounded failure. Split
its independent outcomes rather than extending deadlines. Host failures must
remain failures and retain evidence. A larger runner is billable and is not
enabled by this change.

Current verification:

- 55 harness/export tests passed, including real timeout/nonzero-output capture
  and shell-entry-point failures at compilation, boot and native execution.
  Unavailable/failing diagnostics retain the original exit code and still delete
  only the script's owned device. No failed native case is retried.
- The actual CI entry point (`ios/Onionary/Scripts/test.sh`) passed Swift core
  checks, compilation and all six Duo cases: zero failures/skips in 269.6 seconds.
  Logs/results: `.tmp/ci35-duo-isolated.log` and
  `.tmp/ci35-duo-isolated/Onionary.xcresult`. Both following Duo CI jobs also passed.
- Shell syntax, workflow lint and whitespace checks passed. Full fresh GitHub
  gates remain required; no idle polling, archive/upload, release tag or billable
  runner change is included.

## Foreground session renewal contract

- [x] Exercise silent renewal after real background/foreground activation, with the test backend expiring its access token only after backgrounding. Verify checked cooking progress before and after renewal, renewed access expiry, identity and absence of a passkey prompt.
- [x] Keep the separate full process-termination restoration test and offline-draft restart test unchanged. These cover cold disk restoration; do not combine a second process launch with the foreground-renewal scenario.
- [ ] Run the native renewal regression with its preceding share-link scenario on iPad; retain existing deadlines/assertions and update evidence. No retries, skipped cases, billable runners, release tags or TestFlight.

At 382e99f both Duo CI jobs passed, as did the full six-case local Duo suite
(269.6 seconds, zero failures). iPhone and all non-iOS checks passed. The PR iPad
run passed 21 of 22 cases; only silent renewal exceeded its three-minute limit.
Its mid-case termination took 44 seconds and relaunch took over 60 seconds.
Progress, renewed expiry, account/email and no-prompt assertions subsequently
completed, but the test had already exceeded its deadline. The branch iPad job
was cancelled, not a feature-test failure.

The old fixture rejected the first token immediately at startup, so renewal
occurred before cooking progress was entered. Restarting the app renewed another
fresh fixture token. Replace that indirect sequence with a deterministic server
expiry after backgrounding, then assert real foreground renewal preserves the
existing adventure. Full termination/disk restoration remains independently
tested by testCookUndoScaleAndRestoreAfterTermination and offline draft recovery.

Current verification:

- Updated Debug app and native test bundle compile with Xcode 27.1. The fixture
  observer is compiled out of Release builds. Production renewal logic is unchanged.
- Focused native iPad share-link→renewal verification is running once on a fresh
  disposable simulator; completion is not yet claimed. Logs/results:
  `.tmp/ci36-ipad-renewal/`. All original renewal assertions remain, with checked
  progress additionally verified before backgrounding and after renewed expiry.
- Separate cold-termination restoration and offline-draft restart scenarios are
  unchanged. The ordinary suite remains 22 mandatory cases; no retries, skipped
  behavior, larger test deadlines, billable runners, tags or uploads.
- Shell syntax, workflow lint and whitespace checks passed. Existing 55 harness
  checks and the six-case local/both-CI Duo results remain valid; full fresh
  GitHub checks are still the merge gate.

## Native committed-value queries

- [x] Replace the custom XCTNSPredicateExpectation around element.value with a native query matching the exact expected value, then use the existing five-second native existence wait. Keep separate exact-value assertions before saving/folding and all feature checks.
- [x] Apply the query contract to recipe-name entry, pantry text and Duo draft entry. Keep keyboard/fold coverage; do not dismiss the keyboard to bypass a failing value check.
- [x] Verify iPhone editing with its preceding cold-restoration case and pantry entry, plus Duo draft folding. Local runs passed: three iPhone cases in 122.3 seconds; Duo draft in 72.2 seconds. Update PR evidence; no retries, skipped assertions, longer deadlines, tags or uploads.

At 50c7361 every PR check passed, including all native profiles and both creative
screenshot render/bundle paths. The only branch failure was the iPhone edit
case's custom committed-value expectation (21/22 ordinary cases passed). Its
recording shows "Edited pasta" correctly entered; retained app-side AX logs also
report value "Edited pasta" while that wait fails. The value lookup continued
after the outer expectation's timer expired. This is a synchronization failure,
not evidence that the app lost or altered input.

Match value in the native element query instead of evaluating element.value
through a second client-side expectation. Retain the independent exact-value
assertion, save/reload choice, checked progress and updated library-name checks.
Previous focused iPad share→renewal verification passed both cases in 89.9 seconds
(renewal 30.4 seconds), zero failures/skips. Both Duo profiles remain green.

Current verification:

- Changed native UI test bundle compiles successfully with Xcode 27.1. No app,
  backend, fixture data, release configuration or test deadline changed.
- iPhone cold-restoration→editing→pantry verification is running once on a fresh
  disposable simulator. Duo keyboard/draft folding is queued after it succeeds.
  Logs/results: `.tmp/ci37-iphone-native-values/` and
  `.tmp/ci37-duo-native-values/`. Completion is not yet claimed.
- Whitespace checks passed. All 22 ordinary cases and six Duo cases remain
  mandatory. The previous full PR native, archive, backend/browser, formatting
  and creative screenshot jobs passed; fresh full CI remains the merge gate.
- No input retries, fallback selectors, skipped assertions, longer deadlines,
  billable runner, archive/upload or release tag.

## Stable runtime build selection

- [x] Replace the Duo RC pin (24A94232) with Apple's stable iOS 27.1 simulator build (24A94425). Share exact pins between installation, selection and runtime verification; retain 27.0/24A434 for ordinary profiles.
- [x] Select the matching runtime bundle path, not the ambiguous OS identifier. Configure the matching SDK build only on disposable GitHub-hosted CI machines, and verify the actual booted runtime build before XCTest. Never silently use the RC, delete existing runtimes or alter local Xcode matching preferences.
- [x] Cover RC/stable coexistence and reversed inventory order, missing/wrong builds, SDK mapping and booted-build mismatches with regression fixtures. Verify supported boot metadata locally.
- [ ] Full stable-runtime native CI gates must pass. No retries, skips, increased test deadlines, billable runner, archive, tag or upload.

At f2d1dd1 the local iPhone restoration/edit/pantry cases passed (122.3 seconds)
and Duo draft folding passed (72.2 seconds), all without failures/skips. Both CI
ordinary profiles and every branch check, including creative screenshot bundles,
passed. The PR's first Duo case was terminated with the entire simulator while
waiting for accessibility, before navigation or hinge dispatch; five later cases
passed after Xcode restarted its runner. This remains an infrastructure failure.

Apple's official simulator catalog identifies 24A94232 as "iOS 27.1 Release
Candidate Simulator Runtime" and 24A94425 as "iOS 27.1 Simulator Runtime".
The failed host's retained inventory has both builds with the same OS identifier.
The installer required the RC and the selector checked version/compatibility but
not build, returning the ambiguous identifier. Xcode's SDK mapping also preferred
24A94232. Pinning an OS version therefore did not establish a stable runtime build.
The shutdown cause is not proven solely by this configuration defect; full native
checks on the corrected build remain mandatory.

Catalog: https://devimages-cdn.apple.com/downloads/xcode/simulators/index2.dvtdownloadableindex

Verification:

- Python 3.14.7: all 84 harness/export/release/preflight checks passed, including
  exact-build selection, RC/stable inventory order, guarded SDK mapping and
  readback, guest metadata and fail-before-XCTest cleanup/exit propagation.
- Shell syntax, actionlint and whitespace checks passed. No app, feature assertion
  or XCTest case/suite deadline changed.
- A real local disposable 27.0/24A434 device accepted the exact runtime bundle
  path and exposed its version/build through SIMULATOR_ROOT. The completed CLI
  integration probe is recorded in `.tmp/ci38-final-runtime-probe.log`.
- Both retained CI 27.1 builds support Duo. Stable 24A94425 is already installed
  on the hosted image, but is absent locally. With approximately 10 GiB free,
  downloading/installing another 7.85 GB runtime would violate the test reserve;
  no download, runtime deletion or local SDK preference mutation was attempted.
- Full corrected-runtime CI remains the merge gate. The passing branch run used
  the same RC as the failed PR run, so the selection correction is not proof of
  the cause or resolution of the external simulator shutdown.

## Remove post-boot guest RPC regression

- [x] Remove the post-boot `simctl getenv SIMULATOR_ROOT` gate introduced at 2bb8b14. All six native jobs (PR and branch) stop at this new gate after compilation/boot succeed; no UI case starts. Do not extend its timeout or retry it.
- [x] Validate the selected exact runtime bundle's SystemVersion metadata on the host before device creation. Retain shared build pins, exact bundle selection and disposable-CI SDK mapping/readback. Record the running OS from inside the XCTest runner without another host-to-guest RPC.
- [x] Cover wrong/missing bundle metadata, pre-create failure, supplied/owned simulator lifecycle and absence of post-boot guest probes. Run the integrated harness; retain every feature assertion and original XCTest deadline.
- [x] Focused real native smoke run passed: portion controls in 27.299 seconds, zero failures/skips; owned-device cleanup completed.
- [ ] Full corrected CI remains required.
- [x] Push to the existing PR with accurate evidence. Leave full CI running; no idle polling, billable runner, release tag, local archive or TestFlight upload.

At 2bb8b14 all backend, browser, HTML and unsigned archive jobs passed. All three
native profiles failed on both events at the newly added runtime verification
command. Four logs explicitly report `simctl getenv` timing out after 15 seconds;
both Duo jobs hit the command's 45-second outer cap. Stable runtime installation,
SDK mapping/readback and exact-bundle selection succeeded. This is a regression
in the new harness, not six independently failing app features. A warm local
guest probe did not establish that this extra cold-host RPC was safe in CI.

Current verification:

- All 87 harness/export/release/preflight checks passed with Python 3.14.7.
  Negative fixtures reject a reintroduced post-boot getenv/spawn/runtime command;
  missing/malformed/wrong bundle metadata fails before device creation. Supplied
  devices are neither booted nor deleted, including after a test command fails.
- Shell syntax, actionlint and whitespace checks passed. All 22 ordinary cases
  and six Duo cases and their existing deadlines remain unchanged.
- Updated native UI bundle compiled successfully with Xcode 27.1. The corrected
  selector validated the local 27.0/24A434 bundle and created a disposable device;
  its bounded boot completed. The unchanged portion-button native case passed in
  27.299 seconds, zero failures/skips. XCTest directly reported `Version 27.0
  (Build 24A434)` in-process. Test command and owned-device cleanup both exited
  successfully. Logs/results: `.tmp/ci39-native-smoke/`.
- Installed-bundle validation replaces the previous host-side booted-guest gate.
  Runtime output from XCTest is diagnostic evidence, not an added startup gate.
  The older warm-guest verification above remains historical, not proof of cold
  hosted reliability. Stable runtime pins and CI-only SDK mapping are retained.

## Step editor scenario budget

- [x] Split the combined step-amount insertion and help-dialog flow into independent native cases. Keep placeholder content, contextual toolbar visibility, keyboard dismissal, help presentation/dismissal and editor cancellation checks; keep the 180-second limit.
- [x] Run both cases consecutively on a fresh iPhone simulator, with normal per-case cleanup. Cold restoration → insertion → help passed all three cases in 129.026 seconds, zero failures/skips; cleanup completed. Integrated harness checks passed and directive/PR were updated.
- [ ] Push the correction, leaving full branch/PR CI as the merge gate. No retries, skipped assertions, longer deadlines, tags, uploads or paid runner change.

At 64e39f4 all PR checks passed, including three native profiles and both creative
render/bundle paths. The sole branch failure was testStepAmountTools; the other
21 ordinary cases passed, and iPad/Duo/archive/backend/browser/formatting passed.
Its retained XCTest timeline reaches editor cancellation and teardown after
every feature assertion. Test starts at 11:47:24.718, teardown starts at
11:50:23.867 (179.149 seconds), Home completes and termination begins at
11:50:24.384. The combined body used almost the entire three-minute allowance,
then cleanup was reported over budget. This is the same broad test-budget/
lifecycle reliability class encountered earlier, not a new product regression
or the removed runtime gate. Retain cleanup, and give each independently useful
editor feature its own scenario rather than raising timeouts or omitting checks.

Evidence: https://github.com/Malaber/what-should-we-eat/actions/runs/43417351715/job/131858677774

Verification at implementation:

- Python 3.14.7: all 87 harness/export/release/preflight checks passed. Shell
  syntax, actionlint and whitespace checks passed.
- Updated native UI target compiled with Xcode 27.1; exact 27.0/24A434 runtime
  selection and bounded boot passed. One focused sequence (cold restoration,
  ingredient insertion, contextual help) is running without retries on a fresh
  disposable iPhone simulator. Logs/results: `.tmp/ci40-native-step-tools/`.
  Its final result and full corrected CI remain pending at this checkpoint.
- Ordinary suite now has 23 mandatory cases; Duo retains six. Every original
  insertion/help/keyboard/cancel check remains, with explicit help-dismissal and
  editor-closure assertions added. Production app/backend code, shared cleanup,
  test fixtures and 180/360-second case / 1800-second suite limits are unchanged.

## Focus cooking persistence and Duo interaction readiness

- [x] Separate checklist undo/redo, fractional input/outside-tap/steppers, and cold fractional-state restoration into focused native cases. Preserve every original assertion, including checked state, 1.58× after process restart and persisted `Undo · Checked` history. Retain real termination/relaunch and normal cleanup. Give the adjustment confirmation a stable accessibility identifier so keyboard and sheet Done buttons cannot be confused.
- [x] After Duo geometry validation, use XCTest's native isHittable property wait within the existing total ten-second control-readiness budget. Preserve existence/frame/hittability checks and single taps. Capture the active app screenshot and one hierarchy if readiness fails; the outer-screen fold recording turns black and cannot diagnose inner-display controls.
- [ ] Run focused iPad checklist/fractional/restoration cases and integrated harness checks. Compile the Duo target; stable local 27.1 is absent, so require real stable-runtime CI rather than silently substituting the RC. Update PR and leave fresh full checks running without idle polling.

At 675d6ea the local cold-restoration → step insertion → help sequence passed all
three cases in 129.026 seconds, zero failures/skips, and owned-device cleanup
completed. Every branch CI check passed, including all native profiles and both
creative bundles. The PR iPhone, backend/browser/format/archive jobs passed.

PR iPad passed 22/23 cases. Its combined cooking case completed undo/redo,
fractional input, outside-tap keyboard dismissal and steppers, then exceeded
three minutes while relaunching. This still combines several independent flows
before the actual persistence checks. Split those checks without replacing the
native cold restart or dropping fractional persistence coverage.

PR Duo passed 5/6 cases. Expired-session navigation passed folded, then Settings
existed and had valid geometry after opening, but one immediate isHittable read
was false. Existence does not establish tappability; use the native property
wait, not a custom visibility predicate, fallback query or repeated tap. If the
control stays inaccessible it must still fail, with useful active-display data.

Evidence:
- https://github.com/Malaber/what-should-we-eat/actions/runs/43430568881/job/131902723876
- https://github.com/Malaber/what-should-we-eat/actions/runs/43430568881/job/131902723809
- https://developer.apple.com/documentation/xcuiautomation/xcuielement/exists

Current verification checkpoint:

- Python 3.14.7: all 87 harness/export/release/preflight checks passed. Shell
  syntax, actionlint and whitespace checks passed.
- Xcode 27.1 compiled the app and complete UI target, including the native
  property-wait API used by Duo. The disposable iPad's exact 27.0/24A434 runtime
  metadata and bounded boot passed. Three focused cooking cases are running once
  in `.tmp/ci41-ipad-cooking/`; their final result remains pending here.
- Ordinary suite now has 25 mandatory cases; Duo retains six. No existing
  outcomes, angle sequences, cleanup or 180/360-second case / 1800-second suite
  limits were removed. The native property wait uses the remaining time from
  the existing ten-second control-readiness deadline, not a second full budget.
- Stable local 27.1/24A94425 is absent and only the RC is installed. No fallback,
  runtime deletion, local SDK mutation or unsafe installation was attempted.
  Actual stable-runtime Duo behavior must pass in fresh full CI; compilation
  alone does not establish that its Settings transition now passes.

## Validate shared harness changes against full local suites

- [x] Audit the whole native suite for remaining lazy firstMatch queries and client-side accessibility value expectations. Replace them with scoped indexed queries and native existence/value waits, retaining all exact-value and feature assertions. Await the recovered draft row within its named list after a cold restart.
- [x] Use XCTest's documented launch boundary for independent cases instead of a second global Home/terminate sequence in teardown. Keep real Home/termination/relaunch and every persistence assertion inside the cold-restoration scenarios. Every UI scenario must still launch its own reset fixture.
- [x] Remove the duplicate Duo hittability preflight that errors inside XCTest. Keep finite/visible frame checks, exactly one standard element.tap() and all post-action outcomes; native tap itself computes a hittable point after its normal synchronization. No coordinate taps, forced clicks, retries or hidden-control bypass.
- [x] Add a deterministic full-suite verification runner: frozen detached checkout, sequential complete iPhone/iPad profiles, retained results/status, and optional fast-forward push of only the exact tested commit after both pass. Refuse publishing failed tests, a changed HEAD/branch or dirty source. Test these publish gates before use.
- [x] Align native CI harness Python with local/backend Python 3.14. Current native jobs run the Homebrew default 3.15 before their late screenshot-only setup step. Pin the interpreter before preflight/tests and for archive validation; do not attribute XCTest failures to this drift without evidence.
- [ ] Run integrated harness checks, start full local verification and update the draft PR honestly. Do not push another candidate based only on focused cases. No archive/upload/tag, larger deadlines, skipped feature tests or paid runner changes. Stable Duo CI remains mandatory after local verification succeeds.

At 1a1680b the focused local iPad cooking sequence passed all three cases in
146.341 seconds, zero failures/skips; owned-device cleanup completed. Both CI
ordinary profiles passed 24/25 cases; PR Duo passed 5/6, branch Duo passed all six.
All backend/browser/format/archive jobs passed. Four failures remained:

- PR iPhone: Settings case hangs inside its initial app.launch(), before any
  Settings interaction. Changing Settings assertions cannot address this.
- PR iPad: offline draft survives the restart phase, then its lazy global
  firstMatch row lookup stalls. Await and address that row through recipe-list.
- Branch iPhone: Live Activity still uses the older outer value expectation.
  The awaited AX lookup runs beyond its five-second expectation deadline.
- PR Duo: Generate shopping list has normal bounds in the active shopping-list,
  but the separate hittability computation raises an activation-point error
  before a touch. Standard tap performs the real framework hit test; retain it
  and the generated-shopping-row checks rather than adding another preflight.

The host samples show 3 CPUs/7 GiB RAM, with swap between zero and 820 MiB.
They do not prove memory pressure caused these failures. No speculative runner
upgrade or Xcode-version switch is justified by that sample alone.

Apple contracts:
- https://developer.apple.com/documentation/xcuiautomation/xcuiapplication/launch()
- https://developer.apple.com/documentation/xcuiautomation/xcuielement/tap()

Verification before the full local gate:

- Python 3.14.7: all 98 harness/export/release/preflight checks passed. This
  includes eleven tests for full-profile publication gates: either native
  profile failing, stale HEAD/branch, dirty source, main publication, existing
  output, verify-only mode and rejected pushes. No failed verification may
  publish a candidate or report a successful publication.
- Shell syntax, actionlint and whitespace checks passed. The only remaining
  custom UI expectation reads Duo viewport geometry; accessibility values,
  disappearance and row readiness use native queries/waits throughout.
- Start the frozen full gate with execution/verify_ios_pr.py, output
  `.tmp/ci42-full`, shared cache `.tmp/ci28-build` and explicit --push-branch
  codex/recipe-tools-marketing. Native suite results remain pending until it
  completes; compilation/focused earlier passes are not substitutes.
- The runner publishes only its captured commit after both entire ordinary
  profiles pass and source validation succeeds. No further candidate commit
  should be made while this gate runs; changes deliberately block publication.
  Status: `python3 execution/verify_ios_pr.py --output .tmp/ci42-full --status`.
- All 25 ordinary and six Duo cases remain required, with unchanged case/suite
  deadlines. Actual stable-runtime Duo CI is still a merge gate after the
  candidate is published. No new local runtime is installed or substituted.
