"""Fail before expensive iOS work when Xcode or disk cannot support the build."""
import argparse
import os
from pathlib import Path
import plistlib
import shutil
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET

EXPECTED_XCODE = "Xcode 27.1\nBuild version 27A9275"
# Release profiles are sequential and reuse one release-specific DerivedData.
# Entry needs one test profile's reserve, not a cumulative-build reserve.
# test.sh and archive.sh independently recheck space immediately before their work.
STAGE_GIB = {"release": 8, "test": 8, "archive": 6}
MIN_FREE_BYTES = STAGE_GIB["release"] * 1024 ** 3


def validate_xcode(output):
    if output.strip() != EXPECTED_XCODE:
        raise ValueError(f"Expected {EXPECTED_XCODE!r}; found {output.strip()!r}. Use the xcode-27 runner and Xcode_27.1.app.")


def validate_disk(path, free_bytes, minimum_bytes=MIN_FREE_BYTES):
    if free_bytes < minimum_bytes:
        raise ValueError(f"Insufficient space at {path}: {free_bytes / 10 ** 9:.2f} GB ({free_bytes / 1024 ** 3:.2f} GiB) free; at least {minimum_bytes / 1024 ** 3:g} GiB required. Free disk space before restarting. No files were deleted.")


def validate_test_scheme(path):
    action = ET.parse(path).getroot().find('TestAction')
    if action is None or action.get('preferredScreenCaptureFormat') != 'screenshots':
        raise ValueError('UI test scheme must select screenshots, not the default video recorder.')
    # XcodeGen omits default-valued attributes. Automatic captures default on.
    if action.get('disableAutomaticScreenCaptures', 'NO') != 'NO':
        raise ValueError('UI test scheme must retain automatic failure screenshots.')
    targets = [reference for reference in action.findall('Testables/TestableReference')
               if reference.find('BuildableReference') is not None
               and reference.find('BuildableReference').get('BlueprintName') == 'OnionaryUITests']
    if len(targets) != 1 or targets[0].get('skipped') != 'NO':
        raise ValueError('UI test target must be present and enabled exactly once.')
    if any(list(selection) for name in ('SkippedTests', 'SelectedTests') for selection in action.iter(name)):
        raise ValueError('The scheme must not omit UI cases; profile selection belongs to test.sh.')
    print(f'Validated screenshot capture and complete UI target: {path}')


def validate_test_app(path):
    """Check the built output, not just the requested Xcode build setting."""
    with (path / 'Info.plist').open('rb') as source:
        executable = plistlib.load(source).get('CFBundleExecutable')
    if (not isinstance(executable, str) or not executable
            or executable in {'.', '..'} or Path(executable).name != executable):
        raise ValueError('UI app must name a valid bundle-local executable.')
    binary = path / executable
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise ValueError('UI app executable is missing or not executable.')
    with binary.open('rb') as source:
        header = source.read(16)
    # All supported test runners use thin, native arm64 simulator executables.
    if len(header) != 16 or struct.unpack('<IIII', header)[::3] != (0xFEEDFACF, 2):
        raise ValueError('UI app must contain a 64-bit Mach-O executable.')
    if list(path.glob('*.debug.dylib')) or (path / '__preview.dylib').exists():
        raise ValueError('Headless UI app must use the normal executable layout, without Preview dylibs.')
    print(f'Validated headless UI executable layout: {path}')


def select_test_plan(products):
    """Use the compiled plan directly, without reopening project/package state."""
    plans = sorted(products.glob('Onionary_iphonesimulator*-arm64.xctestrun'))
    if len(plans) != 1:
        raise ValueError('Expected exactly one compiled Onionary arm64 simulator test plan.')
    with plans[0].open('rb') as source:
        plan = plistlib.load(source)
    if plan.get('__xctestrun_metadata__', {}).get('FormatVersion') != 1:
        raise ValueError('Unsupported compiled test-plan format for the pinned Xcode.')
    targets = {name: target for name, target in plan.items() if not name.startswith('__')}
    if set(targets) != {'OnionaryUITests'}:
        raise ValueError('Compiled plan must contain the complete Onionary UI target exactly once.')
    target = targets['OnionaryUITests']
    if target.get('BlueprintName') != 'OnionaryUITests' or target.get('IsUITestBundle') is not True:
        raise ValueError('Compiled plan does not identify the Onionary UI bundle.')
    if target.get('PreferredScreenCaptureFormat') != 'screenshots':
        raise ValueError('Compiled plan must retain screenshot diagnostics.')
    if any(target.get(key) for key in ('SkipTestIdentifiers', 'OnlyTestIdentifiers')):
        raise ValueError('Compiled plan must not filter UI cases; select the full profile in test.sh.')
    paths = {
        'TestHostPath': '__TESTROOT__/Debug-iphonesimulator/OnionaryUITests-Runner.app',
        'TestBundlePath': '__TESTHOST__/PlugIns/OnionaryUITests.xctest',
        'UITargetAppPath': '__TESTROOT__/Debug-iphonesimulator/Onionary.app',
    }
    host = products / 'Debug-iphonesimulator/OnionaryUITests-Runner.app'
    for key, expected in paths.items():
        if target.get(key) != expected:
            raise ValueError(f'Compiled plan has an unexpected {key}.')
        path = expected.replace('__TESTROOT__', str(products)).replace('__TESTHOST__', str(host))
        if not Path(path).is_dir():
            raise ValueError(f'Compiled test product is missing: {path}')
    return plans[0].resolve()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xcode-only', action='store_true')
    parser.add_argument('--stage', choices=STAGE_GIB, default='release')
    parser.add_argument('--test-scheme', type=Path, help='Validate the generated UI scheme without starting Xcode')
    parser.add_argument('--test-app', type=Path, help='Validate the built headless UI app without booting a simulator')
    parser.add_argument('--test-products', type=Path, help='Print the validated compiled UI test-plan path')
    args = parser.parse_args()
    try:
        if args.test_scheme:
            validate_test_scheme(args.test_scheme)
            return
        if args.test_app:
            validate_test_app(args.test_app)
            return
        if args.test_products:
            print(select_test_plan(args.test_products))
            return
        validate_xcode(subprocess.check_output(['xcodebuild', '-version'], text=True))
        if not args.xcode_only:
            for path in (Path(__file__).resolve().parents[1], Path(tempfile.gettempdir())):
                validate_disk(path, shutil.disk_usage(path).free, STAGE_GIB[args.stage] * 1024 ** 3)
    except (ValueError, OSError, ET.ParseError, plistlib.InvalidFileException) as error:
        raise SystemExit(str(error)) from error


if __name__ == '__main__':
    main()
