import pytest
from execution.check_ios_build_environment import MIN_FREE_BYTES, validate_disk, validate_xcode, validate_test_scheme
import xml.etree.ElementTree as ET


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


def scheme():
    return ET.fromstring('''<Scheme><TestAction preferredScreenCaptureFormat="screenshots"
        disableAutomaticScreenCaptures="NO"><Testables><TestableReference skipped="NO">
        <BuildableReference BlueprintName="OnionaryUITests" />
        </TestableReference></Testables></TestAction></Scheme>''')


def test_generated_scheme_keeps_screenshots_and_full_ui_target(tmp_path):
    path = tmp_path / 'Onionary.xcscheme'
    ET.ElementTree(scheme()).write(path)
    validate_test_scheme(path)


def test_xcodegen_omitted_default_still_keeps_automatic_screenshots(tmp_path):
    root = scheme(); del root.find('TestAction').attrib['disableAutomaticScreenCaptures']
    path = tmp_path / 'Onionary.xcscheme'; ET.ElementTree(root).write(path)
    validate_test_scheme(path)


@pytest.mark.parametrize('change', ['video', 'missing-mode', 'disabled-captures', 'missing-target',
                                  'skipped-target', 'duplicate-target', 'skipped-case', 'selected-cases'])
def test_generated_scheme_rejects_recording_drift_or_lost_coverage(tmp_path, change):
    root = scheme(); action = root.find('TestAction')
    target = action.find('Testables/TestableReference')
    if change == 'video': action.set('preferredScreenCaptureFormat', 'screenRecording')
    elif change == 'missing-mode': del action.attrib['preferredScreenCaptureFormat']
    elif change == 'disabled-captures': action.set('disableAutomaticScreenCaptures', 'YES')
    elif change == 'missing-target': action.remove(action.find('Testables'))
    elif change == 'skipped-target': target.set('skipped', 'YES')
    elif change == 'duplicate-target': action.find('Testables').append(ET.fromstring(ET.tostring(target)))
    else:
        selection = ET.SubElement(target, 'SkippedTests' if change == 'skipped-case' else 'SelectedTests')
        ET.SubElement(selection, 'Test', Identifier='OnionaryUITests/testExample')
    path = tmp_path / 'Onionary.xcscheme'; ET.ElementTree(root).write(path)
    with pytest.raises(ValueError): validate_test_scheme(path)
