"""Install missing pinned runtimes and verify availability after every download."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from execution.ios_runtime import (
    DEFAULT_DEVICE, RUNTIME_VERSION, available_runtime, configure_sdk_runtime,
    prepare_runtime_cache, read_command, runtime_build, verify_runtime_bundle,
)


def available(version, device_type):
    runtimes = json.loads(read_command("xcrun", "simctl", "list", "runtimes", "--json"))["runtimes"]
    return available_runtime(runtimes, version, device_type)


def ensure(version, device_type):
    build = runtime_build(version, device_type)
    bundle = available(version, device_type)
    if bundle is None:
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
        bundle = available(version, device_type)
        if bundle is None:
            raise RuntimeError(
                f"iOS {version} ({build}) for {device_type} unavailable after download "
                f"(exit {result.returncode})"
            )
    verify_runtime_bundle(bundle, version, device_type)
    print(f"Verified iOS {version} ({build}) for {device_type}", flush=True)
    configure_sdk_runtime(version, device_type)
    prepare_runtime_cache(version, device_type)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", nargs="?", choices=(RUNTIME_VERSION,), default=RUNTIME_VERSION)
    parser.add_argument("--device-type", default=DEFAULT_DEVICE)
    args = parser.parse_args()
    ensure(args.version, args.device_type)

