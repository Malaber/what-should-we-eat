"""Run a command once with a wall-clock deadline, including its child processes."""
import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from contextlib import nullcontext


def run(seconds, command, log=None, startup_seconds=None, ready_prefix=None):
    if startup_seconds is not None or ready_prefix is not None:
        if not log or not ready_prefix or '\n' in ready_prefix or startup_seconds is None or startup_seconds <= 0:
            raise ValueError('A positive startup deadline requires a log and a nonempty single-line ready prefix.')
    if log is not None:
        log = Path(log)
        log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("wb") if log else nullcontext(None) as output:
        budget = f'deadline {seconds}s' if startup_seconds is None else f'startup {startup_seconds}s; execution {seconds}s'
        print(f"Running once ({budget}): {command[0]}" + (f"; log: {log}" if log else ""), flush=True)
        child = subprocess.Popen(command, start_new_session=True, stdout=output,
                                 stderr=subprocess.STDOUT if output else None)
        if startup_seconds is not None and not wait_for_startup(child, log, ready_prefix, startup_seconds):
            if child.poll() is None:
                print(f'Initialization exceeded {startup_seconds}s without the ready prefix; stopping process group.', flush=True)
                terminate_command(child)
                result = 124
            else:
                result = child.returncode or 125
                print('Command exited before initialization completed; no successful execution was verified.', flush=True)
        else:
            if startup_seconds is not None:
                print(f'Initialization completed; execution deadline {seconds}s starts now.', flush=True)
            result = wait_for_command(child, seconds, command)
    if log:
        # Full output stays in the artifact. Bound console output so slow CI log
        # ingestion cannot block native subprocesses during accessibility queries.
        with log.open("rb") as source:
            source.seek(max(0, log.stat().st_size - 8192))
            print(source.read().decode("utf-8", errors="replace"), end="", flush=True)
    return result


def wait_for_startup(child, log, prefix, seconds):
    """Tail a bounded line prefix in-process; never run the command again."""
    deadline = time.monotonic() + seconds
    prefix = prefix.encode()
    fragment = b''
    discard = False
    with Path(log).open('rb') as source:
        while time.monotonic() < deadline:
            chunk = source.readline(8192)
            if chunk:
                if not discard:
                    fragment += chunk
                    if fragment.startswith(prefix):
                        return True
                    if not prefix.startswith(fragment):
                        fragment = b''
                        discard = True
                if chunk.endswith(b'\n'):
                    fragment = b''
                    discard = False
            else:
                if child.poll() is not None:
                    return False
                time.sleep(min(0.1, max(0, deadline - time.monotonic())))
    return False


def terminate_command(child):
    if child.poll() is not None:
        return
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        child.wait()
        return
    try:
        child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait()


def wait_for_command(child, seconds, command):
    try:
        return child.wait(timeout=seconds)
    except subprocess.TimeoutExpired:
        print(f"Command exceeded {seconds}s; stopping process group: {command[0]}", file=sys.stderr)
        terminate_command(child)
        return 124


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, help="Write full child output directly to this file")
    parser.add_argument('--startup-seconds', type=int, help='Separate bounded initialization from the execution budget')
    parser.add_argument('--ready-prefix', help='Literal log-line prefix marking initialization complete')
    parser.add_argument("seconds", type=int)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.seconds <= 0 or not args.command:
        parser.error("A positive timeout and command are required")
    if args.startup_seconds is not None or args.ready_prefix is not None:
        if not args.log or not args.ready_prefix or '\n' in args.ready_prefix or args.startup_seconds is None or args.startup_seconds <= 0:
            parser.error('Startup monitoring requires --log, --ready-prefix and positive --startup-seconds')
    raise SystemExit(run(args.seconds, args.command, args.log, args.startup_seconds, args.ready_prefix))
