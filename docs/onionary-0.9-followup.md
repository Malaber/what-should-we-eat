# Onionary 0.9 follow-up

- [x] Store owned equipment on the signed-in account. Verify the web and iOS sync paths, account isolation, and migration of existing local checks.
- [x] Edit kitchen equipment in individual recipe rows with add and remove actions.
- [x] Put ingredient and timer placeholders in the keyboard's plus menu. Insert at the current cursor or selection, explain both with examples in the menu, and show when the recipe has no ingredients.
- [x] Keep preparing ingredients separate from using them in steps. Preserve existing preparation progress, undo, and redo. Add an inline hint for partial ingredient references in the editor.
- [x] Diagnose the previous standard-runner failures using logs and retained XCTest results. Keep the native coverage in place.
- [x] Record the physical TestFlight Apple Intelligence result and investigate the production build difference. Exercise available import and error paths.
- [x] Run integrated backend, browser, Swift, and native simulator tests before pushing. [PR #12 and its CI results](https://github.com/Malaber/what-should-we-eat/pull/12/checks)

## Hosted simulator reliability follow-up

- [x] Diagnose the November 22 launch and XCTest startup failures using result bundles and runner logs.
- [x] Stage the app and test runner before hosted XCTest startup. Keep all iPhone, iPad, and Duo cases and screenshot capture.
- [x] Exercise the changed path locally. The 39 iPhone and 39 iPad cases passed on iOS 27.2 with the hosted startup sequence. All five Duo cases passed on the locally installed iOS 27.1 runtime. Apple’s downloader did not install the pinned Duo 27.2 runtime on this Mac. All 355 Python tests and the 60 Swift tests passed.

[Hosted verification](https://github.com/Malaber/what-should-we-eat/pull/12/checks) uses the pinned iOS 27.2 runtimes for all three device profiles.

## Behavior and compatibility

- Update the backend to migration `20261119_01` to sync equipment checks. Each signed-in account has its own equipment inventory, including within a shared kitchen. Web and iOS keep offline changes queued until the server confirms them. Existing locally checked tools migrate on the first successful sync. An explicit uncheck on the server survives later imports from other devices.
- The keyboard’s plus menu in each instruction includes a timer, ingredient amounts, and a worked example. The selected item is inserted at the text cursor or replaces the current text selection. A recipe with no ingredients shows an explanatory message in the menu.
- Preparation checks keep their existing saved state. Each ingredient reference can be marked used independently. In the iOS cooking view, usage has its own undo and history entries. Preparation and step completion drive the progress indicator. The editor shows an inline hint when a recipe already uses at least one ingredient reference and some quantified ingredients have no reference.
- The App Store listing currently shows 0.8.0. The iOS source in its release tag matches `v0.8.0-rc.33`. Daniel confirmed Apple Intelligence works on his iPhone in TestFlight build `0.9.0 (34)`. The earlier screenshot matches the message 0.8.0 uses for `.modelNotReady`. The App Store binary and device model state at the time of that failure are unverified. Automated tests cover structured imports, language and format modes, and the app's empty-input validation. [App Store listing](https://apps.apple.com/de/app/onionary/id6820481524) · [Apple model availability](https://developer.apple.com/documentation/foundationmodels/systemlanguagemodel/availability-swift.enum/unavailablereason/modelnotready)

## Hosted iOS

The [RC 34 run](https://github.com/Malaber/what-should-we-eat/actions/runs/44434900460) shows that the standard `xcode-27` runner can run Xcode 27.2 and both iOS 27.2 simulator builds on macOS 27.0.1. Apple supports Xcode 27.2 from macOS Tahoe 26.6. Four advisory phone and Duo cases failed during app launch, before the first feature interaction. The launch timeouts and process lookup errors do not establish the underlying runner fault. The UI tests now resolve the app by its installed bundle identifier. [Apple Xcode requirements](https://developer.apple.com/xcode/system-requirements/)

## Local verification

- Python 3.14 passed 351 tests. Upgrading from `20261118_02` preserved the existing recipe in a disposable database. The same-household equipment smoke passed locally with production-style mobile sessions and SQLite. CI also exercises it with PostgreSQL in the release image.
- Chromium passed 26 desktop and 26 iPhone 13 viewport tests. The recipe editor passed a separate narrow dark-mode run. HTML formatting passed.
- Xcode 27.2 passed 60 Swift core tests. On the pinned iOS 27.2 simulator, the full iPhone suite passed 39 cases. The full iPad run passed 37 of 39 before the editor fixes. The final three-case run on both devices verified equipment editing, timer and ingredient insertion in distinct instructions, and placeholder help for an empty recipe.
- All five Duo cases passed on the locally installed iOS 27.1 Duo runtime. CI uses its pinned iOS 27.2 Duo build `24B91016s`.
