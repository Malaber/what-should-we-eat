#!/usr/bin/env python3
"""Select a deterministic phone layout, rather than the first installed device."""
import argparse
import json
import subprocess

DEFAULT_DEVICE = 'com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro'


def select_runtime(runtimes, device_type=DEFAULT_DEVICE):
    available = [runtime for runtime in runtimes if runtime.get('isAvailable')
                 and '.iOS-' in runtime['identifier']
                 and any(device['identifier'] == device_type
                         for device in runtime.get('supportedDeviceTypes', []))]
    if not available:
        raise ValueError('Install an iOS runtime compatible with the selected device in Xcode Settings > Components.')
    return max(available, key=lambda runtime: tuple(int(p) for p in runtime['version'].split('.')))['identifier']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--create', action='store_true')
    parser.add_argument('--device-type', default=DEFAULT_DEVICE)
    args = parser.parse_args()
    runtimes = json.loads(subprocess.check_output(['xcrun', 'simctl', 'list', 'runtimes', '--json']))['runtimes']
    runtime = select_runtime(runtimes, args.device_type)
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
