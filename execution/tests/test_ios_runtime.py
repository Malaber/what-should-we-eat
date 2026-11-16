"""No Xcode changes/downloads: exercise exact runtime selection and bundle checks."""
import importlib.util
import json
from pathlib import Path
import plistlib
import subprocess

import pytest

from execution import ios_runtime

spec = importlib.util.spec_from_file_location('installer', Path(__file__).parents[2] / 'ios/Onionary/Scripts/ensure_ios_runtimes.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


@pytest.mark.parametrize('build,device,available,expected', [
    ('24B8117', ios_runtime.DEFAULT_DEVICE, True, True),
    ('24B91016s', ios_runtime.DUO_DEVICE, True, True),
    ('24B8117', ios_runtime.DUO_DEVICE, True, False),
    ('24B91016s', ios_runtime.DEFAULT_DEVICE, True, False),
    ('24B91014', ios_runtime.DUO_DEVICE, True, False),
    ('24B91016s', ios_runtime.DUO_DEVICE, False, False),
])
def test_installer_checks_device_and_exact_stable_pin(monkeypatch, build, device, available, expected):
    installed = {'identifier': ios_runtime.runtime_identifier('27.2'), 'version': '27.2',
                 'buildversion': build, 'isAvailable': available,
                 'bundlePath': '/runtimes/installed.simruntime',
                 'supportedDeviceTypes': [{'identifier': device}]}
    monkeypatch.setattr(installer, 'read_command', lambda *a: json.dumps({'runtimes': [installed]}))
    assert installer.available('27.2', device) == (installed['bundlePath'] if expected else None)


@pytest.mark.parametrize('installed_after_download', [False, True])
def test_download_exit_cannot_override_exact_availability(monkeypatch, installed_after_download):
    version, device = '27.2', ios_runtime.DUO_DEVICE
    bundle = '/runtimes/duo.simruntime'
    availability = iter([None, bundle if installed_after_download else None])
    monkeypatch.setattr(installer, 'available', lambda *a: next(availability))
    calls, stages = [], []
    monkeypatch.setattr(installer.subprocess, 'run', lambda command, **kwargs:
                        calls.append(command) or subprocess.CompletedProcess(command, 70))
    monkeypatch.setattr(installer, 'verify_runtime_bundle', lambda *a: stages.append(('verify', a)))
    monkeypatch.setattr(installer, 'configure_sdk_runtime', lambda *a: stages.append(('map', a)))
    monkeypatch.setattr(installer, 'prepare_runtime_cache', lambda *a: stages.append(('cache', a)))
    if installed_after_download:
        installer.ensure(version, device)
        assert stages == [('verify', (bundle, version, device)), ('map', (version, device)),
                          ('cache', (version, device))]
    else:
        with pytest.raises(RuntimeError, match=r'24B91016s.*exit 70'):
            installer.ensure(version, device)
        assert not stages
    assert calls == [['xcodebuild', '-downloadPlatform', 'iOS', '-buildVersion',
                      '24B91016s', '-architectureVariant', 'arm64']]


def sdk_commands(monkeypatch, chosen_builds):
    chosen = iter(chosen_builds)
    reads, writes = [], []

    def read(*command):
        reads.append(command)
        if command[-1] == '--show-sdk-version':
            return '27.2'
        if command[-1] == '--show-sdk-build-version':
            return '24B8117'
        assert command == ('xcrun', 'simctl', 'runtime', 'match', 'list', '-j')
        return json.dumps({'iphoneos27.2': {'chosenRuntimeBuild': next(chosen)}})

    monkeypatch.setattr(ios_runtime, 'read_command', read)

    def write(command, **kwargs):
        assert kwargs == {'check': True, 'timeout': 15}
        writes.append(command)

    monkeypatch.setattr(ios_runtime.subprocess, 'run', write)
    return reads, writes


@pytest.mark.parametrize('environment', [
    {}, {'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'self-hosted'},
    {'GITHUB_ACTIONS': 'false', 'RUNNER_ENVIRONMENT': 'github-hosted'},
])
def test_sdk_preferences_are_never_changed_on_developer_or_self_hosted_machines(monkeypatch, environment):
    _, writes = sdk_commands(monkeypatch, ['24B8117'])
    with pytest.raises(RuntimeError, match='No local preferences changed') as error:
        ios_runtime.configure_sdk_runtime('27.2', ios_runtime.DUO_DEVICE, environ=environment)
    assert 'match set iphoneos27.2 24B91016s --sdkBuild 24B8117' in str(error.value)
    assert not writes


def test_matching_sdk_needs_no_preference_change(monkeypatch):
    _, writes = sdk_commands(monkeypatch, ['24B91016s'])
    ios_runtime.configure_sdk_runtime('27.2', ios_runtime.DUO_DEVICE, environ={})
    assert not writes


def test_previous_os_runtime_is_rejected_before_mapping(monkeypatch):
    reads, writes = sdk_commands(monkeypatch, [])
    with pytest.raises(ValueError, match='Use iOS 27.2'):
        ios_runtime.configure_sdk_runtime('27.0')
    assert not reads
    assert not writes


@pytest.mark.parametrize('after', ['24B91016s', '24B8117'])
def test_only_disposable_github_runner_can_map_sdk_and_must_verify_result(monkeypatch, after):
    _, writes = sdk_commands(monkeypatch, ['24B8117', after])
    environment = {'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'github-hosted'}
    if after == '24B91016s':
        ios_runtime.configure_sdk_runtime('27.2', ios_runtime.DUO_DEVICE, environ=environment)
    else:
        with pytest.raises(RuntimeError, match='did not select pinned runtime'):
            ios_runtime.configure_sdk_runtime('27.2', ios_runtime.DUO_DEVICE, environ=environment)
    assert writes == [['xcrun', 'simctl', 'runtime', 'match', 'set',
                       'iphoneos27.2', '24B91016s', '--sdkBuild', '24B8117']]


@pytest.mark.parametrize('version,build', [('27.2', '24B91016s'), ('27.2', '24B8117'), ('27.0', '24A434')])
def test_installed_bundle_metadata_must_match_pin_without_guest_rpc(monkeypatch, tmp_path, version, build):
    source = tmp_path / 'Contents/Resources/RuntimeRoot/System/Library/CoreServices/SystemVersion.plist'
    source.parent.mkdir(parents=True)
    source.write_bytes(plistlib.dumps({'ProductVersion': version, 'ProductBuildVersion': build}))
    def forbidden(*args, **kwargs):
        pytest.fail('Bundle verification must not start a host/guest command')

    monkeypatch.setattr(ios_runtime.subprocess, 'check_output', forbidden)
    monkeypatch.setattr(ios_runtime.subprocess, 'run', forbidden)
    if build == '24B91016s':
        ios_runtime.verify_runtime_bundle(tmp_path, '27.2', ios_runtime.DUO_DEVICE)
    else:
        with pytest.raises(RuntimeError, match='Simulator was not created'):
            ios_runtime.verify_runtime_bundle(tmp_path, '27.2', ios_runtime.DUO_DEVICE)


@pytest.mark.parametrize('root', ['', 'relative/path'])
def test_relative_bundle_path_cannot_be_accepted(root):
    with pytest.raises(ValueError, match='absolute path'):
        ios_runtime.verify_runtime_bundle(root, '27.2')


@pytest.mark.parametrize('metadata', [None, b'invalid plist', plistlib.dumps({})])
def test_missing_or_invalid_system_metadata_cannot_be_accepted(tmp_path, metadata):
    if metadata is not None:
        source = tmp_path / 'Contents/Resources/RuntimeRoot/System/Library/CoreServices/SystemVersion.plist'
        source.parent.mkdir(parents=True)
        source.write_bytes(metadata)
    with pytest.raises((FileNotFoundError, plistlib.InvalidFileException, RuntimeError)):
        ios_runtime.verify_runtime_bundle(tmp_path, '27.2', ios_runtime.DUO_DEVICE)


def test_runtime_reads_have_deadline(monkeypatch):
    def output(command, **kwargs):
        assert command == ['xcrun', 'simctl', 'runtime', 'match', 'list', '-j']
        assert kwargs == {'text': True, 'timeout': 15}
        return '{}\n'

    monkeypatch.setattr(ios_runtime.subprocess, 'check_output', output)
    assert ios_runtime.read_command('xcrun', 'simctl', 'runtime', 'match', 'list', '-j') == '{}'


HOSTED_MAC = {'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'github-hosted', 'RUNNER_OS': 'macOS'}


@pytest.mark.parametrize('environment', [
    {}, {**HOSTED_MAC, 'RUNNER_ENVIRONMENT': 'self-hosted'},
    {**HOSTED_MAC, 'GITHUB_ACTIONS': 'false'}, {**HOSTED_MAC, 'RUNNER_OS': 'Linux'},
])
def test_runtime_cache_does_not_touch_developer_self_hosted_or_linux_machines(monkeypatch, environment):
    def forbidden(*args, **kwargs):
        pytest.fail('Cache preparation must not inspect or change this machine')
    monkeypatch.setattr(ios_runtime, 'read_command', forbidden)
    monkeypatch.setattr(ios_runtime.subprocess, 'run', forbidden)
    ios_runtime.prepare_runtime_cache('27.2', ios_runtime.DUO_DEVICE, environ=environment)


@pytest.mark.parametrize('failure', [None, 'exit', 'timeout'])
def test_runtime_cache_prepares_only_validated_stable_bundle_once(monkeypatch, failure):
    runtimes = [dict(identifier=ios_runtime.runtime_identifier('27.2'), version='27.2',
                     buildversion=build, isAvailable=True, bundlePath=path,
                     supportedDeviceTypes=[{'identifier': ios_runtime.DUO_DEVICE}])
                for build, path in [('24B8117', '/runtimes/standard.simruntime'),
                                    ('24B91016s', '/runtimes/stable.simruntime')]]
    monkeypatch.setattr(ios_runtime, 'read_command', lambda *args: json.dumps({'runtimes': runtimes}))
    verified, calls = [], []
    monkeypatch.setattr(ios_runtime, 'verify_runtime_bundle', lambda *args: verified.append(args))
    def run(command, **kwargs):
        assert verified == [('/runtimes/stable.simruntime', '27.2', ios_runtime.DUO_DEVICE)]
        calls.append((command, kwargs))
        if failure == 'exit': raise subprocess.CalledProcessError(2, command)
        if failure == 'timeout': raise subprocess.TimeoutExpired(command, 600)
    monkeypatch.setattr(ios_runtime.subprocess, 'run', run)
    if failure:
        with pytest.raises(subprocess.SubprocessError):
            ios_runtime.prepare_runtime_cache('27.2', ios_runtime.DUO_DEVICE, environ=HOSTED_MAC)
    else:
        ios_runtime.prepare_runtime_cache('27.2', ios_runtime.DUO_DEVICE, environ=HOSTED_MAC)
    assert calls == [(['xcrun', 'simctl', 'runtime', 'dyld_shared_cache', 'update',
                       '/runtimes/stable.simruntime'], {'check': True, 'timeout': 600})]


@pytest.mark.parametrize('change', ['rc', 'unavailable', 'relative-path', 'wrong-version', 'invalid-metadata'])
def test_runtime_cache_never_falls_back_or_prepares_invalid_bundle(monkeypatch, change):
    runtime = dict(identifier=ios_runtime.runtime_identifier('27.2'), version='27.2',
                   buildversion='24B91016s', isAvailable=True, bundlePath='/runtimes/stable.simruntime',
                   supportedDeviceTypes=[{'identifier': ios_runtime.DUO_DEVICE}])
    if change == 'rc': runtime['buildversion'] = '24B91014'
    elif change == 'unavailable': runtime['isAvailable'] = False
    elif change == 'relative-path': runtime['bundlePath'] = 'relative.simruntime'
    elif change == 'wrong-version': runtime['version'] = '27.0'
    monkeypatch.setattr(ios_runtime, 'read_command', lambda *args: json.dumps({'runtimes': [runtime]}))
    def invalid(*args): raise RuntimeError('invalid metadata')
    monkeypatch.setattr(ios_runtime, 'verify_runtime_bundle', invalid)
    def forbidden(*args, **kwargs): pytest.fail('An invalid runtime must not be prepared')
    monkeypatch.setattr(ios_runtime.subprocess, 'run', forbidden)
    with pytest.raises(RuntimeError): ios_runtime.prepare_runtime_cache('27.2', ios_runtime.DUO_DEVICE, environ=HOSTED_MAC)
