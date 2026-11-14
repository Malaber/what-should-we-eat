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
device_type=${SIMULATOR_DEVICE_TYPE:-com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro}
simulator_id=${SIMULATOR_ID:-}
create_simulator() {
  simulator_id=$(python3 Scripts/resolve_simulator.py --create --device-type "$device_type" --runtime "${SIMULATOR_RUNTIME:-}")
}
delete_owned_simulator() {
  if [[ -z "${SIMULATOR_ID:-}" && -n "$simulator_id" ]]; then
    xcrun simctl delete "$simulator_id" >/dev/null 2>&1 || true
    simulator_id=
  fi
}
cleanup() {
  local result=$?
  trap - EXIT
  if [[ "$result" != 0 && -n "$simulator_id" ]]; then
    # Preserve the original failure. Diagnostics are read-only and bounded;
    # neither an unavailable log service nor cleanup can replace its exit code.
    python3 ../../execution/run_bounded.py --log "$result_dir/host-diagnostics.log" 60 \
      python3 ../../execution/collect_ios_test_diagnostics.py \
      --simulator "$simulator_id" --output "$result_dir/host-diagnostics" || true
  fi
  delete_owned_simulator
  exit "$result"
}
trap cleanup EXIT
if [[ -z "$simulator_id" ]]; then create_simulator; fi
# Give compilation its own budget: cold builds must not consume UI test time.
derived_data=${TEST_DERIVED_DATA_DIR:-$result_dir/DerivedData}
# Headless automation does not use SwiftUI Previews. Link the app normally,
# without the extra Preview stub/debug-dylib loader at every cold launch.
# A command-line setting leaves developer previews and Release archives alone.
build_args=(-project Onionary.xcodeproj -scheme Onionary
  -destination "platform=iOS Simulator,id=$simulator_id" -derivedDataPath "$derived_data"
  MARKETING_VERSION="$marketing_version" CODE_SIGNING_ALLOWED=NO COMPILER_INDEX_STORE_ENABLE=NO ENABLE_DEBUG_DYLIB=NO)
python3 ../../execution/run_bounded.py --log "$result_dir/build.log" 1200 xcodebuild "${build_args[@]}" build-for-testing
python3 ../../execution/check_ios_build_environment.py --test-app "$derived_data/Build/Products/Debug-iphonesimulator/Onionary.app"
test_plan=$(python3 ../../execution/check_ios_build_environment.py --test-products "$derived_data/Build/Products")
run_tests() {
  local output=$1 allowance=$2
  shift 2
  mkdir -p "$output"
  if [[ -z "${SIMULATOR_ID:-}" ]]; then
    # Cold compilation is complete before the first guest boots. Avoid extra
    # post-boot guest RPCs before XCTest starts.
    python3 ../../execution/run_bounded.py 600 xcrun simctl bootstatus "$simulator_id" -b
  fi
  python3 ../../execution/run_bounded.py --startup-seconds 600 --ready-prefix "Test Suite 'Selected tests' started at " \
    --log "$output/tests.log" 1800 xcodebuild -xctestrun "$test_plan" \
    -destination "platform=iOS Simulator,id=$simulator_id" \
    -parallel-testing-enabled NO -collect-test-diagnostics never -test-timeouts-enabled YES \
    -default-test-execution-time-allowance "$allowance" -maximum-test-execution-time-allowance "$allowance" \
    -resultBundlePath "$output/Onionary.xcresult" test-without-building "$@"
}

if [[ "$device_type" != *iPhone-Duo ]]; then
  run_tests "$result_dir" 180 -only-testing:OnionaryUITests/OnionaryUITests
elif [[ -n "${SIMULATOR_ID:-}" ]]; then
  run_tests "$result_dir" 360 -only-testing:OnionaryUITests/OnionaryDuoTests
else
  # Each fold scenario starts with a clean SpringBoard/AX session. Reusing the
  # guest forces XCTest to terminate a process tracked by the previous display.
  duo_cases=$(sed -nE 's/^[[:space:]]*(@MainActor[[:space:]]+)?func (test[A-Za-z0-9_]+)\(\).*/\2/p' UITests/OnionaryDuoTests.swift)
  [[ -n "$duo_cases" ]] || { echo 'No Duo test cases found' >&2; exit 1; }
  while IFS= read -r scenario; do
    if [[ -z "$simulator_id" ]]; then create_simulator; fi
    run_tests "$result_dir/duo/$scenario" 360 "-only-testing:OnionaryUITests/OnionaryDuoTests/$scenario"
    delete_owned_simulator
  done <<< "$duo_cases"
fi
echo "Test results: $result_dir"
