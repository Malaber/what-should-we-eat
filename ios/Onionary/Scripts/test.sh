#!/usr/bin/env bash
set -euo pipefail
package_dir=$(cd "$(dirname "$0")/.." && pwd)
cd "$package_dir"
swift test
marketing_version=$(python3 ../../execution/version.py --ios)
xcodegen generate
simulator_id=${SIMULATOR_ID:-$(python3 Scripts/resolve_simulator.py)}
result_dir=${TEST_RESULTS_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/onionary-tests.XXXXXX")}
mkdir -p "$result_dir"
result_dir=$(cd "$result_dir" && pwd)
xcodebuild -project Onionary.xcodeproj -scheme Onionary \
  -destination "platform=iOS Simulator,id=$simulator_id" -derivedDataPath "$result_dir/DerivedData" \
  -parallel-testing-enabled NO -resultBundlePath "$result_dir/Onionary.xcresult" \
  MARKETING_VERSION="$marketing_version" CODE_SIGNING_ALLOWED=NO test
echo "Test results: $result_dir/Onionary.xcresult"
