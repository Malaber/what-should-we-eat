#!/usr/bin/env bash
set -euo pipefail
package_dir=$(cd "$(dirname "$0")/.." && pwd)
cd "$package_dir"
swift test
marketing_version=$(python3 ../../execution/version.py --ios)
xcodegen generate
if [[ -n "${SIMULATOR_ID:-}" ]]; then
  simulator_id=$SIMULATOR_ID
else
  simulator_id=$(python3 Scripts/resolve_simulator.py --create)
  trap 'xcrun simctl delete "$simulator_id" >/dev/null 2>&1 || true' EXIT
  xcrun simctl boot "$simulator_id"
  python3 ../../execution/run_bounded.py 180 xcrun simctl bootstatus "$simulator_id" -b
fi
result_dir=${TEST_RESULTS_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/onionary-tests.XXXXXX")}
mkdir -p "$result_dir"
result_dir=$(cd "$result_dir" && pwd)
python3 ../../execution/run_bounded.py 900 xcodebuild -project Onionary.xcodeproj -scheme Onionary \
  -destination "platform=iOS Simulator,id=$simulator_id" -derivedDataPath "$result_dir/DerivedData" \
  -parallel-testing-enabled NO -test-timeouts-enabled YES \
  -default-test-execution-time-allowance 120 -maximum-test-execution-time-allowance 180 \
  -resultBundlePath "$result_dir/Onionary.xcresult" \
  MARKETING_VERSION="$marketing_version" CODE_SIGNING_ALLOWED=NO test
echo "Test results: $result_dir/Onionary.xcresult"
