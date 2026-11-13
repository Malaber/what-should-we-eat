"""Verify a frozen commit on both local UI profiles; optionally publish that commit."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

PROFILES = (
    ("iphone", "com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro"),
    ("ipad", "com.apple.CoreSimulator.SimDeviceType.iPad-Pro-13-inch-M5-16GB"),
)


def git(repo, *arguments):
    return subprocess.check_output(["git", *arguments], cwd=repo, text=True).strip()


def validate_source(repo, commit, branch=None):
    if git(repo, "rev-parse", "HEAD") != commit:
        raise RuntimeError("Source HEAD changed; the tested candidate was not published.")
    if branch and git(repo, "branch", "--show-current") != branch:
        raise RuntimeError("Source branch changed; the tested candidate was not published.")
    if git(repo, "status", "--porcelain=v1"):
        raise RuntimeError("Source has uncommitted changes; the tested candidate was not published.")


def verify(repo, commit, output, derived_data, push_branch=None):
    if push_branch and not push_branch.startswith("codex/"):
        raise ValueError("This runner only publishes codex/ development branches.")
    output.mkdir(parents=True, exist_ok=False)
    source = output / "source"
    status = {"pid": os.getpid(), "commit": commit, "status": "preparing", "profiles": {},
              "published": False, "source": str(source),
              "started_at": datetime.now(timezone.utc).isoformat()}

    def save():
        temporary = output / "status.new"
        temporary.write_text(json.dumps(status, indent=2) + "\n")
        temporary.replace(output / "status.json")

    save()
    try:
        validate_source(repo, commit, push_branch)
        subprocess.run(["git", "worktree", "add", "--detach", str(source), commit], cwd=repo, check=True)
        for name, device in PROFILES:
            status["status"] = "testing"
            status["profile"] = name
            results = output / name
            results.mkdir()
            status["profiles"][name] = {"status": "running", "results": str(results)}
            save()
            print(f"Running full {name} suite for {commit}", flush=True)
            environment = {**os.environ, "SIMULATOR_DEVICE_TYPE": device, "SIMULATOR_RUNTIME": "27.0",
                           "TEST_RESULTS_DIR": str(results), "TEST_DERIVED_DATA_DIR": str(derived_data)}
            # Always own a fresh simulator. A caller's shell must not accidentally
            # turn both profiles into tests against its existing device.
            environment.pop("SIMULATOR_ID", None)
            with (results / "profile.log").open("w") as log:
                result = subprocess.run(["bash", str(source / "ios/Onionary/Scripts/test.sh")],
                                        cwd=source, env=environment, stdout=log, stderr=subprocess.STDOUT)
            status["profiles"][name].update(status="passed" if result.returncode == 0 else "failed",
                                             exit_code=result.returncode)
            save()
            result.check_returncode()
        if push_branch:
            validate_source(repo, commit, push_branch)
            status["status"] = "publishing"
            save()
            # An immutable SHA, a single explicit development ref and no force.
            subprocess.run(["git", "push", "github", f"{commit}:refs/heads/{push_branch}"], cwd=repo, check=True)
            status["published"] = True
        status["status"] = "passed"
        return_code = 0
    except Exception as error:
        status.update(status="failed", error=str(error))
        return_code = getattr(error, "returncode", 1)
    status["finished_at"] = datetime.now(timezone.utc).isoformat()
    save()
    print(json.dumps(status, indent=2), flush=True)
    return return_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", default="HEAD")
    parser.add_argument("--output", type=Path, default=Path(".tmp/ios-verification"))
    parser.add_argument("--derived-data", type=Path)
    parser.add_argument("--push-branch", help="Optional codex/ branch; only publish after both complete suites pass")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if args.status:
        print((output / "status.json").read_text(), end="")
        return 0
    commit = git(repo, "rev-parse", "--verify", args.commit + "^{commit}")
    derived = args.derived_data.resolve() if args.derived_data else output / "DerivedData"
    return verify(repo, commit, output, derived, args.push_branch)


if __name__ == "__main__":
    raise SystemExit(main())
