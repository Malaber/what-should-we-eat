#!/usr/bin/env python3
"""Select a deterministic phone layout, rather than the first installed device."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from execution.ios_runtime import DEFAULT_DEVICE, default_runtime, runtime_build, runtime_identifier


def select_runtime(runtimes, device_type=DEFAULT_DEVICE, version=None):
    version = version or default_runtime(device_type)
    build = runtime_build(version)
    available = [runtime for runtime in runtimes if runtime.get('isAvailable')
                 and runtime.get('identifier') == runtime_identifier(version)
                 and runtime.get('version') == version
                 and runtime.get('buildversion') == build
                 and Path(runtime.get('bundlePath', '')).is_absolute()
                 and any(device['identifier'] == device_type
                         for device in runtime.get('supportedDeviceTypes', []))]
    if not available:
        raise ValueError(f'Install iOS {version} ({build}) compatible with {device_type}; no fallback to a different runtime is allowed.')
    # RC and stable builds can share an identifier. simctl create also accepts
    # a runtime bundle path, which identifies the exact installed build.
    return sorted(runtime['bundlePath'] for runtime in available)[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--create', action='store_true')
    parser.add_argument('--device-type', default=DEFAULT_DEVICE)
    parser.add_argument('--runtime', help='Exact iOS version; defaults to the profile pin')
    args = parser.parse_args()
    runtimes = json.loads(subprocess.check_output(['xcrun', 'simctl', 'list', 'runtimes', '--json']))['runtimes']
    runtime = select_runtime(runtimes, args.device_type, args.runtime)
    version = args.runtime or default_runtime(args.device_type)
    print(f"Selected iOS {version} ({runtime_build(version)}) at {runtime} for {args.device_type}", file=sys.stderr)
    if args.create:
        print(subprocess.check_output(['xcrun', 'simctl', 'create', 'Onionary Isolated Tests',
                                       args.device_type, runtime], text=True).strip())
    else:
        devices = json.loads(subprocess.check_output(['xcrun', 'simctl', 'list', 'devices', 'available', '--json']))['devices']
        matching = [d for d in devices.get(runtime_identifier(version), [])
                    if d.get('deviceTypeIdentifier') == args.device_type]
        if not matching:
            raise SystemExit('No matching simulator exists; use --create.')
        print(sorted(matching, key=lambda d: d['udid'])[0]['udid'])


if __name__ == '__main__':
    main()
