from execution.release_main import release_version

def test_main_release_promotes_rc_and_bumps_minor():
    assert release_version(['v0.2.0-rc.1', 'v0.2.0-rc.3']) == '0.3.0'
    assert release_version(['v0.3.0', 'v0.2.0-rc.3']) == '0.4.0'
    assert release_version([]) == '0.2.0'
    assert release_version(['junk', 'v0.3.0'], 'patch') == '0.3.1'
    assert release_version(['v0.3.0'], 'major') == '1.0.0'
