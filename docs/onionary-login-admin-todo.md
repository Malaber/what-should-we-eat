# Login, identity, administration and CI

- [x] Fix CI's recipe-import sheet failure; bound test execution without retries.
- [x] Make login gate perform passkey login/registration directly; keep one shared ceremony implementation for native/admin/enrollment routes.
- [x] Show account name/email in iOS backend settings and masked identity during recovery; avoid duplicate expired-session alerts.
- [x] Restore local admin assets and make account details, boolean values and link forms usable with CSS/JS disabled; record HTML-first rule.
- [x] Add repository skill for todo-first, separate commits, final validation and immutable releases.
- [x] Complete regression tests, update PR and upload fresh tagged TestFlight build.

Validation: Python 3.14 backend suite: 143 passed. Swift core: 21 passed;
iOS simulator: all 12 UI tests passed, including the previously failing import
flow, masked recovery identity and Settings account details. HTML formatting
passed. Signed app and both extensions archived as 0.3.0 (11). Desktop and mobile browser suites each passed all 20 tests. Fresh `v0.3.0-rc.11` published and PR #6 updated. TestFlight upload
**0.3.0 (11)** accepted 2026-10-11 at 14:57 Europe/Berlin; Apple processing
started. GitHub CI results remain external validation; no idle polling.
This completion record changes documentation only, not the tagged app code.
