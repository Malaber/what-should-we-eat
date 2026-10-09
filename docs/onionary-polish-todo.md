# Onionary polish and import revisions

Commit this checklist first. Implement each item in its own commit with relevant
regression coverage, then run the complete applicable test suites and fix failures.
Use the Apple design skill for interaction, accessibility and layout work.

- [x] Dismiss iOS keyboard by tapping outside fields; retain accessible Done action.
- [x] Give populated numeric recipe fields persistent labels and units.
- [x] Store recipe base portions end-to-end, including Chefkoch import and editing.
- [x] Update portion adjustment live on field exit and +/-; remove redundant whole-recipe scaling section.
- [x] Add free-text Apple Intelligence recipe drafting with Hiinterval-style availability handling and draft review.
- [x] Accept Chefkoch app share-sheet payloads (URL and text links), including tracking query strings.
- [x] Publish stable GitHub releases on main, minor bump by default, with merged PR title/body as release notes (Planini pattern).
- [x] Format HTML with a pinned formatter and enforce it in CI, including GitHub Pages.
- [x] Add appropriate web links to app.onionary.malaber.de.
- [x] Move user passkeys, language and appearance to account settings; match Planini list/actions and prevent deleting the last passkey server-side.
- [x] Fix dark-mode recipe-import panel contrast.
- [x] Keep recipe-card actions visible with responsive wrapping or scrolling.
- [x] Center and space recipe-share dialogs; provide responsive sizing, focus handling and reduced-motion support.
- [x] Preserve umlauts in configured Impressum values, including the Ansible-to-Compose path.
- [x] Run backend, web, iOS and affected deployment/release tests; fix regressions, inspect UI, push new PR. Leave GitHub CI follow-up to the user.

## Validation and release

- PR: https://github.com/Malaber/what-should-we-eat/pull/4
- Python 3.14 packaged backend: 131 tests passed; final added Chefkoch yield test and release tests: 9 passed.
- Fresh/repeated PostgreSQL migrations and non-root API/passkey smoke checks passed.
- Desktop Chromium: 15 passed; iPhone emulation: 15 passed; final mobile recipe/layout checks: 3 passed.
- Swift core: 15 passed; clean isolated simulator UI build: 5 passed.
- HTML formatter and diff checks passed; dark import and share-dialog screenshots inspected.
- Eight deployment role tests passed, including UTF-8 Compose round-trip. Related selfhosted !30 and infra !38 merged/deployed by operator.
- Physical-device checks remain: Chefkoch app discovery and actual Apple Intelligence generation (simulator cannot establish these).
- TestFlight v0.2.0-rc.4 / 0.2.0 (4) uploaded and accepted by Apple on 2026-10-09 at 22:01 Europe/Berlin; processing started. Signed app/extension versions and text-share activation verified.
