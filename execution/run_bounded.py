"""Run a command once with a wall-clock deadline, including its child processes."""
import argparse
import os
import signal
import subprocess
import sys


def run(seconds, command):
    child = subprocess.Popen(command, start_new_session=True)
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
    parser.add_argument("seconds", type=int)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.seconds <= 0 or not args.command:
        parser.error("A positive timeout and command are required")
    raise SystemExit(run(args.seconds, args.command))
