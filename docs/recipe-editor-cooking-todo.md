# Recipe editing, imports and cooking

- [x] Fit the web editor at desktop and mobile widths and add a recipe emoji picker.
- [x] Add selected-tag chips with typeahead suggestions in the web editor.
- [x] Add web step ordering and move group management for ingredients and steps into the reorder views on both platforms.
- [x] Add Cook now with browser-local ingredient and step checks to public recipe copies.
- [x] Keep the normal navbar on account settings, lay out footer items inline, and preserve recipe cards across search input.
- [x] Show No tags in the iOS preview. Match the ingredient and step editor cards.
- [x] Save iOS drafts only when changed and show a summary of changes beside each draft.
- [x] Use Apple Intelligence formatting for other recipe URLs on iOS and preserve ingredient and step groups.
- [x] Preserve Chefkoch group headings and generate ingredient amount placeholders from unambiguous imported quantities.
- [x] Render scalable ingredient badges in cooking steps and synchronize checks with the ingredient list.

- [x] Recover the v0.7.0 iPhone Duo captures and include verified Duo screenshots in future GitHub releases.
- [x] Promote the reachable release-candidate version on a normal main release and preserve explicit version bumps.

## Verification

- Python 3.14 test suite, Chromium desktop and iPhone-size browser suite, Swift package tests and HTML formatting.
- Both supplied Chefkoch pages parsed locally. Fixture tests cover grouped ingredient tables and a step heading folded into the previous paragraph.
- The PR's checks cover the iPhone, iPad and iPhone Duo suites, archive and screenshot jobs.
- Apple Intelligence model output requires a supported device with the model ready. The automated tests cover URL handling and page extraction.
- Duo exports were validated against the original v0.7.0 CI result. Release tests cover promotion, unrelated RC tags, explicit bumps and immutable tags.
