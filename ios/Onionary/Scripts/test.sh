#!/usr/bin/env bash
set -euo pipefail
package_dir=$(cd "$(dirname "$0")/.." && pwd)
cd "$package_dir"
mode=${1:-all}
case "$mode" in
  all|--build-only|--test-only) ;;
  *) echo "Usage: $0 [--build-only | --test-only]" >&2; exit 2 ;;
esac
python3 ../../execution/check_ios_build_environment.py --stage test
result_dir=${TEST_RESULTS_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/onionary-tests.XXXXXX")}
mkdir -p "$result_dir"
result_dir=$(cd "$result_dir" && pwd)
derived_data=${TEST_DERIVED_DATA_DIR:-$result_dir/DerivedData}
products="$derived_data/Build/Products"

build_for_testing() {
  local destination=$1 marketing_version
  swift test
  marketing_version=$(python3 ../../execution/version.py --ios)
  xcodegen generate
  python3 ../../execution/check_ios_build_environment.py --test-scheme Onionary.xcodeproj/xcshareddata/xcschemes/Onionary.xcscheme
  # Link normally for headless tests without the SwiftUI Preview debug loader.
  python3 ../../execution/run_bounded.py --log "$result_dir/build.log" 1200 xcodebuild \
    -project Onionary.xcodeproj -scheme Onionary -destination "$destination" \
    -derivedDataPath "$derived_data" MARKETING_VERSION="$marketing_version" \
    ARCHS=arm64 CODE_SIGNING_ALLOWED=NO COMPILER_INDEX_STORE_ENABLE=NO ENABLE_DEBUG_DYLIB=NO build-for-testing
}

validate_test_products() {
  python3 ../../execution/check_ios_build_environment.py --test-app "$products/Debug-iphonesimulator/Onionary.app"
  test_plan=$(python3 ../../execution/check_ios_build_environment.py --test-products "$products")
}

if [[ "$mode" == --build-only ]]; then
  build_for_testing 'generic/platform=iOS Simulator'
  validate_test_products
  exit
fi

device_type=${SIMULATOR_DEVICE_TYPE:-com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro}
shard=all
if [[ "$mode" == --test-only ]]; then shard=${SIMULATOR_TEST_SHARD:-all}; fi
if [[ "$device_type" == *iPhone-Duo ]]; then
  duo_cases=$(sed -nE 's/^[[:space:]]*(@MainActor[[:space:]]+)?func (test[A-Za-z0-9_]+)\(\).*/\2/p' UITests/OnionaryDuoTests.swift)
  [[ -n "$duo_cases" ]] || { echo 'No Duo test cases found' >&2; exit 1; }
  if [[ "$shard" != all ]]; then
    if ! grep -Fxq -- "$shard" <<< "$duo_cases"; then
      echo "Unknown Duo test case: $shard" >&2
      exit 2
    fi
    duo_cases=$shard
  fi
else
  case "$shard" in
    all|1|2|3) ;;
    *) echo "Invalid simulator test shard: $shard" >&2; exit 2 ;;
  esac
fi
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
if [[ "$mode" == all ]]; then
  if [[ -z "$simulator_id" ]]; then create_simulator; fi
  build_for_testing "platform=iOS Simulator,id=$simulator_id"
fi
validate_test_products
if [[ -z "$simulator_id" ]]; then create_simulator; fi
run_tests() {
  local output=$1 allowance=$2
  shift 2
  mkdir -p "$output"
  # Keep the new device shut down until XCTest takes ownership of its boot,
  # app installation and test session. A prebooted session can disappear
  # while xcodebuild is still initializing its runner.
  python3 ../../execution/run_bounded.py --startup-seconds 600 --ready-prefix "Test Suite 'Selected tests' started at " \
    --log "$output/tests.log" 1800 xcodebuild -xctestrun "$test_plan" \
    -destination "platform=iOS Simulator,id=$simulator_id" \
    -parallel-testing-enabled NO -collect-test-diagnostics never -test-timeouts-enabled YES \
    -default-test-execution-time-allowance "$allowance" -maximum-test-execution-time-allowance "$allowance" \
    -resultBundlePath "$output/Onionary.xcresult" test-without-building "$@"
}

if [[ "$device_type" != *iPhone-Duo && "$shard" == all ]]; then
  run_tests "$result_dir" 180 -only-testing:OnionaryUITests/OnionaryUITests
elif [[ "$device_type" != *iPhone-Duo ]]; then
  # A fresh standard runner runs each third of the suite. Keep the capture
  # case on shard 1 and balance all other cases in a stable order.
  native_cases=$(sed -nE 's/^[[:space:]]*(@MainActor[[:space:]]+)?func (test[A-Za-z0-9_]+)\(\).*/\2/p' UITests/OnionaryUITests.swift | LC_ALL=C sort)
  [[ -n "$native_cases" ]] || { echo 'No iPhone or iPad test cases found' >&2; exit 1; }
  tests=()
  index=0
  while IFS= read -r scenario; do
    [[ -n "$scenario" ]] || continue
    if [[ "$scenario" == testMarketingScreenshots ]]; then
      assigned=1
    else
      assigned=$(( (index + 1) % 3 + 1 ))
      index=$(( index + 1 ))
    fi
    if [[ "$assigned" == "$shard" ]]; then
      tests+=("-only-testing:OnionaryUITests/OnionaryUITests/$scenario")
    fi
  done <<< "$native_cases"
  [[ ${#tests[@]} -gt 0 ]] || { echo "No UI tests found in shard $shard" >&2; exit 1; }
  run_tests "$result_dir" 180 "${tests[@]}"
elif [[ -n "${SIMULATOR_ID:-}" && "$shard" == all ]]; then
  run_tests "$result_dir" 360 -only-testing:OnionaryUITests/OnionaryDuoTests
else
  # Each fold scenario starts with a clean SpringBoard/AX session. Reusing the
  # guest forces XCTest to terminate a process tracked by the previous display.
  # CI selects one case per VM. Local full runs use the Duo source order.
  while IFS= read -r scenario; do
    if [[ -z "$simulator_id" ]]; then create_simulator; fi
    run_tests "$result_dir/duo/$scenario" 360 "-only-testing:OnionaryUITests/OnionaryDuoTests/$scenario"
    delete_owned_simulator
  done <<< "$duo_cases"
fi
echo "Test results: $result_dir"
