#!/usr/bin/env bash
set -euo pipefail
package_dir=$(cd "$(dirname "$0")/.." && pwd)
cd "$package_dir"
python3 ../../execution/check_ios_build_environment.py --stage test
swift test
marketing_version=$(python3 ../../execution/version.py --ios)
xcodegen generate
python3 ../../execution/check_ios_build_environment.py --test-scheme Onionary.xcodeproj/xcshareddata/xcschemes/Onionary.xcscheme
result_dir=${TEST_RESULTS_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/onionary-tests.XXXXXX")}
mkdir -p "$result_dir"
result_dir=$(cd "$result_dir" && pwd)
created_simulator=false
if [[ -n "${SIMULATOR_ID:-}" ]]; then
  simulator_id=$SIMULATOR_ID
else
  simulator_id=$(python3 Scripts/resolve_simulator.py --create --device-type "${SIMULATOR_DEVICE_TYPE:-com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro}" --runtime "${SIMULATOR_RUNTIME:-}")
  created_simulator=true
fi
cleanup() {
  local result=$?
  trap - EXIT
  if [[ "$result" != 0 ]]; then
    # Preserve the original failure. Diagnostics are read-only and bounded;
    # neither an unavailable log service nor cleanup can replace its exit code.
    python3 ../../execution/run_bounded.py --log "$result_dir/host-diagnostics.log" 60 \
      python3 ../../execution/collect_ios_test_diagnostics.py \
      --simulator "$simulator_id" --output "$result_dir/host-diagnostics" || true
  fi
  if [[ "$created_simulator" == true ]]; then
    xcrun simctl delete "$simulator_id" >/dev/null 2>&1 || true
  fi
  exit "$result"
}
trap cleanup EXIT
# Give compilation its own budget: cold builds must not consume UI test time.
build_args=(-project Onionary.xcodeproj -scheme Onionary
  -destination "platform=iOS Simulator,id=$simulator_id" -derivedDataPath "${TEST_DERIVED_DATA_DIR:-$result_dir/DerivedData}"
  MARKETING_VERSION="$marketing_version" CODE_SIGNING_ALLOWED=NO COMPILER_INDEX_STORE_ENABLE=NO)
python3 ../../execution/run_bounded.py --log "$result_dir/build.log" 1200 xcodebuild "${build_args[@]}" build-for-testing
if [[ "$created_simulator" == true ]]; then
  # Compile against a shutdown device. Fresh runtime indexing and cold Swift
  # compilation must not compete for memory/disk before XCTest loads accessibility.
  # Start monitoring before boot, rather than attaching after boot returned.
  python3 ../../execution/run_bounded.py 600 xcrun simctl bootstatus "$simulator_id" -b
fi
# Runtime bundle metadata was checked before creation. Do not add a post-boot
# simctl getenv/spawn probe: cold hosted guests can stall that extra RPC before
# XCTest starts. The runner records its OS version directly when it initializes.
test_allowance=180
if [[ "${SIMULATOR_DEVICE_TYPE:-}" == *iPhone-Duo ]]; then test_allowance=360; fi
# Keep XCTest failures/attachments, but avoid Xcode's simulator-wide sysdiagnose
# collector (which stalls for 600 seconds even after a fully passed suite).
test_args=("${build_args[@]}" -parallel-testing-enabled NO -collect-test-diagnostics never -test-timeouts-enabled YES
  -default-test-execution-time-allowance "$test_allowance" -maximum-test-execution-time-allowance "$test_allowance"
  -resultBundlePath "$result_dir/Onionary.xcresult" test-without-building)
if [[ "${SIMULATOR_DEVICE_TYPE:-}" == *iPhone-Duo ]]; then
  python3 ../../execution/run_bounded.py --log "$result_dir/tests.log" 1800 xcodebuild "${test_args[@]}" \
    -only-testing:OnionaryUITests/OnionaryDuoTests
else
  python3 ../../execution/run_bounded.py --log "$result_dir/tests.log" 1800 xcodebuild "${test_args[@]}" \
    -only-testing:OnionaryUITests/OnionaryUITests
fi
echo "Test results: $result_dir/Onionary.xcresult"
