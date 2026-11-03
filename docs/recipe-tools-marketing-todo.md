# Recipe tools and editable App Store artwork

Commit this checklist before implementation. Each feature gets a separate commit
with relevant tests; execute integrated checks after all features, then commit
fixes separately. Long simulator tests run detached; no retries or idle CI polling.

- [ ] Recipe editor: preselected existing tags and suggestions from instance tags.
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
