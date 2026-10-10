# Main CI and stable release repair

- [ ] Diagnose the failed tag-sheet UI interaction from main's simulator artifact.
- [ ] Fix the cause and run the complete iOS suite without retries.
- [ ] Verify stable-release creation, PR notes and immutable tags with realistic tests.
- [ ] Publish a fix PR and fresh version tag; preserve required release gates.

Main run 38037583704: backend, browser, HTML and container publication passed;
iOS testStepToolsAndRecipeTags failed; release-main was correctly skipped.
TestFlight build 7 archived but export failed because Xcode lost App Store Connect
account access. Do not report build 7 as uploaded.

## Follow-up release corrections

- [ ] Verify Pages deployment and public app domain; correct deployment failures.
- [ ] Capture iPhone screenshots for the requested 6.1/6.3-inch slot and reject
  incorrect dimensions before publishing; retain correct iPad dimensions.
- [ ] Populate marketing recipe browsing/history and show cooking progress on both devices.
- [ ] Style the web servings input and replace navbar account text with an accessible cog.
- [ ] Make administrator setup and SQLAdmin App Review passkey links easy to find.
- [ ] Run relevant tests, publish fresh tag/build and upload to TestFlight.
