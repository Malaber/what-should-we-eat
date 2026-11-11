"""Exercise the shell entry point with fake tool executables, never a simulator."""
import json
import os
from pathlib import Path
import subprocess

import pytest

SCRIPT = Path(__file__).parents[2] / 'ios/Onionary/Scripts/test.sh'


@pytest.mark.parametrize('device,allowance,suite', [
    ('iPhone-17-Pro', '180', 'OnionaryUITests'),
    ('iPad-Pro-13-inch-M5-16GB', '180', 'OnionaryUITests'),
    ('iPhone-Duo', '360', 'OnionaryDuoTests'),
])
def test_test_command_has_one_timeout_per_option(tmp_path, device, allowance, suite):
    bins = tmp_path / 'bin'; bins.mkdir()
    for command in ('swift', 'xcodegen'):
        path = bins / command; path.write_text('#!/bin/sh\nexit 0\n'); path.chmod(0o755)
    python = bins / 'python3'
    python.write_text('''#!/usr/bin/env python3_REAL
import json, os, sys
if sys.argv[1].endswith('version.py'):
    print('0.6.0')
elif 'xcodebuild' in sys.argv:
    with open(os.environ['CAPTURE_ARGS'], 'a') as f:
        f.write(json.dumps(sys.argv[sys.argv.index('xcodebuild')+1:]) + '\\n')
'''.replace('/usr/bin/env python3_REAL', __import__('sys').executable))
    python.chmod(0o755)
    capture = tmp_path / 'args.jsonl'
    subprocess.run(['bash', str(SCRIPT)], check=True, env={**os.environ,
        'PATH': str(bins) + os.pathsep + os.environ['PATH'], 'CAPTURE_ARGS': str(capture),
        'SIMULATOR_ID': 'test-only', 'SIMULATOR_DEVICE_TYPE': device,
        'TEST_RESULTS_DIR': str(tmp_path / 'results')})
    build, test = [json.loads(line) for line in capture.read_text().splitlines()]
    assert 'build-for-testing' in build
    assert 'test-without-building' in test
    for option in ('-default-test-execution-time-allowance', '-maximum-test-execution-time-allowance'):
        assert test.count(option) == 1
        assert test[test.index(option) + 1] == allowance
    assert f'-only-testing:OnionaryUITests/{suite}' in test
    assert '-retry-tests-on-failure' not in test


@pytest.mark.parametrize('build_fails', [False, True])
@pytest.mark.parametrize('runtime_override', [None, '27.1'])
def test_compile_precedes_boot_and_declared_runtime_reaches_selector(tmp_path, build_fails, runtime_override):
    bins = tmp_path / 'bin'; bins.mkdir()
    capture = tmp_path / 'commands.jsonl'
    shim = '''#!PYTHON
import json, os, sys
with open(os.environ['CAPTURE_ARGS'], 'a') as output:
    output.write(json.dumps([os.path.basename(sys.argv[0]), *sys.argv[1:]]) + '\\n')
if any(arg.endswith('version.py') for arg in sys.argv): print('0.6.0')
if any(arg.endswith('resolve_simulator.py') for arg in sys.argv): print('isolated-test-device')
if 'build-for-testing' in sys.argv and os.environ['FAIL_BUILD'] == '1': sys.exit(42)
'''.replace('PYTHON', __import__('sys').executable)
    for name in ('python3', 'swift', 'xcodegen', 'xcrun'):
        path = bins / name; path.write_text(shim); path.chmod(0o755)
    env = {**os.environ, 'PATH': str(bins) + os.pathsep + os.environ['PATH'],
           'CAPTURE_ARGS': str(capture), 'FAIL_BUILD': str(int(build_fails)),
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
    assert result.returncode == (42 if build_fails else 0)
    if build_fails:
        assert not any('boot' in c or 'test-without-building' in c for c in commands)
    else:
        boot = next(i for i, c in enumerate(commands) if 'boot' in c)
        ready = next(i for i, c in enumerate(commands) if 'bootstatus' in c)
        test = next(i for i, c in enumerate(commands) if 'test-without-building' in c)
        assert build < boot < ready < test
    assert commands[-1] == ['xcrun', 'simctl', 'delete', 'isolated-test-device']
