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


@pytest.mark.parametrize('stage,gib', [('release', 8), ('test', 8), ('archive', 6)])
def test_stage_reserves_allow_sequential_profiles_without_requiring_initial_space(stage, gib):
    from execution.check_ios_build_environment import STAGE_GIB
    reserve = STAGE_GIB[stage] * 1024 ** 3
    assert reserve == gib * 1024 ** 3
    validate_disk('/build', reserve, reserve)
    with pytest.raises(ValueError, match='Insufficient space'):
        validate_disk('/build', reserve - 1, reserve)


def test_reported_available_space_can_start_sequential_release():
    # Finder's decimal GB must not be compared directly with binary GiB.
    validate_disk('/build', 12_530_000_000)
    with pytest.raises(ValueError, match='Insufficient space'):
        validate_disk('/build', 8 * 1024 ** 3 - 1)
