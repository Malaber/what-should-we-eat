from pathlib import Path
import pytest
from execution.configure_ci_apt import configure


def fixture(root, version='24.04'):
    (root/'etc/apt/sources.list.d').mkdir(parents=True)
    (root/'etc/apt/apt.conf.d').mkdir()
    (root/'etc/os-release').write_text(f'ID=ubuntu\nVERSION_ID="{version}"\n')
    sources = root/'etc/apt/sources.list.d/ubuntu.sources'
    sources.write_text('Types: deb\nURIs: mirror+file:/etc/apt/apt-mirrors.txt\nSuites: noble noble-updates\nComponents: main universe\nSigned-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg\n\nTypes: deb\nURIs: https://security.ubuntu.com/ubuntu\nSuites: noble-security\nComponents: main universe\nSigned-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg\n')
    return sources


def test_keeps_security_updates_and_signature_verification(tmp_path):
    sources = fixture(tmp_path)
    before = sources.read_text()
    configure(tmp_path)
    after = sources.read_text()
    assert after.count('URIs: https://archive.ubuntu.com/ubuntu/') == 2
    assert 'security.ubuntu.com' not in after
    assert [s for s in before.splitlines() if not s.startswith('URIs:')] == [s for s in after.splitlines() if not s.startswith('URIs:')]
    config = (tmp_path/'etc/apt/apt.conf.d/99-onionary-ci').read_text()
    assert 'Error-Mode "any"' in config and 'Retries "0"' in config
    configure(tmp_path)
    assert sources.read_text() == after


def test_wrong_distribution_does_not_alter_sources(tmp_path):
    sources = fixture(tmp_path, '26.04')
    before = sources.read_text()
    with pytest.raises(ValueError, match='pinned Ubuntu 24.04'):
        configure(tmp_path)
    assert sources.read_text() == before
    assert not (tmp_path/'etc/apt/apt.conf.d/99-onionary-ci').exists()
