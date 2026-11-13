"""No Xcode changes/downloads: exercise exact runtime selection and guest checks."""
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


@pytest.mark.parametrize('build,available,expected', [
    ('24A94425', True, True), ('24A94232', True, False), ('24A94425', False, False),
])
def test_installer_uses_shared_exact_stable_pin(monkeypatch, build, available, expected):
    installed = {'identifier': ios_runtime.runtime_identifier('27.1'),
                 'buildversion': build, 'isAvailable': available}
    monkeypatch.setattr(installer.subprocess, 'run', lambda *a, **k:
                        subprocess.CompletedProcess(a, 0, stdout=json.dumps({'runtimes': [installed]})))
    assert installer.RUNTIMES is ios_runtime.RUNTIME_BUILDS
    assert installer.available('27.1') is expected


@pytest.mark.parametrize('installed_after_download', [False, True])
def test_download_exit_cannot_override_exact_availability(monkeypatch, installed_after_download):
    availability = iter([False, installed_after_download])
    monkeypatch.setattr(installer, 'available', lambda version: next(availability))
    calls = []
    monkeypatch.setattr(installer.subprocess, 'run', lambda command, **kwargs:
                        calls.append(command) or subprocess.CompletedProcess(command, 70))
    mapped = []
    monkeypatch.setattr(installer, 'configure_sdk_runtime', mapped.append)
    if installed_after_download:
        installer.ensure('27.1')
        assert mapped == ['27.1']
    else:
        with pytest.raises(RuntimeError, match=r'24A94425.*exit 70'):
            installer.ensure('27.1')
        assert not mapped
    assert calls == [['xcodebuild', '-downloadPlatform', 'iOS', '-buildVersion',
                      '24A94425', '-architectureVariant', 'arm64']]


def sdk_commands(monkeypatch, chosen_builds):
    chosen = iter(chosen_builds)
    reads, writes = [], []

    def read(*command):
        reads.append(command)
        if command[-1] == '--show-sdk-version':
            return '27.1'
        if command[-1] == '--show-sdk-build-version':
            return '24A94232'
        assert command == ('xcrun', 'simctl', 'runtime', 'match', 'list', '-j')
        return json.dumps({'iphoneos27.1': {'chosenRuntimeBuild': next(chosen)}})

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
    _, writes = sdk_commands(monkeypatch, ['24A94232'])
    with pytest.raises(RuntimeError, match='No local preferences changed') as error:
        ios_runtime.configure_sdk_runtime('27.1', environment)
    assert 'match set iphoneos27.1 24A94425 --sdkBuild 24A94232' in str(error.value)
    assert not writes


def test_matching_sdk_needs_no_preference_change(monkeypatch):
    _, writes = sdk_commands(monkeypatch, ['24A94425'])
    ios_runtime.configure_sdk_runtime('27.1', {})
    assert not writes


def test_older_os_runtime_does_not_change_newer_sdk_mapping(monkeypatch):
    reads, writes = sdk_commands(monkeypatch, [])
    ios_runtime.configure_sdk_runtime('27.0', {})
    assert reads == [('xcrun', '--sdk', 'iphonesimulator', '--show-sdk-version')]
    assert not writes


@pytest.mark.parametrize('after', ['24A94425', '24A94232'])
def test_only_disposable_github_runner_can_map_sdk_and_must_verify_result(monkeypatch, after):
    _, writes = sdk_commands(monkeypatch, ['24A94232', after])
    environment = {'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'github-hosted'}
    if after == '24A94425':
        ios_runtime.configure_sdk_runtime('27.1', environment)
    else:
        with pytest.raises(RuntimeError, match='did not select pinned runtime'):
            ios_runtime.configure_sdk_runtime('27.1', environment)
    assert writes == [['xcrun', 'simctl', 'runtime', 'match', 'set',
                       'iphoneos27.1', '24A94425', '--sdkBuild', '24A94232']]


@pytest.mark.parametrize('version,build', [('27.1', '24A94425'), ('27.1', '24A94232'), ('27.0', '24A434')])
def test_running_guest_build_must_match_pin(monkeypatch, tmp_path, capsys, version, build):
    source = tmp_path / 'System/Library/CoreServices/SystemVersion.plist'
    source.parent.mkdir(parents=True)
    source.write_bytes(plistlib.dumps({'ProductVersion': version, 'ProductBuildVersion': build}))
    calls = []
    monkeypatch.setattr(ios_runtime, 'read_command', lambda *args: calls.append(args) or str(tmp_path))
    if build == '24A94425':
        ios_runtime.verify_booted('owned-device', '27.1')
        assert 'Verified booted iOS 27.1 (24A94425)' in capsys.readouterr().out
    else:
        with pytest.raises(RuntimeError, match='XCTest was not started'):
            ios_runtime.verify_booted('owned-device', '27.1')
    assert calls == [('xcrun', 'simctl', 'getenv', 'owned-device', 'SIMULATOR_ROOT')]


@pytest.mark.parametrize('root', ['', 'relative/path'])
def test_invalid_guest_metadata_cannot_be_accepted(monkeypatch, root):
    monkeypatch.setattr(ios_runtime, 'read_command', lambda *args: root)
    with pytest.raises(RuntimeError, match='no absolute runtime root'):
        ios_runtime.verify_booted('owned-device', '27.1')


def test_runtime_reads_have_deadline(monkeypatch):
    def output(command, **kwargs):
        assert command == ['xcrun', 'simctl', 'runtime', 'match', 'list', '-j']
        assert kwargs == {'text': True, 'timeout': 15}
        return '{}\n'

    monkeypatch.setattr(ios_runtime.subprocess, 'check_output', output)
    assert ios_runtime.read_command('xcrun', 'simctl', 'runtime', 'match', 'list', '-j') == '{}'
