# Onionary kitchen and sharing checklist

Commit this checklist before implementation. Each numbered feature gets its own commit with appropriate tests. Finish with a combined regression pass and fixes. Open a new PR; do not poll GitHub while idle.

- [x] 1. Add an iOS share extension for Chefkoch URL import, with draft review before saving.
- [ ] 2. Add the web kitchen's meal planning, cooked state, and shopping list to iOS.
- [ ] 3. Render the selected web language immediately, using centralized translation files with no English-to-German flash.
- [ ] 4. Configure backend Impressum through environment variables and refuse startup when required values are missing; document deployment changes.
- [ ] 5. Edit recipes in iOS, including ingredients and steps, with validation and safe cooking-state behavior.
- [ ] 6. Tighten native lists and spacing while preserving readable content, Dynamic Type, and usable tap targets.
- [ ] 7. Replace oversized iOS settings presentation with native settings: one backend, appearance (system/light/dark), and language (system/English/German).
- [ ] 8. Share expiring recipe-copy links between Onionary instances; import independent snapshots, with no synchronization, authenticated creation/import, and safe external fetching.
- [ ] 9. Run backend, browser, Swift, simulator, and packaged PostgreSQL regressions; inspect layouts and fix failures.
- [ ] 10. Push the branch and open a new PR with migration/deployment notes and local test evidence. Leave GitHub CI follow-up to the user.

## Implementation assumptions

- Shared recipes are immutable snapshots; anyone holding a valid temporary link can read that snapshot until expiry or revocation. Creating/importing a copy requires login.
- Backend legal identity is instance-specific. Static app-site legal/support information remains separate.
- Keep existing cooking adventures safe when recipe definitions change; offer a deliberate restart to use edited instructions.
