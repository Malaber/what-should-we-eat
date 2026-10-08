from unittest.mock import patch
from types import SimpleNamespace
from execution.version import version


def test_initial_version_without_tags(monkeypatch):
    monkeypatch.delenv('APP_VERSION', raising=False)
    with patch('execution.version.subprocess.run', return_value=SimpleNamespace(stdout='')), patch('execution.version.subprocess.check_output', return_value='abc123\n'):
        assert version() == '0.2.0-dev.abc123'


def test_exact_release_candidate(monkeypatch):
    monkeypatch.delenv('APP_VERSION', raising=False)
    with patch('execution.version.subprocess.run', side_effect=[SimpleNamespace(stdout='v0.2.0-rc.1\n'), SimpleNamespace(stdout='v0.2.0-rc.1\n')]):
        assert version() == '0.2.0-rc.1'


def test_stable_tag_and_container_version(monkeypatch):
    monkeypatch.setenv('APP_VERSION','0.3.0')
    assert version() == '0.3.0'
    monkeypatch.delenv('APP_VERSION')
    with patch('execution.version.subprocess.run', side_effect=[SimpleNamespace(stdout='v0.2.0\nv0.3.0\n'),SimpleNamespace(stdout='v0.3.0\n')]):
        assert version() == '0.3.0'
