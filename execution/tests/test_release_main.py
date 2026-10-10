from execution.release_main import release_version

def test_main_release_promotes_rc_and_bumps_minor():
    assert release_version(['v0.2.0-rc.1', 'v0.2.0-rc.3']) == '0.3.0'
    assert release_version(['v0.3.0', 'v0.2.0-rc.3']) == '0.4.0'
    assert release_version([]) == '0.2.0'
    assert release_version(['junk', 'v0.3.0'], 'patch') == '0.3.1'
    assert release_version(['v0.3.0'], 'major') == '1.0.0'


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
    release_main.main()
    assert not any(c[:2] == ['git','push'] for c in calls)
    create = next(c for c in calls if c[:3] == ['gh','release','create'])
    assert create[create.index('--title') + 1] == 'Keep `literal` $(text)'
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
    real_run(['git', 'init', str(repo)], check=True, capture_output=True)
    monkeypatch.chdir(repo)

    def git(*args):
        return real_output(['git', *args], text=True).strip()

    git('config', 'user.email', 'ci@example.org')
    git('config', 'user.name', 'CI test')
    git('commit', '--allow-empty', '-m', 'merged feature')
    git('remote', 'add', 'origin', str(remote))
    git('tag', 'v0.2.0-rc.7')
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
            return SimpleNamespace(returncode=0 if args[3] in published else 1)
        if args[:3] == ['gh', 'release', 'create']:
            creates.append(args)
            published.add(args[3])
            return SimpleNamespace(returncode=0)
        return real_run(args, **kwargs)

    monkeypatch.setattr(release_main.subprocess, 'check_output', output)
    monkeypatch.setattr(release_main.subprocess, 'run', run)
    release_main.main()
    assert git('ls-remote', 'origin', 'refs/tags/v0.3.0').split()[0] == sha
    assert creates[0][3] == 'v0.3.0'
    assert creates[0][creates[0].index('--title') + 1] == 'Cooking and widgets'
    assert '--verify-tag' in creates[0]
    assert (repo / 'release-notes.md').read_text().startswith('Recipe discovery\n\nValidated changes.')
    release_main.main()
    assert len(creates) == 1
    assert git('ls-remote', 'origin', 'refs/tags/v0.3.0').split()[0] == sha
