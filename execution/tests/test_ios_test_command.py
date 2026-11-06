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
