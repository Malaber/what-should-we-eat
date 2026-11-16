"""Require the pinned build even when RC/stable share an OS identifier."""
import importlib.util
import json
from pathlib import Path
import plistlib
import sys
import pytest

from execution.ios_runtime import runtime_identifier

spec = importlib.util.spec_from_file_location('simulator', Path(__file__).parents[2] / 'ios/Onionary/Scripts/resolve_simulator.py')
simulator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(simulator)
DUO = 'com.apple.CoreSimulator.SimDeviceType.iPhone-Duo'


def runtime(version, device=DUO, available=True, build=None):
    build = build or ('24B91016s' if device == DUO else '24B8117')
    return {'identifier': runtime_identifier(version),
            'version': version, 'buildversion': build, 'isAvailable': available,
            'bundlePath': f'/Runtimes/{build}/iOS {version}.simruntime',
            'supportedDeviceTypes': [{'identifier': device}]}


def test_declared_duo_build_wins_over_rc_and_standard_runtime():
    stable = runtime('27.2')
    runtimes = [runtime('27.2', build='24B8117'), runtime('27.2', build='24B91014'), stable]
    for order in (runtimes, list(reversed(runtimes))):
        assert simulator.select_runtime(order, DUO) == stable


def test_device_specific_duo_registration_wins_over_generic_alias():
    alias = runtime('27.2')
    dedicated = {**alias, 'identifier': alias['identifier'] + '-iPhone19-4'}
    assert simulator.select_runtime([alias, dedicated], DUO) == dedicated


@pytest.mark.parametrize('runtimes', [
    [runtime('27.2', build='24B8117')],
    [{**runtime('27.2'), 'identifier': runtime_identifier('27.2') + '-iPhone20-1'}],
    [runtime('27.2', available=False)],
    [runtime('27.2', device=simulator.DEFAULT_DEVICE)],
    [runtime('27.2', build='24B91014')],
    [runtime('27.2', available=False), runtime('27.2', build='24B91014')],
])
def test_missing_or_incompatible_pin_fails_without_fallback(runtimes):
    with pytest.raises(ValueError, match='no fallback'):
        simulator.select_runtime(runtimes, DUO)


@pytest.mark.parametrize('missing', ['buildversion', 'bundlePath'])
def test_incomplete_runtime_metadata_cannot_select_an_ambiguous_build(missing):
    installed = runtime('27.2')
    installed.pop(missing)
    with pytest.raises(ValueError, match='no fallback'):
        simulator.select_runtime([installed], DUO)


def test_unpinned_version_is_rejected():
    with pytest.raises(ValueError, match='No simulator build pin'):
        simulator.select_runtime([runtime('27.2', build='24B8117')], DUO, '27.3')


@pytest.mark.parametrize('model', ['iPhone-17-Pro', 'iPad-Pro-13-inch-M5-12GB'])
def test_hosted_ordinary_devices_select_stable_272(model):
    device = f'com.apple.CoreSimulator.SimDeviceType.{model}'
    pinned = runtime('27.2', device, build='24B8117')
    other = [runtime('27.0', device), runtime('27.2', device, build='24B114'),
             runtime('27.2', build='24B91016s')]
    assert simulator.select_runtime(other + [pinned], device) == pinned
    with pytest.raises(ValueError, match='24B8117'):
        simulator.select_runtime(other, device, '27.2')


@pytest.mark.parametrize('create', [False, True])
@pytest.mark.parametrize('scoped', [False, True])
def test_cli_creates_with_exact_bundle_path_but_lists_by_os_identifier(monkeypatch, tmp_path, capsys, create, scoped):
    pinned = runtime('27.2')
    pinned['identifier'] += '-iPhone19-4'
    pinned['bundlePath'] = str(tmp_path / 'iOS 27.2.simruntime')
    source = Path(pinned['bundlePath']) / 'Contents/Resources/RuntimeRoot/System/Library/CoreServices/SystemVersion.plist'
    source.parent.mkdir(parents=True)
    source.write_bytes(plistlib.dumps({'ProductVersion': '27.2', 'ProductBuildVersion': '24B91016s'}))
    calls = []
    device_set = ['--device-set', str(tmp_path / 'devices')] if scoped else []
    prefix = ['xcrun', 'simctl', '--set', device_set[1]] if scoped else ['xcrun', 'simctl']

    def output(command, **kwargs):
        calls.append(command)
        assert command[:len(prefix)] == prefix
        action = command[len(prefix):]
        if action[:2] == ['list', 'runtimes']:
            return json.dumps({'runtimes': [runtime('27.2', build='24B91014'), pinned]})
        if action[0] == 'create':
            return 'owned-device\n'
        return json.dumps({'devices': {pinned['identifier']: [
            {'udid': 'existing-device', 'deviceTypeIdentifier': DUO}]}})

    monkeypatch.setattr(simulator.subprocess, 'check_output', output)
    monkeypatch.setattr(sys, 'argv', ['resolve_simulator.py', '--device-type', DUO, *device_set]
                        + (['--create'] if create else []))
    simulator.main()
    output = capsys.readouterr()
    assert output.out.strip() == ('owned-device' if create else 'existing-device')
    assert 'iOS 27.2 (24B91016s)' in output.err
    if create:
        assert calls[-1] == [*prefix, 'create', 'Onionary Isolated Tests', DUO, pinned['bundlePath']]
    else:
        assert calls[-1] == [*prefix, 'list', 'devices', 'available', '--json']


def test_wrong_bundle_metadata_stops_before_device_creation(monkeypatch, tmp_path):
    pinned = runtime('27.2')
    pinned['bundlePath'] = str(tmp_path)
    source = tmp_path / 'Contents/Resources/RuntimeRoot/System/Library/CoreServices/SystemVersion.plist'
    source.parent.mkdir(parents=True)
    source.write_bytes(plistlib.dumps({'ProductVersion': '27.2', 'ProductBuildVersion': '24B91014'}))
    calls = []
    monkeypatch.setattr(simulator.subprocess, 'check_output', lambda command, **kwargs:
                        calls.append(command) or json.dumps({'runtimes': [pinned]}))
    monkeypatch.setattr(sys, 'argv', ['resolve_simulator.py', '--create', '--device-type', DUO])
    with pytest.raises(RuntimeError, match='Simulator was not created'):
        simulator.main()
    assert calls == [['xcrun', 'simctl', 'list', 'runtimes', '--json']]
