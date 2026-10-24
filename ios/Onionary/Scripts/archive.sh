#!/usr/bin/env bash
# Same Release/device archive for CI and TestFlight; CI omits signing credentials.
set -euo pipefail
package_dir=$(cd "$(dirname "$0")/.." && pwd)
cd "$package_dir"
archive_path=$1
marketing_version=$2
build_number=$3
xcodegen generate
signing=(CODE_SIGNING_ALLOWED=NO)
if [[ "${ARCHIVE_SIGNED:-0}" == 1 ]]; then
  signing=(DEVELOPMENT_TEAM=VWKG94374J CODE_SIGN_STYLE=Automatic -allowProvisioningUpdates)
fi
env PATH=/usr/bin:/bin:/usr/sbin:/sbin /usr/bin/xcodebuild   -project Onionary.xcodeproj -scheme Onionary -configuration Release   -destination 'generic/platform=iOS' -archivePath "$archive_path"   MARKETING_VERSION="$marketing_version" CURRENT_PROJECT_VERSION="$build_number"   "${signing[@]}" archive
python3 - "$archive_path" "$marketing_version" "$build_number" <<'PY'
import plistlib
from pathlib import Path
import sys
root = Path(sys.argv[1]) / "Products/Applications/Onionary.app"
bundles = [root, *sorted((root / "PlugIns").glob("*.appex"))]
assert len(bundles) == 3, "Expected app, share extension and widget"
for bundle in bundles:
    with (bundle / "Info.plist").open("rb") as f:
        info = plistlib.load(f)
    assert info["CFBundleShortVersionString"] == sys.argv[2], bundle
    assert str(info["CFBundleVersion"]) == sys.argv[3], bundle
    assert (bundle / info["CFBundleExecutable"]).is_file(), bundle
    print(f"Validated {info['CFBundleIdentifier']} {sys.argv[2]} ({sys.argv[3]})")
PY
