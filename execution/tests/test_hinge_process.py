import importlib.util
from pathlib import Path
import sys
import pytest

spec = importlib.util.spec_from_file_location('hinge', Path(__file__).parents[2] / 'ios/Onionary/Scripts/hinge_process.py')
hinge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hinge)


def command(body):
    return [sys.executable, '-u', '-c', body]


def test_folds_share_one_process_and_acknowledge_each_angle():
    controller = hinge.HingeProcess(command('import sys\nprint("READY")\nfor line in sys.stdin: print("OK " + line.strip())'))
    pid = controller.process.pid
    try:
        for angle in [0, 180, 90, 180, 0]:
            controller.pose(angle)
            assert controller.process.pid == pid
    finally:
        controller.close()
    assert controller.process.poll() is not None


@pytest.mark.parametrize('response', ['print("WRONG", flush=True)', 'sys.exit(7)', 'import time; time.sleep(5)'])
def test_failed_acknowledgement_stops_session_without_retry(response):
    controller = hinge.HingeProcess(command('import sys\nprint("READY")\nline=sys.stdin.readline()\n' + response), timeout=0.3)
    with pytest.raises((RuntimeError, TimeoutError)):
        controller.pose(90)
    assert controller.process.poll() is not None
    with pytest.raises(RuntimeError, match='no longer running'):
        controller.pose(180)


def test_partial_line_cannot_escape_deadline():
    with pytest.raises(TimeoutError):
        hinge.HingeProcess(command('import sys,time\nsys.stdout.write("REA");sys.stdout.flush();time.sleep(5)'), timeout=0.3)
