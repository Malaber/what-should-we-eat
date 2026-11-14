"""Retain bounded, read-only evidence before a failed test simulator is deleted."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
from uuid import UUID


def capture(command, destination, *, timeout=5, limit=65536):
    """Run once; retain a bounded tail even on timeout or a nonzero exit."""
    report = {"command": command, "returncode": None, "timed_out": False}
    with tempfile.TemporaryFile() as output:
        try:
            result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT,
                                    timeout=timeout, check=False)
            report["returncode"] = result.returncode
        except subprocess.TimeoutExpired:
            report["timed_out"] = True
        except OSError as error:
            report["error"] = str(error)
        size = output.tell()
        report["truncated_bytes"] = max(0, size - limit)
        output.seek(max(0, size - limit))
        destination.write_bytes(output.read())
    return report


def commands(simulator):
    # UUID validation keeps the log predicate an exact device filter. No writes
    # to simulator state, no environment dump and no unrelated process cleanup.
    simulator = str(UUID(simulator)).upper()
    predicate = (
        '(process CONTAINS "CoreSimulator" OR process == "launchd_sim") AND '
        f'(eventMessage CONTAINS[c] "{simulator}" OR '
        'eventMessage CONTAINS[c] "shutdown" OR '
        'eventMessage CONTAINS[c] "termination" OR '
        'eventMessage CONTAINS[c] "memory pressure")'
    )
    return {
        "hardware": ["sysctl", "hw.ncpu", "hw.memsize"],
        "memory": ["vm_stat"],
        "swap": ["sysctl", "vm.swapusage"],
        "devices": ["xcrun", "simctl", "list", "devices", "--json"],
        "runtimes": ["xcrun", "simctl", "list", "runtimes", "--json"],
        "simulator-events": ["/usr/bin/log", "show", "--last", "15m", "--style",
                             "compact", "--predicate", predicate],
    }


def collect(output, simulator):
    plan = commands(simulator)
    output.mkdir(parents=True, exist_ok=True)
    reports = {name: capture(command, output / f"{name}.txt")
               for name, command in plan.items()}
    manifest = {"simulator": simulator, "commands": reports}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--simulator", required=True)
    args = parser.parse_args()
    collect(args.output, args.simulator)
