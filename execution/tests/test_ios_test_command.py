"""Exercise the shell entry point with fake tool executables, never a simulator."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

IOS = Path(__file__).parents[2] / 'ios/Onionary'
SCRIPT = IOS / 'Scripts/test.sh'


@pytest.mark.parametrize('device,allowance,suite', [
    ('iPhone-17-Pro', '180', 'OnionaryUITests'),
    ('iPad-Pro-13-inch-M5-16GB', '180', 'OnionaryUITests'),
    ('iPhone-Duo', '360', 'OnionaryDuoTests'),
])
@pytest.mark.parametrize('fail_test', [False, True])
@pytest.mark.parametrize('mode', ['all', '--build-only', '--test-only'])
def test_supplied_device_is_never_booted_or_deleted(tmp_path, device, allowance, suite, fail_test, mode):
    bins = tmp_path / 'bin'; bins.mkdir()
    for command in ('swift', 'xcodegen'):
        path = bins / command; path.write_text('#!/bin/sh\nexit 0\n'); path.chmod(0o755)
    python = bins / 'python3'
    python.write_text('''#!/usr/bin/env python3_REAL
import json, os, sys
if sys.argv[1].endswith('version.py'):
    print('0.6.0')
elif '--test-products' in sys.argv:
    print(sys.argv[-1] + '/Onionary_iphonesimulator27.1-arm64.xctestrun')
elif 'xcodebuild' in sys.argv:
    with open(os.environ['CAPTURE_ARGS'], 'a') as f:
        f.write(json.dumps(sys.argv[sys.argv.index('xcodebuild')+1:]) + '\\n')
    if 'test-without-building' in sys.argv and os.environ['FAIL_TEST'] == '1': sys.exit(44)
elif any(arg.endswith('ios_runtime.py') for arg in sys.argv):
    sys.exit(95)  # No post-boot runtime command, including through run_bounded.
'''.replace('/usr/bin/env python3_REAL', __import__('sys').executable))
    python.chmod(0o755)
    capture = tmp_path / 'args.jsonl'
    xcrun = bins / 'xcrun'
    xcrun.write_text('#!/bin/sh\nprintf called > "$FORBIDDEN_GUEST_COMMAND"\nexit 95\n')
    xcrun.chmod(0o755)
    forbidden = tmp_path / 'guest-command'
    arguments = ['bash', str(SCRIPT)] + ([] if mode == 'all' else [mode])
    result = subprocess.run(arguments, env={**os.environ,
        'PATH': str(bins) + os.pathsep + os.environ['PATH'], 'CAPTURE_ARGS': str(capture),
        'FAIL_TEST': str(int(fail_test)), 'FORBIDDEN_GUEST_COMMAND': str(forbidden),
        'SIMULATOR_ID': 'test-only', 'SIMULATOR_DEVICE_TYPE': device,
        'SIMULATOR_TEST_SHARD': '1' if mode == 'all' else 'all',
        'TEST_RESULTS_DIR': str(tmp_path / 'results'), 'TEST_DERIVED_DATA_DIR': str(tmp_path / 'shared-build')})
    assert result.returncode == (44 if fail_test and mode != '--build-only' else 0)
    assert not forbidden.exists()
    commands = [json.loads(line) for line in capture.read_text().splitlines()]
    assert len(commands) == (2 if mode == 'all' else 1)
    if mode != '--test-only':
        build = commands[0]
        assert build[build.index('-derivedDataPath') + 1] == str(tmp_path / 'shared-build')
        assert 'build-for-testing' in build
        assert build.count('ENABLE_DEBUG_DYLIB=NO') == 1
        assert 'ARCHS=arm64' in build
    if mode == '--build-only':
        assert build[build.index('-destination') + 1] == 'generic/platform=iOS Simulator'
        return
    test = commands[-1]
    assert test[test.index('-xctestrun') + 1] == str(tmp_path / 'shared-build/Build/Products/Onionary_iphonesimulator27.1-arm64.xctestrun')
    assert not any(option in test for option in ('-derivedDataPath', '-project', '-scheme'))
    assert 'test-without-building' in test
    assert not any(option.startswith('ENABLE_DEBUG_DYLIB=') for option in test)
    for option in ('-default-test-execution-time-allowance', '-maximum-test-execution-time-allowance'):
        assert test.count(option) == 1
        assert test[test.index(option) + 1] == allowance
    assert f'-only-testing:OnionaryUITests/{suite}' in test
    assert '-retry-tests-on-failure' not in test
    assert test[test.index('-collect-test-diagnostics') + 1] == 'never'
    assert '-resultBundlePath' in test


@pytest.mark.parametrize('device', ['iPhone-17-Pro', 'iPad-Pro-13-inch-M5-12GB'])
def test_ui_shards_run_every_case_once(tmp_path, device):
    bins = tmp_path / 'bin'
    bins.mkdir()
    capture = tmp_path / 'args.jsonl'
    python = bins / 'python3'
    python.write_text(f'''#!{sys.executable}
import json, os, sys
if '--test-products' in sys.argv:
    print(sys.argv[-1] + '/Onionary_iphonesimulator27.1-arm64.xctestrun')
if 'xcodebuild' in sys.argv:
    with open(os.environ['CAPTURE_ARGS'], 'a') as output:
        output.write(json.dumps(sys.argv) + '\\n')
''')
    python.chmod(0o755)
    env = {**os.environ, 'PATH': str(bins) + os.pathsep + os.environ['PATH'],
           'CAPTURE_ARGS': str(capture), 'SIMULATOR_ID': 'test-only',
           'SIMULATOR_DEVICE_TYPE': device, 'TEST_RESULTS_DIR': str(tmp_path / 'results')}
    for shard in ('1', '2', '3'):
        subprocess.run(['bash', str(SCRIPT), '--test-only'],
                       env={**env, 'SIMULATOR_TEST_SHARD': shard}, check=True)

    prefix = '-only-testing:OnionaryUITests/OnionaryUITests/'
    runs = [json.loads(line) for line in capture.read_text().splitlines()]
    portions = [[arg.removeprefix(prefix) for arg in run if arg.startswith(prefix)] for run in runs]
    assert len(portions) == 3
    assert 'testMarketingScreenshots' in portions[0]
    assert max(map(len, portions)) - min(map(len, portions)) <= 1
    source = (IOS / 'UITests/OnionaryUITests.swift').read_text()
    expected = re.findall(r'\bfunc\s+(test\w+)\s*\(', source)
    assert sorted(name for portion in portions for name in portion) == sorted(expected)
    for run in runs:
        assert 'test-without-building' in run
        assert run[run.index('-maximum-test-execution-time-allowance') + 1] == '180'


@pytest.mark.parametrize('failure_stage', ['none', 'build', 'app', 'plan', 'boot', 'test'])
@pytest.mark.parametrize('runtime_override', [None, '27.1'])
@pytest.mark.parametrize('diagnostics_fail', [False, True])
def test_compile_precedes_boot_and_declared_runtime_reaches_selector(tmp_path, failure_stage, runtime_override, diagnostics_fail):
    bins = tmp_path / 'bin'; bins.mkdir()
    capture = tmp_path / 'commands.jsonl'
    shim = '''#!PYTHON
import json, os, sys
with open(os.environ['CAPTURE_ARGS'], 'a') as output:
    output.write(json.dumps([os.path.basename(sys.argv[0]), *sys.argv[1:]]) + '\\n')
if any(arg.endswith('version.py') for arg in sys.argv): print('0.6.0')
if '--test-products' in sys.argv: print(sys.argv[-1] + '/Onionary_iphonesimulator27.1-arm64.xctestrun')
if '--test-products' in sys.argv and os.environ['FAIL_STAGE'] == 'plan': sys.exit(45)
if any(arg.endswith('resolve_simulator.py') for arg in sys.argv):
    with open(os.environ['CAPTURE_ARGS']) as source:
        device = sum('resolve_simulator.py' in line for line in source)
    print(f'isolated-test-device-{device}')
if 'build-for-testing' in sys.argv and os.environ['FAIL_STAGE'] == 'build': sys.exit(42)
if '--test-app' in sys.argv and os.environ['FAIL_STAGE'] == 'app': sys.exit(41)
if 'bootstatus' in sys.argv and os.environ['FAIL_STAGE'] == 'boot': sys.exit(43)
if 'getenv' in sys.argv or 'spawn' in sys.argv or any(arg.endswith('ios_runtime.py') for arg in sys.argv): sys.exit(95)
if 'test-without-building' in sys.argv and os.environ['FAIL_STAGE'] == 'test': sys.exit(44)
if any(arg.endswith('collect_ios_test_diagnostics.py') for arg in sys.argv) and os.environ['FAIL_DIAGNOSTICS'] == '1': sys.exit(99)
'''.replace('PYTHON', __import__('sys').executable)
    for name in ('python3', 'swift', 'xcodegen', 'xcrun'):
        path = bins / name; path.write_text(shim); path.chmod(0o755)
    env = {**os.environ, 'PATH': str(bins) + os.pathsep + os.environ['PATH'],
           'CAPTURE_ARGS': str(capture), 'FAIL_STAGE': failure_stage, 'FAIL_DIAGNOSTICS': str(int(diagnostics_fail)),
           'SIMULATOR_DEVICE_TYPE': 'com.apple.CoreSimulator.SimDeviceType.iPhone-Duo',
           'TEST_RESULTS_DIR': str(tmp_path / 'results')}
    env.pop('SIMULATOR_RUNTIME', None)
    if runtime_override is not None:
        env['SIMULATOR_RUNTIME'] = runtime_override
    env.pop('SIMULATOR_ID', None)
    result = subprocess.run(['bash', str(SCRIPT)], env=env)
    commands = [json.loads(line) for line in capture.read_text().splitlines()]
    resolve = next(c for c in commands if any(a.endswith('resolve_simulator.py') for a in c))
    assert resolve[resolve.index('--runtime') + 1] == (runtime_override or '')
    build = next(i for i, c in enumerate(commands) if 'build-for-testing' in c)
    assert result.returncode == {'none': 0, 'build': 42, 'app': 41, 'plan': 45, 'boot': 43, 'test': 44}[failure_stage]
    assert not any('boot' in c for c in commands)
    assert not any('getenv' in c or 'spawn' in c or any(a.endswith('ios_runtime.py') for a in c) for c in commands)
    if failure_stage in {'build', 'app', 'plan'}:
        assert not any('boot' in c or 'test-without-building' in c for c in commands)
    elif failure_stage == 'boot':
        assert any('bootstatus' in c for c in commands)
        assert not any('test-without-building' in c for c in commands)
    else:
        ready = next(i for i, c in enumerate(commands) if 'bootstatus' in c)
        test = next(i for i, c in enumerate(commands) if 'test-without-building' in c)
        assert build < ready < test
        assert not any(any('run_duo_tests.py' in a or '--prepare' == a for a in c) for c in commands)
    if failure_stage != 'build':
        layout = next(i for i, c in enumerate(commands) if '--test-app' in c)
        assert build < layout
        assert commands[layout][-1] == str(tmp_path / 'results/DerivedData/Build/Products/Debug-iphonesimulator/Onionary.app')
        if failure_stage not in {'app', 'plan'}:
            assert layout < next(i for i, c in enumerate(commands) if 'bootstatus' in c)
    if failure_stage in {'none', 'test'}:
        execution = next(c for c in commands if 'test-without-building' in c)
        assert execution[execution.index('--startup-seconds') + 1] == '600'
        assert execution[execution.index('--ready-prefix') + 1] == "Test Suite 'Selected tests' started at "
        assert execution[execution.index('xcodebuild') - 1] == '1800'
    instances = [c[-1] for c in commands if c[:3] == ['xcrun', 'simctl', 'delete']]
    assert instances == [f'isolated-test-device-{index}' for index in range(1, len(instances) + 1)]
    if failure_stage == 'none':
        source = (IOS / 'UITests/OnionaryDuoTests.swift').read_text()
        scenarios = re.findall(r'\bfunc\s+(test\w+)\s*\(', source)
        assert 'testMarketingScreenshots' in scenarios
        runs = [c for c in commands if 'test-without-building' in c]
        assert [c[-1] for c in runs] == [f'-only-testing:OnionaryUITests/OnionaryDuoTests/{name}' for name in scenarios]
        assert [c[c.index('-destination') + 1].split('id=')[-1] for c in runs] == instances
        assert sum('build-for-testing' in c for c in commands) == 1
    else:
        assert len(instances) == 1
    diagnostics = [i for i, command in enumerate(commands)
                   if any(arg.endswith('collect_ios_test_diagnostics.py') for arg in command)]
    assert len(diagnostics) == (0 if failure_stage == 'none' else 1)
    if diagnostics:
        assert diagnostics[0] < len(commands) - 1
        command = commands[diagnostics[0]]
        assert command[command.index('--simulator') + 1] == 'isolated-test-device-1'
        assert command[command.index('--output') + 1] == str(tmp_path / 'results/host-diagnostics')
