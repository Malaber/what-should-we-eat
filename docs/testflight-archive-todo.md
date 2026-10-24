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
