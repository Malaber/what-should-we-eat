"""Exercise release profile ordering/cache isolation without Xcode or uploads."""
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

SCRIPT = Path(__file__).parents[2] / 'ios/Onionary/Scripts/upload_testflight.sh'


@pytest.mark.parametrize('fail_profile', ['', 'iPad-Pro-13-inch-M5-16GB'])
def test_profiles_share_build_cache_but_not_results(tmp_path, fail_profile):
    bins = tmp_path / 'bin'
    bins.mkdir()
    shim = bins / 'bash'
    shim.write_text(f'''#!{sys.executable}
import json, os, sys
with open(os.environ['CAPTURE'], 'a') as out:
    out.write(json.dumps([sys.argv[1], os.environ.get('SIMULATOR_DEVICE_TYPE'),
                         os.environ.get('TEST_RESULTS_DIR'), os.environ.get('TEST_DERIVED_DATA_DIR')]) + '\\n')
if sys.argv[1].endswith('archive.sh'): sys.exit(43)  # Never reach real export.
if os.environ.get('FAIL_PROFILE') and os.environ['SIMULATOR_DEVICE_TYPE'].endswith(os.environ['FAIL_PROFILE']): sys.exit(42)
''')
    shim.chmod(0o755)
    python = bins / 'python3'
    python.write_text('#!/bin/sh\nexit 0\n')
    python.chmod(0o755)
    capture = tmp_path / 'commands.jsonl'
    result = subprocess.run(['/bin/bash', str(SCRIPT), '0.6.0', '26'], env={**os.environ,
        'PATH': str(bins) + os.pathsep + os.environ['PATH'], 'TMPDIR': str(tmp_path),
        'CAPTURE': str(capture), 'FAIL_PROFILE': fail_profile})
    calls = [json.loads(line) for line in capture.read_text().splitlines()]
    profiles = [c for c in calls if c[0].endswith('test.sh')]
    assert len(profiles) == (2 if fail_profile else 3)
    assert len({c[2] for c in profiles}) == len(profiles)
    assert len({c[3] for c in profiles}) == 1
    assert profiles[0][3] and profiles[0][3] != profiles[0][2]
    assert result.returncode == (42 if fail_profile else 43)
    assert any(c[0].endswith('archive.sh') for c in calls) == (not fail_profile)
