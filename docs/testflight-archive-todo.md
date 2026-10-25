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
