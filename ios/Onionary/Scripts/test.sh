#!/usr/bin/env bash
set -euo pipefail
package_dir=$(cd "$(dirname "$0")/.." && pwd)
cd "$package_dir"
swift test
xcodegen generate
simulator_id=${SIMULATOR_ID:-$(python3 Scripts/resolve_simulator.py)}
result_dir=$(mktemp -d "${TMPDIR:-/tmp}/onionary-tests.XXXXXX")
xcodebuild -project Onionary.xcodeproj -scheme Onionary \
  -destination "platform=iOS Simulator,id=$simulator_id" \
  -parallel-testing-enabled NO -resultBundlePath "$result_dir/Onionary.xcresult" \
  CODE_SIGNING_ALLOWED=NO test
echo "Test results: $result_dir/Onionary.xcresult"
