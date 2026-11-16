# Main CI and release follow-up

- [x] Trace all three failed iOS jobs from [main CI](https://github.com/Malaber/what-should-we-eat/actions/runs/43811873620) to their original XCTest logs.
- [x] Let XCTest boot the pinned simulator for each session. Keep the standard runners, selectors, case deadlines and failure diagnostics.
- [x] Separate offline save/cold restoration from the saved-draft changes sheet. Keep both flows in the native phone and tablet suites.
- [x] Verify GHCR publishing and exercise stable screenshot packaging on PRs. Publish the stable GitHub release with all four ZIPs after its matching image is pushed.
- [x] Run focused local verification. Swift 50, Python harness 86, release/artifact tests 10. iPad passed both draft cases. iPhone passed cold boot and offline draft restoration.
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
