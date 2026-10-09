# Onionary revision checklist

Each numbered revision gets its own commit. Final regression fixes and release follow.

- [x] 1. Display quantities/portions with at most two decimal places; retain calculation precision.
- [x] 2. Improve enabled-control contrast in light and dark appearance.
- [x] 3. Add subtle haptics to portion +/- and ingredient/step checks.
- [x] 4. Add persistent redo alongside undo, timestamped history, and animated transient action feedback.
- [ ] 5. Align native connection, web welcome, and passkey pages with system light/dark appearance.
- [ ] 6. Show current ingredients at the top of the portion adjustment sheet.
- [ ] 7. Add review enrollment links and full passkey management, using shared library capabilities and extending the library if needed.
- [ ] 8. Run backend/Postgres/browser/native tests, inspect screenshots, and fix regressions.
- [ ] 9. Release a Git-tag-derived version to TestFlight and verify upload acceptance.
