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
archive_path=${3:-$release_dir/Onionary.xcarchive}
if [[ $# -ge 3 ]]; then
  if [[ ! -d "$archive_path" ]]; then
    echo "Archive does not exist: $archive_path" >&2
    exit 2
  fi
else
# A release must pass both core and simulator UI tests before archiving.
bash Scripts/test.sh
env PATH=/usr/bin:/bin:/usr/sbin:/sbin /usr/bin/xcodebuild -project Onionary.xcodeproj -scheme Onionary -configuration Release \
  -destination 'generic/platform=iOS' -archivePath "$archive_path" \
  DEVELOPMENT_TEAM=VWKG94374J \
  MARKETING_VERSION="$marketing_version" CURRENT_PROJECT_VERSION="$build_number" \
  CODE_SIGN_STYLE=Automatic -allowProvisioningUpdates archive
fi
env PATH=/usr/bin:/bin:/usr/sbin:/sbin /usr/bin/xcodebuild -exportArchive -archivePath "$archive_path" \
  -exportPath "$release_dir/export" -exportOptionsPlist ExportOptions.TestFlight.plist \
  -allowProvisioningUpdates
echo "TestFlight upload accepted. Archive: $archive_path"
