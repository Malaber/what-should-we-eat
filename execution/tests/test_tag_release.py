import subprocess

import pytest

from execution.tag_release import publish


def test_publish_never_replaces_local_or_remote_tag(tmp_path):
    remote = tmp_path / "remote.git"
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()

    git("config", "user.email", "test@example.org")
    git("config", "user.name", "Test")
    git("commit", "--allow-empty", "-m", "initial")
    git("remote", "add", "origin", str(remote))
    publish("v0.2.0-rc.1", "origin", repo)
    original = git("rev-parse", "HEAD")
    git("commit", "--allow-empty", "-m", "next")
    with pytest.raises(ValueError, match="already exists"):
        publish("v0.2.0-rc.1", "origin", repo)
    git("tag", "-d", "v0.2.0-rc.1")  # Disposable local fixture: test remote-only guard.
    with pytest.raises(ValueError, match="already exists"):
        publish("v0.2.0-rc.1", "origin", repo)
    assert git("ls-remote", "origin", "refs/tags/v0.2.0-rc.1").split()[0] == original
    publish("v0.2.0-rc.2", "origin", repo)
    assert git("ls-remote", "origin", "refs/tags/v0.2.0-rc.2").split()[0] == git("rev-parse", "HEAD")
