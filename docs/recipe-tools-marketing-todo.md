# Recipe tools and editable App Store artwork

Commit this checklist before implementation. Each feature gets a separate commit
with relevant tests; execute integrated checks after all features, then commit
fixes separately. Long simulator tests run detached; no retries or idle CI polling.

- [ ] Recipe editor: preselected existing tags and suggestions from instance tags.
- [ ] Apple Intelligence modes: creative recipe generation versus faithful formatting; formatting preserves content and leaves missing quantities unspecified.
- [ ] Apple Intelligence: detect input language by default; explicit recipe-language picker.
- [ ] Recipe food icons: broad curated selection, persisted and displayed instead of leaf.
- [ ] Remove the uninformative “Ready when you are” text.
- [ ] Ingredient matching: enter available ingredients and amounts; rank existing recipes with clear matching/missing information, without inventing unit conversions.
- [ ] Recently visited: show three initially, with show-more control.
- [ ] Recipe browsing: select multiple tags together.
- [ ] Settings: selectable app accent colors, respecting light/dark contrast.
- [ ] Ingredient drag reordering with persistent order through edit/save/reload/share.
- [ ] Named ingredient and instruction subgroups, preserved through backend, iOS editing/cooking and recipe-copy exchange; keep old recipes compatible.
- [ ] Editable header.svg and search-results.svg; deterministic Inkscape/Pillow RGB exports at 5244×2950; actual branding and demo UI, embedded fonts or outlined text, safe compositions.
- [ ] Generate creative assets from current screenshot bundle in CI, validate outputs, retain release packaging, document reusable workflow for other apps; inspect Malaber/github-workflows for reuse.
- [ ] Integrated backend/core/browser/format checks, visual asset review, detached iOS tests; fix failures separately and open/update PR with honest evidence.

Scope: native recipe UX plus backend/web compatibility for new stored fields.
Existing release tags remain immutable. No automatic App Store Connect asset
replacement: generated previews require visual approval.

## Follow-up requests (2026-11-04)
- [ ] Consume the merged central creative workflow at an immutable SHA; keep app-specific artwork configurable.
- [ ] Remove the hard square edge around the header icon using an editable SVG mask.
- [ ] Persist account-scoped recipe drafts offline, restore them after app restart, support retry/copy/delete; failed saves must keep the editor open.
- [ ] After saving changes to the currently cooked recipe, offer an explicit reload/reset confirmation; declining preserves cooking progress.

## Implementation / validation checkpoint (2026-11-04)

All feature code is committed on `codex/recipe-tools-marketing`; checkboxes remain
open until integrated validation completes. PR #9 is deliberately a draft.

- Swift core tests passed, including incomplete draft persistence/account separation,
  corruption handling and explicit cooking-progress reset.
- Desktop Chromium: 23 passed. HTML formatting and `git diff --check` passed.
- Updated header and search PNGs rendered and decoded at 5244×2950 RGB. Header
  visually inspected: square outer edge removed; original rounded icon retained.
- Python 3.14 backend and iOS simulator suites are running detached. Recheck
  `.tmp/recipe-tools-backend-followup.log` and `.tmp/recipe-tools-ios-followup.log`.
- Native recovery UI test now covers reopening after app termination. Latest
  accessibility-identifier follow-up is included in pushed CI.
- No TestFlight build or App Store Connect asset upload performed for this batch.
