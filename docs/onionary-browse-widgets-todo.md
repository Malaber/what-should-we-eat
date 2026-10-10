# Recipe discovery and cooking surfaces

Commit this checklist before implementation. Keep features in individual commits,
then run and fix the relevant complete test suites without retries.

- [x] Add searchable tags, category navigation and richer recipe browsing.
- [x] Add explicit ingredient quantity placeholders to recipe steps, resolving
  percentages against the recipe quantities and current portion scale.
- [x] Add a Live Activity for the current cooking session with progress and next step.
- [x] Add a Home Screen kitchen widget for recipes planned this week, with deep links.
- [x] Configure Onionary widget App ID and shared App Group without deleting Apple records.
- [x] Configure Planini phone widget App ID / group as required by PR 110.
- [x] Test parsing, scaling, category filtering, snapshots, lifecycle, UI and signed packaging.
- [x] Update PR with evidence and upload the next git-versioned TestFlight build.

Use existing Onionary App Group `group.de.malaber.onionary` for app, share and
widget targets. Store widget snapshots only, never authentication tokens.
Planini PR 110 specifies widget `de.malaber.planini.widget` and existing group
`group.de.malaber.planini.watch`; verify these against Apple before changes.
Do not delete any App Store Connect or Apple Developer records.

## Validation

- 20 Swift core tests passed: search/category intersection, old-cache decoding,
  percentage placeholders, snapshot state/undo/scale, week expiry and scoped links.
- Seven iOS UI tests passed, including category search and real ActivityKit start/stop.
- Desktop Chromium: 16 passed. Mobile Chromium initially exposed a profile hydration
  race during appearance changes; fixed by applying theme in place and disabling
  profile controls until load. Final mobile suite: 16 passed; desktop account check: 1 passed.
- Apple accepted TestFlight 0.2.0 (5), tag v0.2.0-rc.5, on 2026-10-10 at
  08:17 Europe/Berlin. App and both extensions use the Onionary shared group.
