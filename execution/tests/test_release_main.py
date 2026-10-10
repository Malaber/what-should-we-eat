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
