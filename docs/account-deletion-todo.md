# Permanent account deletion

- [x] Add authenticated email-confirmed deletion with transactional cleanup of credentials, sessions, private recipes and household membership; preserve other members' shared data.
- [x] Add accessible web Danger zone with explicit consequences, email confirmation, success and error states.
- [x] Add native iOS Danger zone with matching confirmation, error handling and local-account cleanup after success.
- [ ] Test authorization, confirmation mismatch, relational cleanup, shared-data preservation and UI flows; document physical-device App Review recording steps.

## Validation
- Backend Python 3.14: 150 passed, including six deletion tests.
- Browser: three desktop cases (light, dark, no CSS/JS), two mobile cases passed.
- HTML formatter and git diff checks passed; light/dark screenshots inspected.
- Swift core: 13 passed. Native app and UI tests compile.
- Native UI deletion success and offline preservation passed. Full suite: 15 passed, one edit/share setup failure; recipe selection fixed, fresh regression run pending.
- Draft PR #8. Backend must deploy before the app. Physical-iPhone recording instructions: docs/account-deletion.md.
- TestFlight 0.5.0 (13) upload accepted. Remaining: full native UI pass/CI results and physical-device recording for App Review. Backend deployment is still required.
