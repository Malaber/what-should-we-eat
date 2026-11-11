from pathlib import Path
import subprocess
import pytest
from execution import marketing_screenshots as capture


def test_build_then_boot_then_one_capture_test(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(capture.subprocess, 'run', lambda command, **kwargs: calls.append(command))
    capture.capture_tests('isolated', tmp_path, tmp_path/'result.xcresult')
    assert 'build-for-testing' in calls[0]
    assert calls[1][-4:] == ['simctl', 'bootstatus', 'isolated', '-b']
    assert not any('boot' in c or 'appearance' in c for c in calls)
    assert 'test-without-building' in calls[-1]
    assert sum('test-without-building' in c for c in calls) == 1
    assert all('run_bounded.py' in c[1] for c in calls)
    assert calls[-1][calls[-1].index('-maximum-test-execution-time-allowance')+1] == '180'


@pytest.mark.parametrize('failure_index', [0, 1, 2, 3])
def test_capture_failure_stops_without_retry(monkeypatch, tmp_path, failure_index):
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        if len(calls) == failure_index + 1:
            raise subprocess.CalledProcessError(65, command)
    monkeypatch.setattr(capture.subprocess, 'run', run)
    with pytest.raises(subprocess.CalledProcessError):
        capture.capture_tests('isolated', tmp_path, tmp_path/'result.xcresult')
    assert len(calls) == failure_index + 1
