import pytest
from execution.check_ios_build_environment import MIN_FREE_BYTES, validate_disk, validate_xcode


def test_xcode_matches_version_and_build():
    validate_xcode('Xcode 27.1\nBuild version 27A9275\n')
    for output in ['Xcode 26.6\nBuild version 17F113', 'Xcode 27.1\nBuild version other']:
        with pytest.raises(ValueError, match='xcode-27 runner'):
            validate_xcode(output)


def test_disk_guard_accepts_boundary_and_rejects_insufficient_space():
    validate_disk('/build', MIN_FREE_BYTES)
    with pytest.raises(ValueError, match='Free disk space before restarting'):
        validate_disk('/build', MIN_FREE_BYTES - 1)
