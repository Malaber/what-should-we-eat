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
for device in com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro \
              com.apple.CoreSimulator.SimDeviceType.iPad-Pro-13-inch-M5-16GB \
              com.apple.CoreSimulator.SimDeviceType.iPhone-Duo; do
  profile_results="$release_dir/tests-${device##*.}"
  TEST_RESULTS_DIR="$profile_results" SIMULATOR_DEVICE_TYPE="$device" bash Scripts/test.sh
  # A completed profile retains its xcresult; its isolated build is reproducible.
  rm -rf "$profile_results/DerivedData"
done
stage archive
ARCHIVE_SIGNED=1 bash Scripts/archive.sh "$archive_path" "$marketing_version" "$build_number"
fi
stage upload
env PATH=/usr/bin:/bin:/usr/sbin:/sbin /usr/bin/xcodebuild -exportArchive -archivePath "$archive_path" \
  -exportPath "$release_dir/export" -exportOptionsPlist ExportOptions.TestFlight.plist \
  -allowProvisioningUpdates
stage uploaded
echo "TestFlight upload accepted. Archive: $archive_path"
