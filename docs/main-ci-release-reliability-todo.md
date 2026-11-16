# Main CI and release follow-up

- [x] Trace all three failed iOS jobs from [main CI](https://github.com/Malaber/what-should-we-eat/actions/runs/43811873620) to their original XCTest logs.
- [x] Let XCTest boot the pinned simulator for each session. Keep the standard runners, selectors, case deadlines and failure diagnostics.
- [x] Separate offline save/cold restoration from the saved-draft changes sheet. Keep both flows in the native phone and tablet suites.
- [x] Isolate each Duo case on its own standard runner. Export both display sizes from the passing screenshot and fold results of that run.
- [x] Pin the hosted build, test, export and archive toolchain to Xcode 27.2 across both GitHub runner images.
- [x] Use the SDK-matched iOS 27.2 runtime build 24B8117 for hosted iPhone and iPad. Keep their device models and the existing stable Duo runtime.
- [x] Shorten the cooking-menu feedback test setup, retaining the real checklist tap, menu action, editor cancellation and checked progress.
- [x] Allow up to four minutes for the two native menu cases that hit two 60-second XCTest animation waits. Keep standard and suite deadlines.
- [x] Verify GHCR publishing and exercise stable screenshot packaging on PRs. Publish the stable GitHub release with all four ZIPs after its matching image is pushed.
- [x] Run focused local verification. Swift 50, Python harness 87, release/artifact tests 10. iPhone and iPad passed both draft cases. Duo fold and screenshot cases passed locally on the simulator RC selected by Xcode. The stable Duo runtime is verified by hosted CI.
- [ ] Verify the stable GitHub release and versioned GHCR image after the follow-up merges and main CI passes.

The merged commit and RC 32 have the same Git tree. In the failing main run,
the iPhone guest completed explicit preboot, returned to Booting under XCTest,
and then failed to connect to Instruments. Duo started its suite but the
marketing app launch stalled before its first assertion. The iPad spent the
remainder of its three-minute test budget searching the draft changes sheet.

GHCR returned the same multi-architecture manifest for `main` and
`sha-f1e1b9752947c015151389511355191d26972ee8`. Image digest
`sha256:5108a1193b14f0f3544ecab4f9078084da8ec4e9dae55bcd77f3df78486a21d9`.
The stable GitHub release job was skipped after the iOS failures.

[PR run 43818237211](https://github.com/Malaber/what-should-we-eat/actions/runs/43818237211)
passed the Duo fold and marketing cases on 27.1 build 24A94425. The third
guest on the same runner stalled loading Accessibility before the suite
started. The same passing result bundles produced and validated the combined
Duo artwork locally.

The [isolated Duo shopping job](https://github.com/Malaber/what-should-we-eat/actions/runs/43821715191/job/133147310015)
also failed before the app launched. The Instruments service connection was
interrupted and XCTest timed out waiting for Accessibility. Adjacent jobs
using `xcode-27` received two different macOS images. The iPad job on the
newer image lost a preflight-verified 27.0 runtime during app installation.
The hosted toolchain
pin advances to the same [Xcode build available on both images](https://github.com/actions/runner-images/releases).

[The newer toolchain run](https://github.com/Malaber/what-should-we-eat/actions/runs/43823651650/job/133155500972)
again lost the iPad's iOS 27.0 runtime during app installation. The runner's
post-failure inventory lists the same build remounted under a different path.
Its installed 27.2/24B8117 runtime supports both tested iPhone and iPad models.

[Run 43826496965](https://github.com/Malaber/what-should-we-eat/actions/runs/43826496965)
passed two iPad shards and four Duo cases. Three simulator sessions lost their
runner connection, and another timed out before starting the suite. The
cooking-menu feedback case separately exhausted its budget after two
60-second XCTest animation waits. Give that case an active recipe fixture to
reach its original assertions sooner. The release ZIP packager passed using
the four genuine RC 32 bundles, with all ZIP checksums verified.

[Run 43834232110](https://github.com/Malaber/what-should-we-eat/actions/runs/43834232110)
logged two consecutive 60-second XCTest animation waits in the step ingredient
picker. The token assertion and dismissal still ran. The iPad tag test
separately lost its connection and was terminated after the simulator shut down.

[Run 43838616167](https://github.com/Malaber/what-should-we-eat/actions/runs/43838616167/job/133204272091)
timed out before launching the iPad test suite. Xcode encountered preset watch
devices with unavailable runtimes while looking up destinations. Give each
hosted native job a separate CoreSimulator device set containing its test
destination and use that set for diagnostics and cleanup.

[Run 43842490646](https://github.com/Malaber/what-should-we-eat/actions/runs/43842490646)
confirmed that the private set removes the unrelated destination warnings.
On two iPad workers, CoreSimulator still shut down after opening the
testmanagerd connection and before XCTest could start any case. One Duo
worker stalled preparing Accessibility. The iPhone edit-progress case
reached the save prompt after two minute-long waits for native menu
animations. Use the recipe preview's edit toolbar for this case. The
separate feedback-expiry case continues to exercise the cooking menu.
The same run separately lost the iPhone import app's process during launch
and timed out in iPad automation while dismissing the deletion confirmation
and reactivating the app after backgrounding. Four other Duo cases passed.

## iOS 27.2 and Duo follow-up

- [x] Diagnose the red native checks on PR #11 and verify Apple's exact 27.2 simulator builds.
- [x] Use Xcode 27.2 for build, test and archive. Select the matching 27.2 runtime build by device profile and test both builds sharing an OS version.
- [x] Document the migration from Xcode 26.x, including older device support, local setup, Duo layout checks and screenshot capture.
- [ ] Run local checks, push to PR #11 and verify required checks on the new commit. Record any unresolved hosted runner failure.

[Run 43850578132](https://github.com/Malaber/what-should-we-eat/actions/runs/43850578132)
timed out before the iPad XCTest suite started. Its Duo marketing case could
not launch the app during XCTest. Apple's catalog lists `24B8117` and
`24B91016s` as separate stable iOS 27.2 simulator builds. The former is the
runner's regular iPhone/iPad runtime. The latter adds the Duo profile.

[Run 43855117738](https://github.com/Malaber/what-should-we-eat/actions/runs/43855117738)
registered the exact download on the new runner image and reported it already
downloaded on the older image. The availability check only accepted the
generic iOS runtime identifier. Recognize Duo's device-specific identifier
while still requiring the stable build, supported device type and bundle
system metadata.

[Run 43856952320](https://github.com/Malaber/what-should-we-eat/actions/runs/43856952320)
confirmed that native Duo marketing and reauthentication run on `24B91016s`.
The marketing suite took 576 seconds to start. On the same run an iPad
worker reached the 600-second startup limit, then macOS rejected the kill
signal for the process group. Extend hosted startup to 900 seconds. Keep
case and execution limits and preserve timeout diagnostics if group signaling fails.

[Run 43861371753](https://github.com/Malaber/what-should-we-eat/actions/runs/43861371753)
passed all five native Duo cases, two iPad shards, and the Xcode 27.2 device
archive. The archive declares minimum iOS 17.0 for the app and both extensions.
Two iPhone workers lost the simulator session before starting XCTest. Another
spent 176 seconds on UI setup before pressing Home in the silent renewal case.
Begin that case from the existing active recipe fixture. Keep the real tap,
Home and foreground events, expiry and checked progress assertions.
The revised test passed locally in 51 seconds on the installed iOS 27.0
simulator. All eight Duo screenshots exported from the two 27.2 XCTest
bundles and passed release validation.

[Run 43883677267](https://github.com/Malaber/what-should-we-eat/actions/runs/43883677267)
passed the revised renewal case on iPad. An iPhone screenshot from that run
shows the instruction field after its native tap with the keyboard still
closed. Tap the center of the field and verify keyboard focus before looking
up the ingredient menu. The separate iPad edit-progress case completed its
assertions and timed out during XCTest finalization. Give that case the same
four-minute allowance as the two other measured cases.
The revised renewal case also passed on iPhone in 52 seconds. That shard
failed independently when XCTest could not terminate the previous app process
to start the draft-details case. Both revised input and edit tests passed
locally in 39 and 51 seconds respectively.

[Run 43890269707](https://github.com/Malaber/what-should-we-eat/actions/runs/43890269707)
passed the iPhone ingredient picker and edit-progress checks. In a separate
case XCTest repeatedly queried the editor's retired navigation bar after
Cancel. Assert the cooking toolbar is actionable and the ingredient is still
checked after cancellation.

[Run 43896492355](https://github.com/Malaber/what-should-we-eat/actions/runs/43896492355)
lost an iPhone simulator session before launching the first test. Two other
sessions terminated a test after Instruments stopped responding. The iPhone
cooking-menu case also stalled re-resolving the same native menu row after
feedback expiration. Tap the position of the visible row and verify the editor
opens and cancels. An iPad capture timed out after visiting Settings and
returning to Cooking. Start captures from the light marketing fixture, as Duo
already does, and leave appearance picker coverage in its own test.
The revised iPhone menu and both capture cases passed locally, and the phone
and tablet capture bundles validated. Four Duo cases passed on this run. The
shopping job was canceled before XCTest reported a case. Both passing Duo
capture results exported and validated all eight screenshots.

## Finish PR #11 and ship the verified TestFlight build

- [ ] Trace the iPhone and iPad failures from run 43906504448 to their first failing operations.
- [ ] Repair the native test setup or app behavior that reproduces the failures. Keep all iPhone, iPad and Duo coverage and the standard runners.
- [ ] Verify the affected paths locally and all expected checks on the pushed PR head, including the four screenshot bundles.
- [ ] Publish a new immutable release-candidate tag for that head and confirm the tag's CI run.
- [ ] Build, upload and verify the matching TestFlight build, then confirm the PR still points to the verified green commit.
