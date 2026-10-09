# Onionary kitchen and sharing checklist

Commit this checklist before implementation. Each numbered feature gets its own commit with appropriate tests. Finish with a combined regression pass and fixes. Open a new PR; do not poll GitHub while idle.

- [x] 1. Add an iOS share extension for Chefkoch URL import, with draft review before saving.
- [x] 2. Add the web kitchen's meal planning, cooked state, and shopping list to iOS.
- [x] 3. Render the selected web language immediately, using centralized translation files with no English-to-German flash.
- [x] 4. Configure backend Impressum through environment variables and refuse startup when required values are missing; document deployment changes.
- [x] 5. Edit recipes in iOS, including ingredients and steps, with validation and safe cooking-state behavior.
- [x] 6. Tighten native lists and spacing while preserving readable content, Dynamic Type, and usable tap targets.
- [x] 7. Replace oversized iOS settings presentation with native settings: one backend, appearance (system/light/dark), and language (system/English/German).
- [x] 8. Share expiring recipe-copy links between Onionary instances; import independent snapshots, with no synchronization, authenticated creation/import, and safe external fetching.
- [x] 9. Run backend, browser, Swift, simulator, and packaged PostgreSQL regressions; inspect layouts and fix failures.
- [x] 10. Push the branch and open a new PR with migration/deployment notes and local test evidence. Leave GitHub CI follow-up to the user.

## Implementation assumptions

- Shared recipes are immutable snapshots; anyone holding a valid temporary link can read that snapshot until expiry or revocation. Creating/importing a copy requires login.
- Backend legal identity is instance-specific. Static app-site legal/support information remains separate.
- Keep existing cooking adventures safe when recipe definitions change; offer a deliberate restart to use edited instructions.

## Local validation

- Final Python 3.14 Docker image: 121 backend tests passed (one upstream httpx deprecation warning).
- PostgreSQL fresh and repeated migrations, non-root app startup, and protected API smoke checks passed.
- Chromium desktop and iPhone emulation: 14 tests each, including German navigation and recipe link revocation.
- Swift core: 13 tests; iOS simulator: 4 UI tests covering cooking persistence, editing/import, sharing/revocation, live language/appearance settings, and marketing screenshots.
- App plus share-extension simulator build passed. Compact cooking screenshots inspected.
- Device signing and real-device share-extension delivery are not validated by simulator tests. The follow-up TestFlight release uses tag `v0.2.0-rc.3`, version `0.2.0` and build `3`; signing and upload results are recorded after verification.
- GitHub CI has not been polled. User will return with results.

Deployment prerequisites and behavior: [kitchen-sharing-deployment.md](kitchen-sharing-deployment.md).

PR: https://github.com/Malaber/what-should-we-eat/pull/2
