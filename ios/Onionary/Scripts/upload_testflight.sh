#!/usr/bin/env bash
set -euo pipefail
package_dir=$(cd "$(dirname "$0")/.." && pwd)
marketing_version=${1:-$(python3 "$package_dir/../../execution/version.py" --ios)}
build_number=${2:-}
if [[ ! "$marketing_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ || ! "$build_number" =~ ^[1-9][0-9]*$ ]]; then
  echo "Usage: $0 <marketing-version> <build-number>" >&2
  exit 2
fi
release_dir=$(mktemp -d "${TMPDIR:-/tmp}/onionary-testflight.XXXXXX")
cd "$package_dir"
stage() {
  echo "Release stage: $1"
  if [[ -n "${ONIONARY_RELEASE_STAGE_FILE:-}" ]]; then printf '%s' "$1" > "$ONIONARY_RELEASE_STAGE_FILE"; fi
}
archive_path=${3:-$release_dir/Onionary.xcarchive}
if [[ $# -ge 3 ]]; then
  if [[ ! -d "$archive_path" ]]; then
    echo "Archive does not exist: $archive_path" >&2
    exit 2
  fi
else
# A release must pass both core and simulator UI tests before archiving.
python3 ../../execution/check_ios_build_environment.py
stage tests
# One compact regression suite, one iPad suite, and the Duo continuity suite.
# Each creates its own compatible simulator; any failure stops the release.
# Exercise the previously failing profile first; every profile remains required.
for device in com.apple.CoreSimulator.SimDeviceType.iPhone-Duo \
              com.apple.CoreSimulator.SimDeviceType.iPad-Pro-13-inch-M5-16GB \
              com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro; do
  stage "tests:${device##*.}"
  profile_results="$release_dir/tests-${device##*.}"
  # Same source/SDK, sequential destinations: reuse Xcode's validated build cache.
  # Repeated delete/rebuild cycles retain old blocks in APFS snapshots and can
  # exhaust disk despite deleting each previous profile's DerivedData.
  TEST_RESULTS_DIR="$profile_results" TEST_DERIVED_DATA_DIR="$release_dir/DerivedData" \
    SIMULATOR_DEVICE_TYPE="$device" bash Scripts/test.sh
done
rm -rf "$release_dir/DerivedData"
stage archive
ARCHIVE_SIGNED=1 bash Scripts/archive.sh "$archive_path" "$marketing_version" "$build_number"
fi
stage upload
env PATH=/usr/bin:/bin:/usr/sbin:/sbin /usr/bin/xcodebuild -exportArchive -archivePath "$archive_path" \
  -exportPath "$release_dir/export" -exportOptionsPlist ExportOptions.TestFlight.plist \
  -allowProvisioningUpdates
stage uploaded
echo "TestFlight upload accepted. Archive: $archive_path"
