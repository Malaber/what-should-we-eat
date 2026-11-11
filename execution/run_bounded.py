"""Run a command once with a wall-clock deadline, including its child processes."""
import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path
from contextlib import nullcontext


def run(seconds, command, log=None):
    if log is not None:
        log = Path(log)
        log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("wb") if log else nullcontext(None) as output:
        print(f"Running once (deadline {seconds}s): {command[0]}" + (f"; log: {log}" if log else ""), flush=True)
        child = subprocess.Popen(command, start_new_session=True, stdout=output,
                                 stderr=subprocess.STDOUT if output else None)
        result = wait_for_command(child, seconds, command)
    if log:
        # Full output stays in the artifact. Bound console output so slow CI log
        # ingestion cannot block native subprocesses during accessibility queries.
        with log.open("rb") as source:
            source.seek(max(0, log.stat().st_size - 8192))
            print(source.read().decode("utf-8", errors="replace"), end="", flush=True)
    return result


def wait_for_command(child, seconds, command):
    try:
        return child.wait(timeout=seconds)
    except subprocess.TimeoutExpired:
        print(f"Command exceeded {seconds}s; stopping process group: {command[0]}", file=sys.stderr)
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
        return 124


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, help="Write full child output directly to this file")
    parser.add_argument("seconds", type=int)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.seconds <= 0 or not args.command:
        parser.error("A positive timeout and command are required")
    raise SystemExit(run(args.seconds, args.command, args.log))
