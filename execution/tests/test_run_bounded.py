import sys
from execution.run_bounded import run


def test_preserves_command_status():
    assert run(5, [sys.executable, '-c', 'raise SystemExit(7)']) == 7


def test_stalled_command_is_stopped():
    assert run(1, [sys.executable, '-c', 'import time; time.sleep(60)']) == 124
