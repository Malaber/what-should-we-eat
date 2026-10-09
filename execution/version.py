"""Versions derive from reachable vMAJOR.MINOR.PATCH tags; no release tag => 0.2.0."""
import argparse
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def version():
    supplied = os.getenv('APP_VERSION')
    if supplied:
        return supplied
    tags = subprocess.run(['git', 'tag', '--merged', 'HEAD', '--list', 'v*'], cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()
    versions = [tuple(map(int, t[1:].split('-')[0].split('.'))) for t in tags if re.fullmatch(r'v\d+\.\d+\.\d+(?:-rc\.\d+)?', t)]
    base = '.'.join(map(str, max(versions))) if versions else '0.2.0'
    exact = subprocess.run(['git', 'tag', '--points-at', 'HEAD'], cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()
    release_tags = [t[1:] for t in exact if re.fullmatch(r'v\d+\.\d+\.\d+(?:-rc\.\d+)?', t)]
    if release_tags:
        return sorted(release_tags)[-1]
    sha = subprocess.check_output(['git', 'rev-parse', '--short=12', 'HEAD'], cwd=ROOT, text=True).strip()
    return f'{base}-dev.{sha}'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ios', action='store_true')
    args = parser.parse_args()
    value = version()
    print(value.split('-')[0] if args.ios else value)
