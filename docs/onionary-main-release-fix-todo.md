# Main CI and stable release repair

- [x] Diagnose the failed tag-sheet UI interaction from main's simulator artifact.
- [x] Fix the cause and run the complete iOS suite without retries.
- [x] Verify stable-release creation, PR notes and immutable tags with realistic tests.
- [ ] Publish a fix PR and fresh version tag; preserve required release gates.

Main run 38037583704: backend, browser, HTML and container publication passed;
iOS testStepToolsAndRecipeTags failed; release-main was correctly skipped.
TestFlight build 7 archived but export failed because Xcode lost App Store Connect
account access. Do not report build 7 as uploaded.

## Follow-up release corrections

- [x] Verify Pages deployment and public app domain; correct deployment failures.
- [x] Capture iPhone screenshots for the requested 6.1/6.3-inch slot and reject
  incorrect dimensions before publishing; retain correct iPad dimensions.
- [x] Populate marketing recipe browsing/history and show cooking progress on both devices.
- [x] Style the web servings input and replace navbar account text with an accessible cog.
- [x] Make administrator setup and SQLAdmin App Review passkey links easy to find.
- [ ] Run relevant tests, publish fresh tag/build and upload to TestFlight.

## Evidence

- Main failure artifact showed a visible tag button without its sheet. Cooking now
  uses one identifiable sheet destination; all 20 core and 8 simulator UI tests passed.
- Passkey/admin, immutable tags, release metadata and screenshot packaging: 25 passed.
- Desktop browser suite: 16 passed. Mobile: 15 passed plus one incorrect test radius
  assumption, corrected to compare with existing form styles. All three recipe/form
  tests then passed on both mobile and desktop. HTML formatting passed.
- Real screenshot captures passed on iPhone Pro (1206×2622) and iPad 13-inch
  (2064×2752). Final captures wait for the action banner to finish dismissing.
- Pages deployed successfully. Public DNS is correct and the operator reports the
  site live after fixing GitHub settings; local DNS/TLS still lagged during checks.
