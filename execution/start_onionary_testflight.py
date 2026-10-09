#!/usr/bin/env python3
"""Start a detached local build/test/upload and keep a log plus an exit status.

python execution/start_onionary_testflight.py auto 2
python execution/start_onionary_testflight.py --status
Uses the Apple account already configured in Xcode; no secrets in this script.
"""
import argparse
import fcntl
import json
import os
import plistlib
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".tmp/onionary-testflight"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", nargs="?")
    parser.add_argument("build", nargs="?")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--archive", type=Path, help="Retry exporting an existing, already-tested archive")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    status_file = OUTPUT / "status.json"
    if args.status:
        print(status_file.read_text() if status_file.exists() else "No upload has been started.")
        return
    if args.version == "auto":
        args.version = subprocess.check_output(
            [sys.executable, str(ROOT / "execution/version.py"), "--ios"], cwd=ROOT, text=True
        ).strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version or "") or not re.fullmatch(r"[1-9]\d*", args.build or ""):
        parser.error("Provide a version (auto for the Git-tag version, or 0.2.0) and positive build number.")
    if args.archive:
        args.archive = args.archive.resolve()
        try:
            with (args.archive / "Products/Applications/Onionary.app/Info.plist").open("rb") as source:
                info = plistlib.load(source)
            if (info.get("CFBundleIdentifier"), info.get("CFBundleShortVersionString"), str(info.get("CFBundleVersion"))) != ("de.malaber.onionary", args.version, args.build):
                parser.error("Archive bundle ID, version, or build number does not match.")
        except (OSError, ValueError) as error:
            parser.error(f"Cannot read archive: {error}")
    if args.worker:
        with (OUTPUT / "worker.lock").open("w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise SystemExit("Another TestFlight build is already running.")
            state = {"pid": os.getpid(), "version": args.version, "build": args.build, "status": "running",
                     "started_at": datetime.now(timezone.utc).isoformat(), "log": str(OUTPUT / "build.log")}
            status_file.write_text(json.dumps(state, indent=2))
            command = ["bash", str(ROOT / "ios/Onionary/Scripts/upload_testflight.sh"), args.version, args.build]
            if args.archive:
                command.append(str(args.archive))
                state["archive"] = str(args.archive)
                status_file.write_text(json.dumps(state, indent=2))
            result = subprocess.run(command, cwd=ROOT)
            state.update(status="uploaded" if result.returncode == 0 else "failed", exit_code=result.returncode,
                         finished_at=datetime.now(timezone.utc).isoformat())
            status_file.write_text(json.dumps(state, indent=2))
            raise SystemExit(result.returncode)
    with (OUTPUT / "build.log").open("a") as log:
        command = [sys.executable, str(Path(__file__).resolve()), args.version, args.build, "--worker"]
        if args.archive:
            command.extend(["--archive", str(args.archive)])
        child = subprocess.Popen(command,
                                 stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                 start_new_session=True, cwd=ROOT)
    print(f"Started worker {child.pid}. Log: {OUTPUT / 'build.log'}")
    print("Check progress with: python execution/start_onionary_testflight.py --status")


if __name__ == "__main__":
    main()
