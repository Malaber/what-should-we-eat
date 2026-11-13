"""Exact simulator build pins, disposable-CI SDK mapping and bundle validation."""

import json
import os
from pathlib import Path
import plistlib
import subprocess

RUNTIME_BUILDS = {"27.0": "24A434", "27.1": "24A94425"}
DEFAULT_DEVICE = "com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro"


def default_runtime(device_type):
    return "27.1" if device_type.endswith(".iPhone-Duo") else "27.0"


def runtime_build(version):
    if version not in RUNTIME_BUILDS:
        raise ValueError(f"No simulator build pin for iOS {version}; no fallback is allowed.")
    return RUNTIME_BUILDS[version]


def runtime_identifier(version):
    return "com.apple.CoreSimulator.SimRuntime.iOS-" + version.replace(".", "-")


def read_command(*arguments):
    return subprocess.check_output(list(arguments), text=True, timeout=15).strip()


def configure_sdk_runtime(version, environ=None):
    """Map duplicate OS builds explicitly, without changing developer preferences."""
    expected = runtime_build(version)
    sdk_version = read_command("xcrun", "--sdk", "iphonesimulator", "--show-sdk-version")
    if sdk_version != version:
        return  # SDK mappings concern the matching OS version, not older runtimes.
    sdk_build = read_command("xcrun", "--sdk", "iphonesimulator", "--show-sdk-build-version")
    # CoreSimulator uses the device SDK canonical name for its simulator mapping.
    canonical = "iphoneos" + version

    def selected_build():
        mappings = json.loads(read_command("xcrun", "simctl", "runtime", "match", "list", "-j"))
        return mappings.get(canonical, {}).get("chosenRuntimeBuild")

    if selected_build() == expected:
        return
    command = ["xcrun", "simctl", "runtime", "match", "set", canonical,
               expected, "--sdkBuild", sdk_build]
    environ = os.environ if environ is None else environ
    if not (environ.get("GITHUB_ACTIONS") == "true"
            and environ.get("RUNNER_ENVIRONMENT") == "github-hosted"):
        raise RuntimeError(
            f"SDK {sdk_version} selects a different runtime build. "
            f"No local preferences changed. To select the pinned build explicitly: {' '.join(command)}"
        )
    subprocess.run(command, check=True, timeout=15)
    if selected_build() != expected:
        raise RuntimeError(f"SDK {sdk_version} did not select pinned runtime {expected}")
    print(f"Mapped SDK {sdk_version} ({sdk_build}) to runtime {expected}", flush=True)


def verify_runtime_bundle(bundle, version):
    """Validate installed system metadata before creating/booting a guest."""
    expected = runtime_build(version)
    if not Path(bundle).is_absolute():
        raise ValueError("Runtime bundle must be an absolute path")
    root = Path(bundle) / "Contents/Resources/RuntimeRoot"
    with (Path(root) / "System/Library/CoreServices/SystemVersion.plist").open("rb") as source:
        metadata = plistlib.load(source)
    actual = (metadata.get("ProductVersion"), metadata.get("ProductBuildVersion"))
    if actual != (version, expected):
        raise RuntimeError(
            f"Runtime bundle {bundle} contains iOS {actual[0]} ({actual[1]}); "
            f"required iOS {version} ({expected}). Simulator was not created."
        )
