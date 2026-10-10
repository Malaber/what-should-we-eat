"""Publish a new immutable version tag; never move, replace or delete a tag."""
import argparse
from pathlib import Path
import re
import subprocess


def publish(tag: str, remote: str, root: Path):
    if not re.fullmatch(r"v\d+\.\d+\.\d+(?:-rc\.\d+)?", tag):
        raise ValueError("Use vMAJOR.MINOR.PATCH or vMAJOR.MINOR.PATCH-rc.N")

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()

    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Commit tracked changes before tagging a release.")
    ref = f"refs/tags/{tag}"
    if git("tag", "--list", tag) or git("ls-remote", "--tags", remote, ref):
        raise ValueError(f"{tag} already exists. Choose a new version; never overwrite tags.")
    # Both commands reject an existing tag, including one created concurrently.
    subprocess.run(["git", "tag", tag, "HEAD"], cwd=root, check=True)
    subprocess.run(["git", "push", remote, f"{ref}:{ref}"], cwd=root, check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    parser.add_argument("--remote", default="github")
    args = parser.parse_args()
    publish(args.tag, args.remote, Path(__file__).resolve().parents[1])
