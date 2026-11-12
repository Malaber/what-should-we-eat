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

- [ ] Split the combined tag/pantry/AI test into independent feature cases, retaining its assertions. CI completed its actions at 178.9 seconds then exceeded the 180-second allowance during teardown; keep the allowance unchanged.
- [ ] Centralize recipe selection through the named list and indexed identifier query, replacing global firstMatch lookups that can stall during navigation.
- [ ] Inspect Duo navigation snapshot frames and prevent probing hidden/invalid activation points while retaining real hittability checks and all navigation assertions.
- [ ] Verify these exact cases locally, lint workflows and push CI-only fixes. Full GitHub gates remain required; no tags/uploads.
