# CI stabilization before TestFlight

User requested CI-only work. Do not create release tags, archive/upload locally,
or start a TestFlight worker until separately requested. Preserve all feature
assertions and current deadlines; no retries, sleeps or skipped failures.

- [x] Fix Duo helper startup ordering: both failed jobs time out waiting for READY before XCTest even starts. Initialize the single helper on the first fold request after the app is running, with failure cleanup and no retries.
- [x] Diagnose/fix iPhone Live Activity and silent-renewal failures from the full result log and recording, with focused native regressions.
- [ ] Test orchestration, run affected native cases, update PR with evidence and push CI fixes. Full CI remains pending until GitHub results arrive; do not poll while idle.

Build 27 completed its local device suites/archive but failed Apple account
access during export. That is recorded only as context; upload work is deferred.

Implementation and verification:

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

- [ ] Remove the Duo host process/HTTP sidecar. Inject folds inside the XCTest runner using the existing simulator-only HID event format; preserve all continuity checks and device geometry waits.
- [ ] Use a fresh XCUIApplication object after each intentional termination/relaunch; retain the same on-device files, arguments and progress assertions.
- [ ] Export marketing captures from the normal UI suite's xcresult. Remove the second screenshot simulator/test launch and its inconsistent outer deadline; preserve all four captures, dimension checks, shared renderer, bundles and release attachments.
- [ ] Validate actual native folds/relaunch, artifact export and workflow wiring before push. No TestFlight or new release tag.

Evidence: both previous/current Duo failures are in the host helper startup/RPC,
not fold assertions. iPad renewal now fails at app.launch after termination with
"does not have a process ID". The screenshot case is killed by a 300-second
outer deadline after long XCTest startup, while its own test has not reached its
180-second deadline. The same marketing case already runs in the normal suite.
Local full iPhone suite passed; the local batch stopped on disk reserve before
Duo, so it never established Duo/iPad runtime success.
