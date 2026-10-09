# Recipe discovery and cooking surfaces

Commit this checklist before implementation. Keep features in individual commits,
then run and fix the relevant complete test suites without retries.

- [ ] Add searchable tags, category navigation and richer recipe browsing.
- [ ] Add explicit ingredient quantity placeholders to recipe steps, resolving
  percentages against the recipe quantities and current portion scale.
- [ ] Add a Live Activity for the current cooking session with progress and next step.
- [ ] Add a Home Screen kitchen widget for recipes planned this week, with deep links.
- [ ] Configure Onionary widget App ID and shared App Group without deleting Apple records.
- [ ] Configure Planini phone widget App ID / group as required by PR 110.
- [ ] Test parsing, scaling, category filtering, snapshots, lifecycle, UI and signed packaging.
- [ ] Update PR with evidence and upload the next git-versioned TestFlight build.

Use existing Onionary App Group `group.de.malaber.onionary` for app, share and
widget targets. Store widget snapshots only, never authentication tokens.
Planini PR 110 specifies widget `de.malaber.planini.widget` and existing group
`group.de.malaber.planini.watch`; verify these against Apple before changes.
Do not delete any App Store Connect or Apple Developer records.
