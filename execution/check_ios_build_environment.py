"""Fail before expensive iOS work when Xcode or disk cannot support the build."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

EXPECTED_XCODE = "Xcode 27.1\nBuild version 27A9275"
MIN_FREE_BYTES = 12 * 1024 ** 3
STAGE_GIB = {"release": 12, "test": 8, "archive": 6}


def validate_xcode(output):
    if output.strip() != EXPECTED_XCODE:
        raise ValueError(f"Expected {EXPECTED_XCODE!r}; found {output.strip()!r}. Use the xcode-27 runner and Xcode_27.1.app.")


def validate_disk(path, free_bytes, minimum_bytes=MIN_FREE_BYTES):
    if free_bytes < minimum_bytes:
        raise ValueError(f"Insufficient space at {path}: {free_bytes / 1024 ** 3:.1f} GiB free; at least {minimum_bytes / 1024 ** 3:g} GiB required. Free disk space before restarting. No files were deleted.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xcode-only', action='store_true')
    parser.add_argument('--stage', choices=STAGE_GIB, default='release')
    args = parser.parse_args()
    try:
        validate_xcode(subprocess.check_output(['xcodebuild', '-version'], text=True))
        if not args.xcode_only:
            for path in (Path(__file__).resolve().parents[1], Path(tempfile.gettempdir())):
                validate_disk(path, shutil.disk_usage(path).free, STAGE_GIB[args.stage] * 1024 ** 3)
    except ValueError as error:
        raise SystemExit(str(error)) from error


if __name__ == '__main__':
    main()
