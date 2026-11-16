# Xcode 27.2 and iPhone Duo

## Move a project from Xcode 26.x

1. Install Xcode 27.2 (27B52) on an Apple silicon Mac running macOS Tahoe 26.6
   or later. Select it per shell with `DEVELOPER_DIR`. Use the same version
   for simulator test compilation, XCTest, screenshot export and device archives.
   [Apple Xcode requirements](https://developer.apple.com/xcode/system-requirements/)
2. Keep each app and extension's existing minimum iOS version. Onionary's
   stays at 17.0. Check the archived app's `MinimumOSVersion` and run a smoke
   test on the oldest supported OS. Use API availability checks where the app
   calls newer APIs. [Xcode 27.2 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-27_2-release-notes)
3. Rebuild with the new SDK and verify the cover and inner displays in Xcode
   Device Hub. Test closed, partially open and fully open, then fold during an
   active task. Check navigation, sheets, keyboard focus, state restoration,
   and landscape. Use adaptive layouts and allow UIKit or SwiftUI to respond
   to the actual window size. [Apple's Duo guide](https://developer.apple.com/iphone-duo/prepare/)
4. Run XCTest on iPhone, iPad and Duo on the standard `xcode-27` runner.
   Reuse compiled simulator products across jobs. Capture both Duo display
   sizes from native screenshot attachments and validate the final bundle.
   [Runner inventory](https://github.com/actions/runner-images/blob/main/images/macos/xcode-27-arm64-Readme.md)

## Choose the simulator build by device

| Device | iOS | Simulator build |
| --- | --- | --- |
| iPhone 17 Pro and iPad Pro | 27.2 | `24B8117` |
| iPhone Duo | 27.2 | `24B91016s` |

Both stable builds use `com.apple.CoreSimulator.SimRuntime.iOS-27-2`.
Inspect `supportedDeviceTypes` in `xcrun simctl list runtimes --json` and match
the exact `buildversion`. `simctl create` accepts the full runtime bundle path.
Onionary checks that path, confirms its `SystemVersion.plist`, and prepares the
device's matching SDK runtime on GitHub-hosted workers.
[Apple's simulator download catalog](https://devimages-cdn.apple.com/downloads/xcode/simulators/index2.dvtdownloadableindex)

## Run Onionary locally

From the repository root, select the new Xcode and install the Duo runtime
with the same preflight CI uses. Each 27.2 runtime download is about 8.3 GB.

```bash
export DEVELOPER_DIR=/Applications/Xcode_27.2.app/Contents/Developer
duo=com.apple.CoreSimulator.SimDeviceType.iPhone-Duo
python3 execution/check_ios_build_environment.py --xcode-only
python3 ios/Onionary/Scripts/ensure_ios_runtimes.py --device-type "$duo"
```

If preflight reports a different SDK mapping, run the command it prints to
select the Duo build, then rerun preflight. Choose the regular build before
switching back to iPhone or iPad tests. Each hosted job runs one profile and
configures its own mapping.

```bash
sdk_build=$(xcrun --sdk iphonesimulator --show-sdk-build-version)
xcrun simctl runtime match set iphoneos27.2 24B91016s --sdkBuild "$sdk_build"
python3 ios/Onionary/Scripts/ensure_ios_runtimes.py --device-type "$duo"
SIMULATOR_DEVICE_TYPE="$duo" bash ios/Onionary/Scripts/test.sh
```

To prepare iPhone or iPad tests again, use `24B8117` in the mapping command
and pass the model's full identifier to the preflight and test script. Local
TestFlight archives only need the selected Xcode, signing credentials, and
the repository's normal version and build number inputs.
