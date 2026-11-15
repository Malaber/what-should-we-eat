"""Publishing must be gated by both full profiles and the unchanged tested source."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from execution import verify_ios_pr as runner

COMMIT = "a" * 40
BRANCH = "codex/recipe-tools-marketing"


@pytest.mark.parametrize("failed_profile", [None, "iphone", "ipad"])
def test_only_two_complete_passes_can_publish_exact_tested_commit(monkeypatch, tmp_path, failed_profile):
    calls, environments = [], []
    monkeypatch.setenv("SIMULATOR_ID", "unrelated-device")
    monkeypatch.setattr(runner, "git", lambda repo, *args:
                        COMMIT if args == ("rev-parse", "HEAD") else BRANCH if args[0] == "branch" else "")

    def run(command, **kwargs):
        calls.append(command)
        if command[0] == "bash":
            env = kwargs["env"]
            environments.append(env)
            name = Path(env["TEST_RESULTS_DIR"]).name
            return subprocess.CompletedProcess(command, 65 if name == failed_profile else 0)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(runner.subprocess, "run", run)
    output = tmp_path / "verification"
    result = runner.verify(tmp_path, COMMIT, output, tmp_path / "build", BRANCH)
    status = json.loads((output / "status.json").read_text())
    pushes = [c for c in calls if c[:2] == ["git", "push"]]
    assert result == (65 if failed_profile else 0)
    assert status["published"] == (failed_profile is None)
    assert status["status"] == ("failed" if failed_profile else "passed")
    assert len(environments) == (1 if failed_profile == "iphone" else 2)
    assert all("SIMULATOR_ID" not in e for e in environments)
    assert all(e["SIMULATOR_RUNTIME"] == "27.0" for e in environments)
    assert all(e["PATH"].split(os.pathsep)[0] == str(Path(sys.executable).parent) for e in environments)
    assert len({e["TEST_RESULTS_DIR"] for e in environments}) == len(environments)
    assert all(e["TEST_DERIVED_DATA_DIR"] == str(tmp_path / "build") for e in environments)
    assert all(c[1] == str(output / "source/ios/Onionary/Scripts/test.sh") for c in calls if c[0] == "bash")
    assert calls[0] == ["git", "worktree", "add", "--detach", str(output / "source"), COMMIT]
    assert pushes == ([] if failed_profile else [["git", "push", "github", f"{COMMIT}:refs/heads/{BRANCH}"]])


@pytest.mark.parametrize("change", ["head", "branch", "dirty"])
def test_source_changes_during_verification_prevent_publish(monkeypatch, tmp_path, change):
    completed, pushes = [], []

    def git(repo, *args):
        changed = len(completed) == 2
        if args == ("rev-parse", "HEAD"):
            return "b" * 40 if changed and change == "head" else COMMIT
        if args[0] == "branch":
            return "codex/other" if changed and change == "branch" else BRANCH
        return " M file.swift" if changed and change == "dirty" else ""

    def run(command, **kwargs):
        if command[0] == "bash":
            completed.append(kwargs["env"]["SIMULATOR_DEVICE_TYPE"])
        if command[:2] == ["git", "push"]:
            pushes.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(runner, "git", git)
    monkeypatch.setattr(runner.subprocess, "run", run)
    output = tmp_path / "verification"
    assert runner.verify(tmp_path, COMMIT, output, tmp_path / "build", BRANCH) == 1
    assert len(completed) == 2
    assert not pushes
    status = json.loads((output / "status.json").read_text())
    assert status["published"] is False
    assert status["status"] == "failed"
    assert "not published" in status["error"]


def test_verification_without_publish_option_never_pushes(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(runner, "git", lambda repo, *args: COMMIT if args[0] == "rev-parse" else "")
    monkeypatch.setattr(runner.subprocess, "run", lambda command, **kwargs:
                        calls.append(command) or subprocess.CompletedProcess(command, 0))
    assert runner.verify(tmp_path, COMMIT, tmp_path / "verification", tmp_path / "build") == 0
    assert not any(c[:2] == ["git", "push"] for c in calls)


def test_runner_cannot_publish_main(monkeypatch, tmp_path):
    with pytest.raises(ValueError, match="codex/"):
        runner.verify(tmp_path, COMMIT, tmp_path / "verification", tmp_path / "build", "main")
    assert not (tmp_path / "verification").exists()


def test_existing_result_directory_is_not_overwritten(tmp_path):
    output = tmp_path / "verification"
    output.mkdir()
    marker = output / "status.json"
    marker.write_text("existing result")
    with pytest.raises(FileExistsError):
        runner.verify(tmp_path, COMMIT, output, tmp_path / "build", BRANCH)
    assert marker.read_text() == "existing result"


def test_rejected_push_is_not_reported_as_published_or_retried(monkeypatch, tmp_path):
    pushes = []
    monkeypatch.setattr(runner, "git", lambda repo, *args:
                        COMMIT if args[0] == "rev-parse" else BRANCH if args[0] == "branch" else "")

    def run(command, **kwargs):
        if command[:2] == ["git", "push"]:
            pushes.append(command)
            raise subprocess.CalledProcessError(128, command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(runner.subprocess, "run", run)
    output = tmp_path / "verification"
    assert runner.verify(tmp_path, COMMIT, output, tmp_path / "build", BRANCH) == 128
    status = json.loads((output / "status.json").read_text())
    assert status["status"] == "failed"
    assert status["published"] is False
    assert len(pushes) == 1


def test_initial_dirty_source_never_starts_work(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(runner, "git", lambda repo, *args:
                        COMMIT if args[0] == "rev-parse" else BRANCH if args[0] == "branch" else " M file.swift")
    monkeypatch.setattr(runner.subprocess, "run", lambda command, **kwargs:
                        calls.append(command) or subprocess.CompletedProcess(command, 0))
    output = tmp_path / "verification"
    assert runner.verify(tmp_path, COMMIT, output, tmp_path / "build", BRANCH) == 1
    assert not calls
    assert json.loads((output / "status.json").read_text())["published"] is False
