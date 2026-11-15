"""Failure evidence must be useful, bounded and unable to change test outcomes."""
import json
import subprocess
import sys

from execution.collect_ios_test_diagnostics import capture, collect, commands


def test_capture_preserves_failure_unicode_and_bounds_output(tmp_path):
    destination = tmp_path / "output.txt"
    report = capture([sys.executable, "-c",
                      "import sys; print('x' * 1000); print('Schädler'); sys.exit(23)"],
                     destination, limit=100)
    assert report["returncode"] == 23
    assert not report["timed_out"]
    assert report["truncated_bytes"] > 900
    assert destination.stat().st_size == 100
    assert destination.read_text().endswith("Schädler\n")


def test_capture_timeout_is_reported_without_retry(tmp_path, monkeypatch):
    invoked = []
    run = subprocess.run

    def observed_run(command, **kwargs):
        invoked.append(command)
        return run(command, **kwargs)

    monkeypatch.setattr("execution.collect_ios_test_diagnostics.subprocess.run", observed_run)
    report = capture([sys.executable, "-c",
                      "import time; time.sleep(30)"],
                     tmp_path / "output.txt", timeout=0.1)
    assert report["timed_out"]
    assert report["returncode"] is None
    assert len(invoked) == 1


def test_missing_tool_does_not_prevent_other_evidence(tmp_path, monkeypatch):
    simulator = "A1C60F1B-3CA3-4D80-A108-6AA0C745D2BF"
    monkeypatch.setattr("execution.collect_ios_test_diagnostics.commands", lambda device: {
        "unavailable": [str(tmp_path / "missing-command")],
        "available": [sys.executable, "-c", "print('evidence retained')"],
    })
    result = collect(tmp_path / "report", simulator)
    assert "error" in result["commands"]["unavailable"]
    assert result["commands"]["available"]["returncode"] == 0
    assert (tmp_path / "report/available.txt").read_text() == "evidence retained\n"
    assert json.loads((tmp_path / "report/manifest.json").read_text()) == result


def test_inventory_is_read_only_and_filters_device():
    simulator = "A1C60F1B-3CA3-4D80-A108-6AA0C745D2BF"
    plan = commands(simulator)
    assert plan["devices"] == ["xcrun", "simctl", "list", "devices", "--json"]
    assert simulator in plan["simulator-events"][-1]
    assert not {"shutdown", "erase", "delete", "boot"}.intersection(
        argument for command in plan.values() for argument in command)
