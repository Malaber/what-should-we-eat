#!/usr/bin/env python3
"""Select a deterministic phone layout, rather than the first installed device."""
import argparse
import json
import subprocess
import sys

DEFAULT_DEVICE = 'com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro'


def default_runtime(device_type):
    return '27.1' if device_type.endswith('.iPhone-Duo') else '27.0'


def select_runtime(runtimes, device_type=DEFAULT_DEVICE, version=None):
    version = version or default_runtime(device_type)
    available = [runtime for runtime in runtimes if runtime.get('isAvailable')
                 and runtime['identifier'] == 'com.apple.CoreSimulator.SimRuntime.iOS-' + version.replace('.', '-')
                 and runtime['version'] == version
                 and any(device['identifier'] == device_type
                         for device in runtime.get('supportedDeviceTypes', []))]
    if not available:
        raise ValueError(f'Install iOS {version} compatible with {device_type}; no fallback to a different runtime is allowed.')
    return available[0]['identifier']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--create', action='store_true')
    parser.add_argument('--device-type', default=DEFAULT_DEVICE)
    parser.add_argument('--runtime', help='Exact iOS version; defaults to the profile pin')
    args = parser.parse_args()
    runtimes = json.loads(subprocess.check_output(['xcrun', 'simctl', 'list', 'runtimes', '--json']))['runtimes']
    runtime = select_runtime(runtimes, args.device_type, args.runtime)
    print(f"Selected {runtime} for {args.device_type}", file=sys.stderr)
    if args.create:
        print(subprocess.check_output(['xcrun', 'simctl', 'create', 'Onionary Isolated Tests',
                                       args.device_type, runtime], text=True).strip())
    else:
        devices = json.loads(subprocess.check_output(['xcrun', 'simctl', 'list', 'devices', 'available', '--json']))['devices']
        matching = [d for d in devices.get(runtime, []) if d.get('deviceTypeIdentifier') == args.device_type]
        if not matching:
            raise SystemExit('No matching simulator exists; use --create.')
        print(sorted(matching, key=lambda d: d['udid'])[0]['udid'])


if __name__ == '__main__':
    main()
