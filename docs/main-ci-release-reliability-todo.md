# Main CI and release follow-up

- [x] Trace all three failed iOS jobs from [main CI](https://github.com/Malaber/what-should-we-eat/actions/runs/43811873620) to their original XCTest logs.
- [x] Let XCTest boot the pinned simulator for each session. Keep the standard runners, selectors, case deadlines and failure diagnostics.
- [x] Separate offline save/cold restoration from the saved-draft changes sheet. Keep both flows in the native phone and tablet suites.
- [x] Isolate each Duo case on its own standard runner. Export both display sizes from the passing screenshot and fold results of that run.
- [x] Pin the hosted build, test, export and archive toolchain to Xcode 27.2 across both GitHub runner images.
- [x] Use the SDK-matched iOS 27.2 runtime build 24B8117 for hosted iPhone and iPad. Keep their device models and the existing stable Duo runtime.
- [x] Shorten the cooking-menu feedback test setup, retaining the real checklist tap, menu action, editor cancellation and checked progress.
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
