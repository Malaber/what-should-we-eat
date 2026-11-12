"""Exercise the real Duo orchestration contract without a simulator."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys
import pytest

SCRIPTS = Path(__file__).parents[2] / 'ios/Onionary/Scripts'


@pytest.fixture
def runner(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    spec = importlib.util.spec_from_file_location('duo_runner', SCRIPTS / 'run_duo_tests.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('shared', [False, True])
def test_uses_built_bundle_and_propagates_test_failure(runner, monkeypatch, tmp_path, shared):
    results = tmp_path / 'results'
    results.mkdir()
    derived = tmp_path / 'shared cache' if shared else results / 'DerivedData'
    bundle = derived / 'Build/Products/Debug-iphonesimulator/OnionaryUITests-Runner.app/PlugIns/OnionaryUITests.xctest'
    bundle.mkdir(parents=True)
    (results / 'duo-hinge').write_text('prepared')
    events = []
    class Hinge:
        def __init__(self, command): events.append('helper')
        def close(self): events.append('closed')
    class Server:
        server_port = 12345
        def __init__(self, *args): pass
        def serve_forever(self): pass
        def shutdown(self): events.append('shutdown')
        def server_close(self): events.append('server_closed')
    monkeypatch.setattr(runner, 'HingeProcess', Hinge)
    monkeypatch.setattr(runner, 'HTTPServer', Server)
    command = [sys.executable, 'run_bounded.py', '--log', str(results/'tests.log'), '1800',
               'xcodebuild', '-derivedDataPath', str(derived), 'test-without-building']
    def execute(actual, **kwargs):
        assert actual == command
        assert (bundle/'duo-port.txt').read_text() == '12345'
        return SimpleNamespace(returncode=65)
    monkeypatch.setattr(runner.subprocess, 'run', execute)
    assert runner.main(['test-device', str(results), *command]) == 65
    assert events == ['helper', 'shutdown', 'server_closed', 'closed']
    if shared:
        assert not (results/'DerivedData').exists()
    assert bundle.exists()


def test_missing_build_fails_before_starting_helper(runner, monkeypatch, tmp_path):
    monkeypatch.setattr(runner, 'HingeProcess', lambda *_: pytest.fail('Helper started without bundle'))
    with pytest.raises(FileNotFoundError, match='Build the Duo test bundle'):
        runner.main(['device', str(tmp_path), 'xcodebuild', '-derivedDataPath', str(tmp_path/'absent')])


def test_prepare_only_compiles_without_starting_simulator(runner, monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(runner.subprocess, 'run', lambda command, **kwargs: calls.append((command, kwargs)))
    monkeypatch.setattr(runner, 'HingeProcess', lambda *_: pytest.fail('Helper started during prepare'))
    assert runner.main(['--prepare', str(tmp_path/'results')]) == 0
    assert calls[0][0][0:4] == ['xcrun', '--sdk', 'iphonesimulator', 'clang']
    assert calls[0][1] == {'check': True, 'timeout': 120}
