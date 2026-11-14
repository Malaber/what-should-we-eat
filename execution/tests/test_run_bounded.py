import sys
import pytest
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


def test_initialization_does_not_consume_execution_budget(tmp_path):
    command = [sys.executable, '-u', '-c',
               "import time; time.sleep(0.5); print('SUITE STARTED'); print('test passed')"]
    assert run(0.25, command, tmp_path / 'native.log', 5, 'SUITE STARTED') == 0


def test_partial_prefix_is_recognized_without_accepting_middle_of_line(tmp_path):
    command = [sys.executable, '-u', '-c',
               "import time; print('not SUITE STARTED'); print('SUITE ', end='', flush=True); time.sleep(0.2); print('STARTED'); print('passed')"]
    assert run(5, command, tmp_path / 'native.log', 5, 'SUITE STARTED') == 0


def test_midline_text_is_not_suite_registration(tmp_path):
    command = [sys.executable, '-u', '-c', "print('not SUITE STARTED')"]
    assert run(5, command, tmp_path / 'native.log', 5, 'SUITE STARTED') == 125


def test_startup_reads_verbose_lines_with_bounded_console_output(tmp_path, capsys):
    command = [sys.executable, '-u', '-c', "print('x' * 2_000_000); print('SUITE STARTED'); raise SystemExit(65)"]
    assert run(5, command, tmp_path / 'native.log', 5, 'SUITE STARTED') == 65
    assert len(capsys.readouterr().out) < 9000


def test_initialization_cli_preserves_native_failure(tmp_path):
    import subprocess
    from pathlib import Path
    log = tmp_path / 'native.log'
    result = subprocess.run([sys.executable, str(Path(__file__).parents[1] / 'run_bounded.py'),
                             '--startup-seconds', '5', '--ready-prefix', 'SUITE STARTED',
                             '--log', str(log), '5', sys.executable, '-u', '-c',
                             "print('SUITE STARTED'); raise SystemExit(65)"], capture_output=True, text=True)
    assert result.returncode == 65
    assert 'Initialization completed' in result.stdout
    assert log.read_text() == 'SUITE STARTED\n'


@pytest.mark.parametrize('exit_code', [0, 65])
def test_missing_suite_start_cannot_report_success_and_preserves_failure(tmp_path, exit_code):
    command = [sys.executable, '-u', '-c', f"print('no suite started'); raise SystemExit({exit_code})"]
    assert run(5, command, tmp_path / 'native.log', 5, 'SUITE STARTED') == (exit_code or 125)


@pytest.mark.parametrize('phase', ['startup', 'execution'])
def test_each_phase_has_its_own_hard_deadline(tmp_path, phase):
    command = [sys.executable, '-u', '-c',
               "import time; " + ("print('SUITE STARTED'); " if phase == 'execution' else '') + "time.sleep(60)"]
    assert run(0.25, command, tmp_path / 'native.log', 0.5 if phase == 'startup' else 5, 'SUITE STARTED') == 124


@pytest.mark.parametrize('log,startup,prefix', [(None, 5, 'READY'), ('log', 0, 'READY'),
                                              ('log', 5, ''), ('log', None, 'READY'),
                                              ('log', 5, 'two\nlines')])
def test_invalid_initialization_contract_never_starts_command(tmp_path, log, startup, prefix):
    with pytest.raises(ValueError):
        run(5, ['must-not-run'], tmp_path / log if log else None, startup, prefix)
