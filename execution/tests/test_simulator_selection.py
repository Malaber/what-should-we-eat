"""Require the pinned build even when RC/stable share an OS identifier."""
import importlib.util
import json
from pathlib import Path
import plistlib
import sys
import pytest

spec = importlib.util.spec_from_file_location('simulator', Path(__file__).parents[2] / 'ios/Onionary/Scripts/resolve_simulator.py')
simulator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(simulator)
DUO = 'com.apple.CoreSimulator.SimDeviceType.iPhone-Duo'


def runtime(version, device=DUO, available=True, build=None):
    build = build or {'27.0': '24A434', '27.1': '24A94425', '27.2': '24B1'}[version]
    return {'identifier': simulator.runtime_identifier(version),
            'version': version, 'buildversion': build, 'isAvailable': available,
            'bundlePath': f'/Runtimes/{build}/iOS {version}.simruntime',
            'supportedDeviceTypes': [{'identifier': device}]}


def test_declared_duo_build_wins_over_rc_and_newer_installed_runtime():
    stable = runtime('27.1')
    runtimes = [runtime('27.2'), runtime('27.1', build='24A94232'), stable]
    for order in (runtimes, list(reversed(runtimes))):
        assert simulator.select_runtime(order, DUO) == stable['bundlePath']


@pytest.mark.parametrize('runtimes', [
    [runtime('27.2')],
    [runtime('27.1', available=False)],
    [runtime('27.1', device=simulator.DEFAULT_DEVICE)],
    [runtime('27.1', build='24A94232')],
    [runtime('27.1', available=False), runtime('27.1', build='24A94232')],
])
def test_missing_or_incompatible_pin_fails_without_fallback(runtimes):
    with pytest.raises(ValueError, match='no fallback'):
        simulator.select_runtime(runtimes, DUO)


@pytest.mark.parametrize('missing', ['buildversion', 'bundlePath'])
def test_incomplete_runtime_metadata_cannot_select_an_ambiguous_build(missing):
    installed = runtime('27.1')
    installed.pop(missing)
    with pytest.raises(ValueError, match='no fallback'):
        simulator.select_runtime([installed], DUO)


def test_unpinned_version_is_rejected():
    with pytest.raises(ValueError, match='No simulator build pin'):
        simulator.select_runtime([runtime('27.2')], DUO, '27.2')


def test_standard_phone_uses_270_even_when_newer_compatible_runtime_exists():
    pinned = runtime('27.0', simulator.DEFAULT_DEVICE)
    runtimes = [runtime('27.2', simulator.DEFAULT_DEVICE), pinned]
    assert simulator.select_runtime(runtimes) == pinned['bundlePath']


@pytest.mark.parametrize('create', [False, True])
def test_cli_creates_with_exact_bundle_path_but_lists_by_os_identifier(monkeypatch, tmp_path, capsys, create):
    pinned = runtime('27.1')
    pinned['bundlePath'] = str(tmp_path / 'iOS 27.1.simruntime')
    source = Path(pinned['bundlePath']) / 'Contents/Resources/RuntimeRoot/System/Library/CoreServices/SystemVersion.plist'
    source.parent.mkdir(parents=True)
    source.write_bytes(plistlib.dumps({'ProductVersion': '27.1', 'ProductBuildVersion': '24A94425'}))
    calls = []

    def output(command, **kwargs):
        calls.append(command)
        if command[2:4] == ['list', 'runtimes']:
            return json.dumps({'runtimes': [runtime('27.1', build='24A94232'), pinned]})
        if command[2] == 'create':
            return 'owned-device\n'
        return json.dumps({'devices': {pinned['identifier']: [
            {'udid': 'existing-device', 'deviceTypeIdentifier': DUO}]}})

    monkeypatch.setattr(simulator.subprocess, 'check_output', output)
    monkeypatch.setattr(sys, 'argv', ['resolve_simulator.py', '--device-type', DUO] + (['--create'] if create else []))
    simulator.main()
    output = capsys.readouterr()
    assert output.out.strip() == ('owned-device' if create else 'existing-device')
    assert 'iOS 27.1 (24A94425)' in output.err
    if create:
        assert calls[-1] == ['xcrun', 'simctl', 'create', 'Onionary Isolated Tests', DUO, pinned['bundlePath']]
    else:
        assert calls[-1] == ['xcrun', 'simctl', 'list', 'devices', 'available', '--json']


def test_wrong_bundle_metadata_stops_before_device_creation(monkeypatch, tmp_path):
    pinned = runtime('27.1')
    pinned['bundlePath'] = str(tmp_path)
    source = tmp_path / 'Contents/Resources/RuntimeRoot/System/Library/CoreServices/SystemVersion.plist'
    source.parent.mkdir(parents=True)
    source.write_bytes(plistlib.dumps({'ProductVersion': '27.1', 'ProductBuildVersion': '24A94232'}))
    calls = []
    monkeypatch.setattr(simulator.subprocess, 'check_output', lambda command, **kwargs:
                        calls.append(command) or json.dumps({'runtimes': [pinned]}))
    monkeypatch.setattr(sys, 'argv', ['resolve_simulator.py', '--create', '--device-type', DUO])
    with pytest.raises(RuntimeError, match='Simulator was not created'):
        simulator.main()
    assert calls == [['xcrun', 'simctl', 'list', 'runtimes', '--json']]
