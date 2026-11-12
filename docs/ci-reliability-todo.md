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
