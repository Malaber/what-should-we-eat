# App Store marketing

- [x] Keep header and search artwork inside Apple’s universal safe area and generate crop previews.
- [x] Build three marketing portraits from native XCTest captures and bundle them with the original screenshots in CI.
- [x] Add Apple’s Smart App Banner and link to the live listing from the landing page.
- [x] Verify real iPhone and iPad captures, release packaging, website markup, and workflow syntax locally.
- [ ] Record the full PR checks.

## Reliability and artwork follow-up

- [x] Verify accessible recipe move controls and saved row order on iPhone and iPad. Keep the native drag handles.
- [x] Exercise the Duo shopping pane at 90° before closing to the cover display. All six Duo cases passed locally on iOS 27.1 build 24A94425.
- [x] Run each Duo case once in a fresh simulator on the pinned runtime. Verify all six native cases and 30 shell harness tests.
- [x] Add richer onion-inspired abstract shapes to creative assets and framed captures. Verify the full artwork and Apple's safe-area crops.
- [ ] Run focused simulator tests and the full GitHub iOS, browser, backend, and artwork checks.

Local checks passed 314 Python tests, 23 desktop and 23 mobile Chromium cases, 16 capture and
packaging cases, HTML formatting, and ingredient reorder/save/reopen on both
iOS 27.0 simulator profiles. Both artwork bundles were built from native captures
and checked at full size and within Apple's safe-area crop.
