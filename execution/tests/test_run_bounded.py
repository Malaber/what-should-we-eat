import sys
from execution.run_bounded import run


def test_preserves_command_status():
    assert run(5, [sys.executable, '-c', 'raise SystemExit(7)']) == 7


def test_stalled_command_is_stopped():
    assert run(1, [sys.executable, '-c', 'import time; time.sleep(60)']) == 124


def test_verbose_output_goes_directly_to_log(tmp_path, capsys):
    log = tmp_path / 'native' / 'tests.log'
    command = [sys.executable, '-c',
               "import sys; sys.stdout.write('x' * 2_000_000); sys.stdout.flush(); sys.stderr.write('FAILURE END\\n'); raise SystemExit(65)"]
    assert run(5, command, log) == 65
    assert log.stat().st_size >= 2_000_000
    assert log.read_text().endswith('FAILURE END\n')
    assert len(capsys.readouterr().out) < 9000


def test_timeout_retains_partial_log(tmp_path):
    log = tmp_path / 'timeout.log'
    assert run(1, [sys.executable, '-u', '-c',
                   "import time; print('started'); time.sleep(60)"], log) == 124
    assert log.read_text() == 'started\n'


def test_log_cli_preserves_failure(tmp_path):
    import subprocess
    from pathlib import Path
    log = tmp_path / 'cli.log'
    result = subprocess.run([sys.executable, str(Path(__file__).parents[1] / 'run_bounded.py'),
                             '--log', str(log), '5', sys.executable, '-c',
                             "print('native failure'); raise SystemExit(65)"], capture_output=True, text=True)
    assert result.returncode == 65
    assert log.read_text() == 'native failure\n'
    assert 'native failure' in result.stdout
