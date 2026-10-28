# TestFlight build and archive reliability

- [x] Isolate simulator tests from existing devices and bound test execution; preserve failure diagnostics.
- [x] Share device Release archive command between local upload and CI; validate unsigned archives in CI.
- [ ] Run tests and archive locally, publish a fresh immutable tag/build, upload to TestFlight and record actual outcome.

## Evidence
- Build 12 failed in simulator tests before archive/export: runner launch returned Host is down / system shell probably crashed.
- Unsigned device Release archive passed, matching the new CI command.
- Signed 0.5.0 (13) archive passed; app/share/widget metadata and codesign verified.
- Deadline helper tests: 2 passed. CI YAML and shell syntax validated.
- Isolated simulator now executes UI tests; deletion success and offline-preservation tests passed. Full suite/upload remain pending.

- Split the combined kitchen/edit/import UI case into independent flows, retaining all assertions. Xcode waited 60 seconds twice for menu animation quiescence; the old 120-second limit expired even though subsequent assertions succeeded.
- Build-for-testing has a separate 10-minute bound; test-without-building has a 30-minute suite bound and 3-minute per-test bound. CI has a matching outer deadline. No test retries.

## Build 13 preview release
The user explicitly authorized uploading the signed 0.5.0 (13) archive for UI
testing before the full UI suite is green. Account-deletion success and offline
preservation tests passed. The split edit/share test currently fails because its
setup does not select a recipe before looking for Cooking options; that test fix
remains pending. This preview upload does not mark the regression gate complete.
Archive signing and all three bundle versions were revalidated before upload.

## Follow-up validation
- Build 13 upload accepted by App Store Connect on 2026-10-25; processing/tester availability not verified.
- The completed UI run had 15 passes and one failure: the split edit/share test omitted recipe selection. Fixed by choosing the seeded recipe and asserting that cooking options appear before editing. No retries or removed assertions.
- Full simulator regression run restarted after this test-only fix; result pending. The uploaded app binary is unchanged.

## CI launch follow-up (2026-10-27)
- [ ] Disable debugger attachment in the automated test action; verify generated scheme and run the suite.
- [ ] Push the fix and record new validation without retries or skipped tests.

Evidence: local corrected suite passed all 16 UI tests. GitHub PR run 40164461506
passed, while branch run 40164459002 failed in the first app launch before any
assertion (Xcode launch timeout; DebuggerVersionStore / signal delivery errors).
The remaining 15 tests and both unsigned archive jobs passed.

Generated scheme verified: TestAction has an empty selectedDebuggerIdentifier,
PosixSpawn launcher, and the original UI test target. All assertions remain.
XcodeGen setting reference: https://github.com/yonaskolb/XcodeGen/blob/master/Docs/ProjectSpec.md
New full suite runs in background; completion is not yet verified.

## Portion tap follow-up (2026-10-28)
- [ ] Restrict keyboard dismissal recognition to active text editing; avoid delaying control touches.
- [ ] Verify existing keyboard-dismissal, plus/minus, precision and restoration UI assertions in a fresh background run.

Branch run 40579499757 failed after portion-minus: accessibility still showed
2.58 instead of 1.58. Other 15 UI tests passed; PR run and local suite passed.
The global keyboard recognizer currently receives every tap, even without an
active editor, and leaves UIKit touch-end delays enabled. This is an interaction
hazard to remove; CI confirmation remains required before calling it resolved.
