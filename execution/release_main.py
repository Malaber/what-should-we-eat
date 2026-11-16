"""Idempotent stable release metadata for main; PR text is data, never shell code."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

from execution.package_marketing_screenshots import RELEASE_FAMILIES

RELEASE_PLAN = Path('release-plan.json')
RELEASE_NOTES = Path('release-notes.md')


def release_version(tags, bump='minor', *, reachable_candidates=()):
    stable_versions = [tuple(map(int, match.groups())) for tag in tags
                       if (match := re.fullmatch(r'v(\d+)\.(\d+)\.(\d+)', tag))]
    major, minor, patch = max(stable_versions, default=(0, 1, 0))
    if bump == 'major':
        return f'{major + 1}.0.0'
    if bump == 'patch':
        return f'{major}.{minor}.{patch + 1}'
    # An RC already names its intended release. Only an RC included in this
    # merge can influence the result, and a release never regresses the version.
    candidates = [tuple(map(int, match.groups())) for tag in reachable_candidates
                  if (match := re.fullmatch(r'v(\d+)\.(\d+)\.(\d+)-rc\.\d+', tag))]
    target = max([(major, minor + 1, 0), *candidates])
    return '.'.join(map(str, target))


def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()


def prepare_release():
    sha = os.environ['GITHUB_SHA']
    repo = os.environ['GITHUB_REPOSITORY']
    tags = git('tag', '--list', 'v*').splitlines()
    exact = [t for t in git('tag', '--points-at', sha).splitlines() if re.fullmatch(r'v\d+\.\d+\.\d+', t)]
    pulls = json.loads(subprocess.check_output(['gh', 'api', f'repos/{repo}/commits/{sha}/pulls'], text=True))
    merged = [p for p in pulls if p.get('merged_at') and p['base']['ref'] == 'main']
    pr = next((p for p in merged if p.get('merge_commit_sha') == sha), merged[0] if merged else None)
    labels = {label['name'] for label in pr.get('labels', [])} if pr else set()
    bump = 'major' if 'release:major' in labels else 'patch' if 'release:patch' in labels else 'minor'
    reachable_candidates = git('tag', '--merged', sha, '--list', 'v*-rc.*').splitlines()
    tag = exact[0] if exact else 'v' + release_version(tags, bump, reachable_candidates=reachable_candidates)
    title = pr['title'] if pr else git('show', '-s', '--format=%s', sha)
    notes = (pr.get('body') or '') if pr else f'Main commit {sha}.'
    if pr: notes += f"\n\nSource: {pr['html_url']}\n"
    RELEASE_NOTES.write_text(notes, encoding='utf-8')
    # Create only after callers have passed all build/test gates. Re-runs reuse the tag.
    if not exact:
        subprocess.run(['git', 'tag', tag, sha], check=True)
        subprocess.run(['git', 'push', 'origin', tag], check=True)
    RELEASE_PLAN.write_text(json.dumps({'tag': tag, 'title': title}), encoding='utf-8')
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
        output.write(f'tag={tag}\nversion={tag[1:]}\n')


def publish_release(directory):
    plan = json.loads(RELEASE_PLAN.read_text(encoding='utf-8'))
    tag = plan['tag']
    if git('rev-parse', f'refs/tags/{tag}^{{commit}}') != os.environ['GITHUB_SHA']:
        raise ValueError(f'Release tag {tag} does not point to the tested main commit')
    assets = [directory / f'onionary-appstore-{family}-en-US.zip' for family in RELEASE_FAMILIES]
    for asset in assets:
        if not asset.is_file() or not asset.stat().st_size:
            raise ValueError(f'Missing release asset: {asset}')
    result = subprocess.run(['gh', 'release', 'view', tag, '--json', 'assets,isDraft'],
                            capture_output=True, text=True)
    if result.returncode:
        # With assets attached, gh creates a draft and publishes it only after upload.
        subprocess.run(['gh', 'release', 'create', tag, *map(str, assets), '--verify-tag',
                        '--title', plan['title'], '--notes-file', str(RELEASE_NOTES)], check=True)
        return
    release = json.loads(result.stdout)
    attached = {asset['name'] for asset in release['assets']}
    missing = [str(asset) for asset in assets if asset.name not in attached]
    if missing:
        subprocess.run(['gh', 'release', 'upload', tag, *missing], check=True)
    if release['isDraft']:
        subprocess.run(['gh', 'release', 'edit', tag, '--draft=false'], check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish-assets', type=Path, help='Publish the prepared release with these verified ZIPs')
    args = parser.parse_args()
    if args.publish_assets is None:
        prepare_release()
    else:
        publish_release(args.publish_assets)
