# App Store marketing assets

- [x] Verify Apple's header/search specifications and generate reusable Onionary artwork.
- [x] Compose header, search-result and framed-phone marketing images from current simulator captures.
- [x] Include generated images in existing CI screenshot artifacts and release ZIPs; validate dimensions and completeness.
- [x] Test renderer/packaging, inspect real previews, document source prompts and upload slots, then push changes.

Validation so far:
- Python 3.14 suite: 144 passed; renderer/package regression tests: 4 passed after final layout adjustment.
- Inspected header/search compositions and iPad portrait; corrected overlapping tablet copy.
- Local fresh simulator capture built both apps but stalled before screenshot test execution; interrupted both task-owned runs, retained xcresults, and did not retry. Current preview ZIPs use existing real simulator captures. Fresh CI capture remains unverified.
- Artwork provenance, exact upload slots and font licenses are in marketing/README.md.
- Published PR #7 from current main. CI results are pending; no idle polling.
