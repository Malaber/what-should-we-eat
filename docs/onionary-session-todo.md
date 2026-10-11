# Session continuity and recipe entry

- [x] Native sessions: 14-day access, further 28-day renewal grace; absolute 42-day passkey deadline, revocable and rotating refresh tokens.
- [x] Silent renewal, same-account passkey overlay, session dates/manual renewal in Settings; retain cooking progress, drafts and cached meal plan.
- [x] Manual recipe entry first in Add menu, using existing editor.
- [x] Visible localized save/network errors and progress; preserve failed drafts.
- [x] Replace widget age counter with refresh link that opens Kitchen and syncs, including session recovery.
- [ ] Test expiry/rotation/isolation, recovery and editor behavior; update PR and publish fresh tag/TestFlight build.

Backend validation: 142 tests passed. UI coverage includes silent renewal,
expired-session cooking, same-account recovery, wrong-account rejection and
manual recipe drafts surviving save failure. Final suite/release pending.
