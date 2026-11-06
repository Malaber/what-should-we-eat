"""Fail before expensive iOS work when Xcode or disk cannot support the build."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

EXPECTED_XCODE = "Xcode 27.1\nBuild version 27A9275"
MIN_FREE_BYTES = 15 * 1024 ** 3


def validate_xcode(output):
    if output.strip() != EXPECTED_XCODE:
        raise ValueError(f"Expected {EXPECTED_XCODE!r}; found {output.strip()!r}. Use the xcode-27 runner and Xcode_27.1.app.")


def validate_disk(path, free_bytes):
    if free_bytes < MIN_FREE_BYTES:
        raise ValueError(f"Insufficient space at {path}: {free_bytes / 1024 ** 3:.1f} GiB free; at least 15 GiB required. Free disk space before restarting. No files were deleted.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xcode-only', action='store_true')
    args = parser.parse_args()
    try:
        validate_xcode(subprocess.check_output(['xcodebuild', '-version'], text=True))
        if not args.xcode_only:
            for path in (Path(__file__).resolve().parents[1], Path(tempfile.gettempdir())):
                validate_disk(path, shutil.disk_usage(path).free)
    except ValueError as error:
        raise SystemExit(str(error)) from error


if __name__ == '__main__':
    main()
