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
stage tests
bash Scripts/test.sh
stage archive
ARCHIVE_SIGNED=1 bash Scripts/archive.sh "$archive_path" "$marketing_version" "$build_number"
fi
stage upload
env PATH=/usr/bin:/bin:/usr/sbin:/sbin /usr/bin/xcodebuild -exportArchive -archivePath "$archive_path" \
  -exportPath "$release_dir/export" -exportOptionsPlist ExportOptions.TestFlight.plist \
  -allowProvisioningUpdates
stage uploaded
echo "TestFlight upload accepted. Archive: $archive_path"
