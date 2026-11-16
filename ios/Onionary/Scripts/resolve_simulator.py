#!/usr/bin/env python3
"""Select a deterministic phone layout, rather than the first installed device."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from execution.ios_runtime import (
    DEFAULT_DEVICE, RUNTIME_VERSION, available_runtime, runtime_build, runtime_identifier, verify_runtime_bundle,
)


def select_runtime(runtimes, device_type=DEFAULT_DEVICE, version=None):
    version = version or RUNTIME_VERSION
    bundle = available_runtime(runtimes, version, device_type)
    if bundle is None:
        build = runtime_build(version, device_type)
        raise ValueError(f'Install iOS {version} ({build}) compatible with {device_type}; no fallback to a different runtime is allowed.')
    return bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--create', action='store_true')
    parser.add_argument('--device-type', default=DEFAULT_DEVICE)
    parser.add_argument('--runtime', help='Exact iOS version; defaults to the profile pin')
    parser.add_argument('--device-set', type=Path)
    args = parser.parse_args()
    simctl = ['xcrun', 'simctl']
    if args.device_set:
        simctl.extend(['--set', str(args.device_set)])
    runtimes = json.loads(subprocess.check_output([*simctl, 'list', 'runtimes', '--json']))['runtimes']
    runtime = select_runtime(runtimes, args.device_type, args.runtime)
    version = args.runtime or RUNTIME_VERSION
    verify_runtime_bundle(runtime, version, args.device_type)
    print(f"Verified installed iOS {version} ({runtime_build(version, args.device_type)}) at {runtime} for {args.device_type}", file=sys.stderr)
    if args.create:
        print(subprocess.check_output([*simctl, 'create', 'Onionary Isolated Tests',
                                       args.device_type, runtime], text=True).strip())
    else:
        devices = json.loads(subprocess.check_output([*simctl, 'list', 'devices', 'available', '--json']))['devices']
        matching = [d for d in devices.get(runtime_identifier(version), [])
                    if d.get('deviceTypeIdentifier') == args.device_type]
        if not matching:
            raise SystemExit('No matching simulator exists; use --create.')
        print(sorted(matching, key=lambda d: d['udid'])[0]['udid'])


if __name__ == '__main__':
    main()
