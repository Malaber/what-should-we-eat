# Deployment visibility and review preparation

- [x] Show the deployed backend version in the web frontend.
- [x] Document administrator promotion and SQLAdmin access clearly.
- [x] Add safe, repeatable demo-data population for a dedicated review account.
- [x] Simplify iOS recipe toolbar: contextual sort, combined Add menu, pull refresh.
- [x] Test, open a new PR, publish a fresh version tag and upload TestFlight.

Validation: backend suite 138 passed; three review-data isolation tests passed;
recipe/version browser tests passed on desktop and mobile (four each); HTML
formatting passed. Signed iOS 0.3.0 (9) archive built successfully.

iOS: 20 core and eight UI tests passed. PR #6 opened. Immutable tag
`v0.3.0-rc.9` published. TestFlight upload **0.3.0 (9)** accepted on
2026-10-11 at 01:19 Europe/Berlin; Apple processing started. This checklist
completion records the tagged build and does not change its app code.
