"""Idempotent stable release metadata for main; PR text is data, never shell code."""
import json
import os
from pathlib import Path
import re
import subprocess


def release_version(tags, bump='minor'):
    versions = [tuple(map(int, m.groups())) for t in tags
                if (m := re.fullmatch(r'v(\d+)\.(\d+)\.(\d+)(?:-rc\.\d+)?', t))]
    major, minor, patch = max(versions, default=(0, 1, 0))
    if bump == 'major': return f'{major + 1}.0.0'
    if bump == 'patch': return f'{major}.{minor}.{patch + 1}'
    return f'{major}.{minor + 1}.0'


def main():
    sha = os.environ['GITHUB_SHA']
    repo = os.environ['GITHUB_REPOSITORY']
    def git(*args): return subprocess.check_output(['git', *args], text=True).strip()
    tags = git('tag', '--list', 'v*').splitlines()
    exact = [t for t in git('tag', '--points-at', sha).splitlines() if re.fullmatch(r'v\d+\.\d+\.\d+', t)]
    pulls = json.loads(subprocess.check_output(['gh', 'api', f'repos/{repo}/commits/{sha}/pulls'], text=True))
    merged = [p for p in pulls if p.get('merged_at') and p['base']['ref'] == 'main']
    pr = next((p for p in merged if p.get('merge_commit_sha') == sha), merged[0] if merged else None)
    labels = {label['name'] for label in pr.get('labels', [])} if pr else set()
    bump = 'major' if 'release:major' in labels else 'patch' if 'release:patch' in labels else 'minor'
    tag = exact[0] if exact else 'v' + release_version(tags, bump)
    title = pr['title'] if pr else git('show', '-s', '--format=%s', sha)
    notes = (pr.get('body') or '') if pr else f'Main commit {sha}.'
    if pr: notes += f"\n\nSource: {pr['html_url']}\n"
    Path('release-notes.md').write_text(notes, encoding='utf-8')
    # Create only after callers have passed all build/test gates. Re-runs reuse the tag.
    if not exact:
        subprocess.run(['git', 'tag', tag, sha], check=True)
        subprocess.run(['git', 'push', 'origin', tag], check=True)
    exists = subprocess.run(['gh', 'release', 'view', tag], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if not exists:
        subprocess.run(['gh', 'release', 'create', tag, '--verify-tag', '--title', title,
                        '--notes-file', 'release-notes.md'], check=True)
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
        output.write(f'tag={tag}\nversion={tag[1:]}\n')

if __name__ == '__main__': main()
