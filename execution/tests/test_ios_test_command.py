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
    default_limit = '-default-test-execution-time-allowance'
    maximum_limit = '-maximum-test-execution-time-allowance'
    assert test.count(default_limit) == test.count(maximum_limit) == 1
    assert test[test.index(default_limit) + 1] == allowance
    assert test[test.index(maximum_limit) + 1] == ('240' if allowance == '180' else allowance)
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
        assert run[run.index('-default-test-execution-time-allowance') + 1] == '180'
        assert run[run.index('-maximum-test-execution-time-allowance') + 1] == '240'


def test_hosted_duo_jobs_select_each_declared_case_once(tmp_path):
    workflow = (IOS.parents[1] / '.github/workflows/ci.yml').read_text()
    shards = re.findall(r'^\s+shard: (test\w+(?:,test\w+)*)$', workflow, re.MULTILINE)
    cases = re.findall(r'\bfunc\s+(test\w+)\s*\(', (IOS / 'UITests/OnionaryDuoTests.swift').read_text())
    assert len(shards) == 3
    assert sorted(case for shard in shards for case in shard.split(',')) == sorted(cases)

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
           'SIMULATOR_DEVICE_TYPE': 'com.apple.CoreSimulator.SimDeviceType.iPhone-Duo',
           'TEST_RESULTS_DIR': str(tmp_path / 'results')}
    for shard in shards:
        subprocess.run(['bash', str(SCRIPT), '--test-only'],
                       env={**env, 'SIMULATOR_TEST_SHARD': shard}, check=True)
    unknown = subprocess.run(['bash', str(SCRIPT), '--test-only'],
                             env={**env, 'SIMULATOR_TEST_SHARD': 'testNonexistent'})
    assert unknown.returncode == 2
    malformed = subprocess.run(['bash', str(SCRIPT), '--test-only'],
                               env={**env, 'SIMULATOR_TEST_SHARD': f'{cases[0]},'})
    assert malformed.returncode == 2

    runs = [json.loads(line) for line in capture.read_text().splitlines()]
    assert len(runs) == len(shards)
    for shard, run in zip(shards, runs, strict=True):
        assert [arg for arg in run if arg.startswith('-only-testing:')] == [
            f'-only-testing:OnionaryUITests/OnionaryDuoTests/{case}' for case in shard.split(',')
        ]
        assert run[run.index('-resultBundlePath') + 1].endswith(f'/duo/{shard}/Onionary.xcresult')
        assert run[run.index('-maximum-test-execution-time-allowance') + 1] == '360'


def test_advisory_ios_jobs_do_not_gate_production_release():
    workflow = (IOS.parents[1] / '.github/workflows/ci.yml').read_text()
    jobs = dict(re.findall(r'^  ([a-z][a-z-]*):\n((?:^[ ]{4}[^\n]*\n|^\n)*)', workflow, re.MULTILINE))
    expected = {
        ('iphone', '2'),
        ('iphone', '3'),
        ('ipad', '2'),
        ('ipad', '3'),
        ('duo', 'testRecipeDraftSurvivesFolds,testRecipePreviewAndChecklistSurviveFolds'),
        ('duo', 'testExpiredSessionKeepsAdaptiveNavigationReachable,testKitchenShoppingChecksSurviveFolds'),
    }
    rows = r"^\s+- profile: (\w+)\n\s+device: [^\n]+\n\s+shard: '?(\w[\w,]*)"
    assert set(re.findall(rows, jobs['ios-advisory'], re.MULTILINE)) == expected
    assert 'ios' not in jobs
    capture_jobs = ('iphone-captures', 'ipad-captures', 'duo-captures')
    for name in ('ios-advisory', *capture_jobs):
        assert 'uses: ./.github/actions/native-ios' in jobs[name]
        assert 'continue-on-error: true' in jobs[name]
    for name in capture_jobs:
        assert "capture: 'true'" in jobs[name]
        assert 'outputs.captures' in jobs[name]
        assert f"needs.{name}.outputs.available == 'true'" in jobs['appstore-screenshots']
    assert "shard: '1'" in jobs['iphone-captures']
    assert "shard: '1'" in jobs['ipad-captures']
    assert 'shard: testMarketingScreenshots' in jobs['duo-captures']
    assert 'needs: [iphone-captures, ipad-captures, duo-captures]' in jobs['appstore-screenshots']
    release = jobs['release-main']
    required = ('backend', 'browser', 'ios-build', 'ios-archive', 'publish-image', 'html-format')
    assert f"needs: [{', '.join((*required, 'appstore-screenshots'))}]" in release
    for name in required:
        assert 'continue-on-error' not in jobs[name]
        assert f"needs.{name}.result == 'success'" in release
    assert "needs.appstore-screenshots.result == 'skipped'" in release
    assert "needs.appstore-screenshots.result == 'success'" in release
    assert "github.ref == 'refs/heads/main'" in release
    assert 'push: true' in release
    assert 'platforms: linux/amd64,linux/arm64' in release
    assert 'python3 -m execution.release_main --publish\n' in release
    assert 'python3 -m execution.release_main --publish-assets' in release


@pytest.mark.parametrize(('profile', 'failure'), [
    ('iPhone-17-Pro', None),
    ('iPad-Pro-13-inch-M5-12GB', 'test'),
    ('iPhone-Duo', None),
    ('iPhone-Duo', 'bootstatus'),
    ('iPhone-Duo', 'Onionary.app'),
    ('iPhone-Duo', 'OnionaryUITests-Runner.app'),
    ('iPhone-Duo', 'test'),
])
def test_hosted_simulator_preparation_is_profile_specific(tmp_path, profile, failure):
    bins = tmp_path / 'bin'
    bins.mkdir()
    capture = tmp_path / 'commands.jsonl'
    shim = f'''#!{sys.executable}
import json, os, sys
with open(os.environ['CAPTURE_ARGS'], 'a') as output:
    output.write(json.dumps([os.path.basename(sys.argv[0]), *sys.argv[1:]]) + '\\n')
if '--test-products' in sys.argv:
    print(sys.argv[-1] + '/Onionary_iphonesimulator27.2-arm64.xctestrun')
if any(arg.endswith('resolve_simulator.py') for arg in sys.argv): print('hosted-test-device')
failure = os.environ['STAGE_FAILURE']
if failure == 'test' and 'test-without-building' in sys.argv: sys.exit(44)
if failure == 'bootstatus' and 'bootstatus' in sys.argv: sys.exit(44)
if 'install' in sys.argv and sys.argv[-1].endswith('/' + failure): sys.exit(44)
if 'delete' in sys.argv: sys.exit(124)
'''
    for name in ('python3', 'xcrun'):
        command = bins / name
        command.write_text(shim)
        command.chmod(0o755)
    results = tmp_path / 'results'
    device_set = str(results / 'simulator-set')
    duo = profile == 'iPhone-Duo'
    env = {**os.environ, 'PATH': str(bins) + os.pathsep + os.environ['PATH'],
           'CAPTURE_ARGS': str(capture), 'TEST_RESULTS_DIR': str(results),
           'STAGE_FAILURE': failure or '',
           'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'github-hosted',
           'SIMULATOR_DEVICE_TYPE': f'com.apple.CoreSimulator.SimDeviceType.{profile}',
           'SIMULATOR_RUNTIME': '27.2',
           'SIMULATOR_TEST_SHARD': 'testMarketingScreenshots' if duo else '1'}
    env.pop('SIMULATOR_ID', None)
    result = subprocess.run(['bash', str(SCRIPT), '--test-only'], env=env)
    assert result.returncode == (44 if failure else 0)
    runs = [json.loads(line) for line in capture.read_text().splitlines()]
    create, = [run for run in runs if '--create' in run]
    assert create[-2:] == ['--device-set', device_set]
    products = results / 'DerivedData/Build/Products/Debug-iphonesimulator'
    simctl = ['xcrun', 'simctl', '--set', device_set]
    setup = [
        [*simctl, 'bootstatus', 'hosted-test-device', '-b'],
        [*simctl, 'install', 'hosted-test-device', str(products / 'Onionary.app')],
        [*simctl, 'install', 'hosted-test-device', str(products / 'OnionaryUITests-Runner.app')],
    ]
    setup_length = {'bootstatus': 1, 'Onionary.app': 2}.get(failure, 3)
    preparation = [run for run in runs if 'bootstatus' in run or 'install' in run]
    assert [run[run.index('xcrun'):] for run in preparation] == (setup[:setup_length] if duo else [])
    assert runs[runs.index(create) + 1:][:len(preparation)] == preparation
    xctest = [run for run in runs if 'test-without-building' in run]
    if failure in (None, 'test'):
        run, = xctest
        assert f'-DVTSimulatorSetLocation={device_set}' in run
        assert run[run.index('--startup-seconds') + 1] == '900'
        assert run[run.index('-destination') + 1] == 'platform=iOS Simulator,id=hosted-test-device'
        assert run[run.index('-xctestrun') + 1] == str(products.parent / 'Onionary_iphonesimulator27.2-arm64.xctestrun')
    else:
        assert not xctest
    diagnostics = [run for run in runs if '--simulator' in run]
    assert len(diagnostics) == int(failure is not None)
    if diagnostics:
        assert diagnostics[0][-2:] == ['--device-set', device_set]
    assert runs[-1][runs[-1].index('xcrun') - 1:] == [
        '30', *simctl, 'delete', 'hosted-test-device',
    ]


@pytest.mark.parametrize('failure_stage', ['none', 'build', 'app', 'plan', 'test'])
@pytest.mark.parametrize('runtime_override', [None, '27.1'])
@pytest.mark.parametrize('diagnostics_fail', [False, True])
def test_xctest_owns_boot_and_declared_runtime_reaches_selector(tmp_path, failure_stage, runtime_override, diagnostics_fail):
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
if any(arg in sys.argv for arg in ('boot', 'bootstatus', 'getenv', 'spawn')): sys.exit(95)
if any(arg.endswith('ios_runtime.py') for arg in sys.argv): sys.exit(95)
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
    assert result.returncode == {'none': 0, 'build': 42, 'app': 41, 'plan': 45, 'test': 44}[failure_stage]
    assert not any(set(c) & {'boot', 'bootstatus', 'getenv', 'spawn'} for c in commands)
    if failure_stage in {'build', 'app', 'plan'}:
        assert not any('test-without-building' in c for c in commands)
    else:
        ready = next(i for i, c in enumerate(commands) if '--test-products' in c)
        test = next(i for i, c in enumerate(commands) if 'test-without-building' in c)
        assert build < ready < test
        assert not any(any('run_duo_tests.py' in a or '--prepare' == a for a in c) for c in commands)
    if failure_stage != 'build':
        layout = next(i for i, c in enumerate(commands) if '--test-app' in c)
        assert build < layout
        assert commands[layout][-1] == str(tmp_path / 'results/DerivedData/Build/Products/Debug-iphonesimulator/Onionary.app')
        if failure_stage not in {'app', 'plan'}:
            assert layout < next(i for i, c in enumerate(commands) if 'test-without-building' in c)
    if failure_stage in {'none', 'test'}:
        execution = next(c for c in commands if 'test-without-building' in c)
        assert execution[execution.index('--startup-seconds') + 1] == '600'
        assert execution[execution.index('--ready-prefix') + 1] == "Test Suite 'Selected tests' started at "
        assert execution[execution.index('xcodebuild') - 1] == '1800'
    instances = [c[-1] for c in commands if c[-4:-1] == ['xcrun', 'simctl', 'delete']]
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
