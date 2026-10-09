# Onionary revision checklist

Each numbered revision gets its own commit. Final regression fixes and release follow.

- [x] 1. Display quantities/portions with at most two decimal places; retain calculation precision.
- [x] 2. Improve enabled-control contrast in light and dark appearance.
- [x] 3. Add subtle haptics to portion +/- and ingredient/step checks.
- [x] 4. Add persistent redo alongside undo, timestamped history, and animated transient action feedback.
- [x] 5. Align native connection, web welcome, and passkey pages with system light/dark appearance.
- [x] 6. Show current ingredients at the top of the portion adjustment sheet.
- [x] 7. Add review enrollment links and full passkey management, using shared library capabilities and extending the library if needed.
- [x] 8. Rebrand the complete webapp and user-facing product copy to Onionary.
- [x] 9. Use SQLAdmin for review/recovery link administration and document this pattern in FastPasskey.
- [x] 10. Run backend/Postgres/browser/native tests, inspect screenshots, and fix regressions.
- [ ] 11. Release a Git-tag-derived version to TestFlight and verify upload acceptance.

Validation: 100 backend tests passed in the Python 3.14 image; PostgreSQL fresh/repeated migrations and non-root API startup passed. Chromium desktop and iPhone emulation: 12 tests each. Swift core: 8 tests; simulator UI: 2 tests. Light/dark web and native screenshots inspected.
