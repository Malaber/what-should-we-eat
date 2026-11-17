"""Install missing pinned runtimes and verify availability after every download."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from execution.ios_runtime import (
    DEFAULT_DEVICE, RUNTIME_VERSION, available_runtime, configure_sdk_runtime,
    prepare_runtime_cache, read_command, runtime_build, runtime_identifier, verify_runtime_bundle,
)


def available(version, device_type, *, report_missing=False):
    runtimes = json.loads(read_command("xcrun", "simctl", "list", "runtimes", "--json"))["runtimes"]
    selected = available_runtime(runtimes, version, device_type)
    if selected is None and report_missing:
        for runtime in runtimes:
            if runtime.get('version') == version:
                supports_device = any(entry.get('identifier') == device_type
                                      for entry in runtime.get('supportedDeviceTypes', []))
                print(f"Found {runtime.get('identifier')} build {runtime.get('buildversion')}, "
                      f"available={runtime.get('isAvailable')}, supports device={supports_device}", flush=True)
    return selected


def ensure(version, device_type):
    build = runtime_build(version, device_type)
    runtime = available(version, device_type)
    if runtime is None:
        result = subprocess.run(
            [
                "xcodebuild",
                "-downloadPlatform",
                "iOS",
                "-buildVersion",
                build,
                "-architectureVariant",
                "arm64",
            ],
            check=False, timeout=1200,
        )
        # Xcode may return 70 for a cached download. Availability is authoritative;
        # a nonzero exit never excuses an absent or mismatched runtime.
        runtime = available(version, device_type, report_missing=True)
        if runtime is None:
            raise RuntimeError(
                f"iOS {version} ({build}) for {device_type} unavailable after download "
                f"(exit {result.returncode})"
            )
    verify_runtime_bundle(runtime['bundlePath'], version, device_type)
    identifier = runtime['identifier']
    print(f"Verified iOS {version} ({build}) for {device_type}: {identifier}", flush=True)
    # The Duo-specific identifier selects its own runtime alongside the generic
    # iPhoneOS SDK match. Only the generic identifier needs SDK remapping.
    if identifier == runtime_identifier(version):
        configure_sdk_runtime(version, device_type)
    prepare_runtime_cache(version, device_type)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", nargs="?", choices=(RUNTIME_VERSION,), default=RUNTIME_VERSION)
    parser.add_argument("--device-type", default=DEFAULT_DEVICE)
    args = parser.parse_args()
    ensure(args.version, args.device_type)

