import pytest

from execution.package_marketing_screenshots import RELEASE_FAMILIES
from execution.release_main import release_version


def make_release_assets(directory):
    for family in RELEASE_FAMILIES:
        (directory / f'onionary-appstore-{family}-en-US.zip').write_bytes(b'test asset')

def test_main_release_promotes_a_reachable_rc_or_bumps_minor():
    tags = ['v0.4.0', 'v0.6.0-rc.29', 'v0.6.0-rc.30', 'v0.99.0-rc.1']
    assert release_version(tags, reachable_candidates=tags[1:3]) == '0.6.0'
    assert release_version(tags) == '0.5.0'
    assert release_version(tags + ['v0.7.0'], reachable_candidates=tags[1:3]) == '0.8.0'
    assert release_version([]) == '0.2.0'
    assert release_version(tags, 'patch', reachable_candidates=tags[1:3]) == '0.4.1'
    assert release_version(tags, 'major', reachable_candidates=tags[1:3]) == '1.0.0'


def test_release_uses_pr_text_without_shell_and_reuses_tag(monkeypatch, tmp_path):
    import json
    from execution import release_main
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('GITHUB_SHA', 'abc123')
    monkeypatch.setenv('GITHUB_REPOSITORY', 'Malaber/what-should-we-eat')
    monkeypatch.setenv('GITHUB_OUTPUT', str(tmp_path / 'output'))
    calls = []
    def output(args, **kwargs):
        if args[:3] == ['git', 'tag', '--list']: return 'v0.2.0-rc.3\nv0.3.0'
        if args[:3] == ['git', 'tag', '--points-at']: return 'v0.3.0'
        if args[:2] == ['git', 'rev-parse']: return 'abc123'
        return json.dumps([{'merged_at':'today', 'base':{'ref':'main'}, 'merge_commit_sha':'abc123',
                           'title':'Keep `literal` $(text)', 'body':'Notes\n\nSecond paragraph',
                           'html_url':'https://github.com/Malaber/what-should-we-eat/pull/4'}])
    def run(args, **kwargs):
        from types import SimpleNamespace
        assert 'shell' not in kwargs
        calls.append(args)
        return SimpleNamespace(returncode=1 if args[:3] == ['gh','release','view'] else 0)
    monkeypatch.setattr(release_main.subprocess, 'check_output', output)
    monkeypatch.setattr(release_main.subprocess, 'run', run)
    release_main.prepare_release()
    assert not calls
    make_release_assets(tmp_path)
    release_main.publish_release(tmp_path)
    create = next(c for c in calls if c[:3] == ['gh','release','create'])
    assert create[create.index('--title') + 1] == 'Keep `literal` $(text)'
    assert [arg for arg in create if arg.endswith('.zip')] == [
        str(tmp_path / f'onionary-appstore-{family}-en-US.zip') for family in RELEASE_FAMILIES
    ]
    assert (tmp_path/'release-notes.md').read_text().startswith('Notes\n\nSecond paragraph')
    assert 'tag=v0.3.0' in (tmp_path/'output').read_text()


def test_first_stable_release_publishes_new_tag_and_preserves_it(monkeypatch, tmp_path):
    """Exercise real Git creation/push, mocking only the external GitHub release API."""
    import json
    import subprocess
    from types import SimpleNamespace
    from execution import release_main

    real_run = subprocess.run
    real_output = subprocess.check_output
    remote = tmp_path / 'remote.git'
    repo = tmp_path / 'repo'
    real_run(['git', 'init', '--bare', str(remote)], check=True, capture_output=True)
    real_run(['git', 'init', '-b', 'candidate', str(repo)], check=True, capture_output=True)
    monkeypatch.chdir(repo)

    def git(*args):
        return real_output(['git', *args], text=True).strip()

    git('config', 'user.email', 'ci@example.org')
    git('config', 'user.name', 'CI test')
    git('commit', '--allow-empty', '-m', 'unrelated candidate')
    git('tag', 'v0.30.0-rc.1')
    git('switch', '--orphan', 'main')
    git('commit', '--allow-empty', '-m', 'merged feature')
    git('remote', 'add', 'origin', str(remote))
    git('tag', 'v0.6.0-rc.7')
    sha = git('rev-parse', 'HEAD')
    monkeypatch.setenv('GITHUB_SHA', sha)
    monkeypatch.setenv('GITHUB_REPOSITORY', 'Malaber/what-should-we-eat')
    monkeypatch.setenv('GITHUB_OUTPUT', str(tmp_path / 'output'))
    published = set()
    creates = []

    def output(args, **kwargs):
        if args[:2] == ['gh', 'api']:
            return json.dumps([{'merged_at': 'today', 'base': {'ref': 'main'},
                               'merge_commit_sha': sha, 'title': 'Cooking and widgets',
                               'body': 'Recipe discovery\n\nValidated changes.',
                               'html_url': 'https://github.com/Malaber/what-should-we-eat/pull/4'}])
        return real_output(args, **kwargs)

    def run(args, **kwargs):
        if args[:3] == ['gh', 'release', 'view']:
            assets = [{'name': path.name} for path in tmp_path.glob('*.zip')]
            return SimpleNamespace(returncode=0 if args[3] in published else 1,
                                   stdout=json.dumps({'isDraft': False, 'assets': assets}))
        if args[:3] == ['gh', 'release', 'create']:
            creates.append(args)
            published.add(args[3])
            return SimpleNamespace(returncode=0)
        return real_run(args, **kwargs)

    monkeypatch.setattr(release_main.subprocess, 'check_output', output)
    monkeypatch.setattr(release_main.subprocess, 'run', run)
    release_main.prepare_release()
    assert git('ls-remote', 'origin', 'refs/tags/v0.6.0').split()[0] == sha
    assert not creates
    with pytest.raises(ValueError, match='Missing release asset'):
        release_main.publish_release(tmp_path)
    assert not creates
    make_release_assets(tmp_path)
    release_main.publish_release(tmp_path)
    assert creates[0][3] == 'v0.6.0'
    assert creates[0][creates[0].index('--title') + 1] == 'Cooking and widgets'
    assert '--verify-tag' in creates[0]
    assert (repo / 'release-notes.md').read_text().startswith('Recipe discovery\n\nValidated changes.')
    release_main.prepare_release()
    release_main.publish_release(tmp_path)
    assert len(creates) == 1
    assert git('ls-remote', 'origin', 'refs/tags/v0.6.0').split()[0] == sha


def test_release_resumes_draft_with_only_missing_assets(monkeypatch, tmp_path):
    import json
    from types import SimpleNamespace
    from execution import release_main

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('GITHUB_SHA', 'tested-sha')
    release_main.RELEASE_PLAN.write_text(json.dumps({'tag': 'v0.8.0', 'title': 'Test'}))
    make_release_assets(tmp_path)
    monkeypatch.setattr(release_main, 'git', lambda *args: 'tested-sha')
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        if command[2] == 'view':
            assets = [{'name': f'onionary-appstore-{family}-en-US.zip'} for family in RELEASE_FAMILIES[:-1]]
            return SimpleNamespace(returncode=0, stdout=json.dumps({'assets': assets, 'isDraft': True}))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(release_main.subprocess, 'run', run)
    release_main.publish_release(tmp_path)
    assert calls[1:] == [
        ['gh', 'release', 'upload', 'v0.8.0', str(tmp_path / 'onionary-appstore-creative-en-US.zip')],
        ['gh', 'release', 'edit', 'v0.8.0', '--draft=false'],
    ]
