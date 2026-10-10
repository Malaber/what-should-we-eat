# Cooking controls follow-up

Commit checklist first, implement features separately, then run and fix tests.

- [x] Show ingredient insertion only above the keyboard when editing a step; move
  percentage help to an information button beside the Steps heading.
- [x] Show all recipe tags in recipe details and make tag browsing easy to find.
- [ ] Automatically start the Live Activity on cooking interactions; add a visible
  top-left cooking-mode symbol toggle and respect an explicit stop.
- [ ] Verify editor focus/insertion, tag browsing and automatic activity lifecycle
  with repeatable tests, then update the PR and upload the next TestFlight build.

Previous build: Apple accepted 0.2.0 (5), v0.2.0-rc.5 at 08:17 Europe/Berlin on
2026-10-10. No App Store Connect records were deleted.
