# Onionary 0.9.0

- [x] Diagnose the released Apple Intelligence import error. Import complete Recipe structured data without a model, and give an actionable error if the formatting or creation model is unavailable.
- [x] Document and test URL classification for Chefkoch, Onionary shares on self-hosted origins, and other recipe websites. Preserve existing share and Chefkoch compatibility.
- [x] Add recipe equipment to editing, preview, cooking, and shared recipes. Remember checked equipment by account across recipes and app restarts.
- [x] Add clickable time placeholders and startable cooking countdowns. Keep times independent of portions and cover existing step durations.
- [x] Let a signed-in web user save a recipe URL for later and see it on iOS. Support review, copying the link, and removing it when done.
- [x] Include a genuine Lock Screen Live Activity capture in the iPhone marketing bundle.
- [x] Use Apple device artwork in the marketing previews. Keep the editable creative sources, safe-area validation, and existing release bundles.
- [x] Keep new recipe fields visible above the keyboard, including at the end of the editor.
- [x] Fix title, item count, and Copy readability in the web shopping-list header. Verify light, dark, and narrow layouts.
- [x] Inspect actual iPhone, iPad, and Duo job logs on the standard GitHub runner and run every advisory case locally.
- [x] Run integrated local tests and verify a signed device archive.
- [ ] Open the 0.9.0 PR and verify its CI. Upload a fresh, immutable TestFlight build after validation.

## Local verification

- Python 3.14 passed 350 tests. Chromium passed 25 browser tests on desktop and 25 using the iPhone viewport. `npm run check:html` passed. The shopping-list regression checks 4.5:1 text contrast and fits a 360-pixel viewport.
- Upgrading a database from `20261103_03` to `20261118_02` preserved an existing recipe and initialized the equipment and inbox data correctly.
- Xcode 27.2 (27B52) passed 57 Swift tests and compiled the UI test bundle. Full local simulator coverage passed with 38 iPhone, 38 iPad, and 5 Duo tests and zero skips. iPhone and iPad ran serially on iOS 27.0, and Duo ran on its iOS 27.1 runtime. The earlier concurrent iOS 27.2 attempts stopped while XCTest prepared the runner.
- Verified a signed device archive of 0.9.0 (34), including the widget and share extensions. Local UI tests exercise the actual Lock Screen activity. Foundation Models generation on a supported physical device still needs verification.
- The standard runner in [the latest 0.8.0 main run](https://github.com/Malaber/what-should-we-eat/actions/runs/44100599294) used host macOS 27.0.1 with Xcode 27.2. The advisory rechecks remain scheduled for November 24 and December 1 in [the test directive](../directives/run_tests.md#temporary-hosted-simulator-exception).
