import pytest
from execution.check_ios_build_environment import MIN_FREE_BYTES, validate_disk, validate_xcode, validate_test_scheme, validate_test_app, select_test_plan
import xml.etree.ElementTree as ET
import plistlib
import struct


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


def make_test_app(tmp_path):
    app = tmp_path / 'Onionary.app'; app.mkdir()
    (app / 'Info.plist').write_bytes(plistlib.dumps({'CFBundleExecutable': 'Onionary'}))
    binary = app / 'Onionary'
    binary.write_bytes(struct.pack('<IIII', 0xFEEDFACF, 0x100000C, 0, 2))
    binary.chmod(0o755)
    return app


def test_headless_app_accepts_normal_executable_layout(tmp_path):
    validate_test_app(make_test_app(tmp_path))


@pytest.mark.parametrize('change', ['debug-dylib', 'preview', 'missing-binary',
                                  'not-executable', 'not-macho', 'not-executable-macho',
                                  'outside-bundle', 'invalid-plist'])
def test_headless_app_rejects_preview_or_invalid_output(tmp_path, change):
    app = make_test_app(tmp_path)
    if change == 'debug-dylib': (app / 'Onionary.debug.dylib').write_bytes(b'debug')
    elif change == 'preview': (app / '__preview.dylib').write_bytes(b'preview')
    elif change == 'missing-binary': (app / 'Onionary').unlink()
    elif change == 'not-executable': (app / 'Onionary').chmod(0o644)
    elif change == 'not-macho': (app / 'Onionary').write_bytes(b'not a valid executable')
    elif change == 'not-executable-macho': (app / 'Onionary').write_bytes(struct.pack('<IIII', 0xFEEDFACF, 0x100000C, 0, 6))
    elif change == 'outside-bundle': (app / 'Info.plist').write_bytes(plistlib.dumps({'CFBundleExecutable': '../Onionary'}))
    elif change == 'invalid-plist': (app / 'Info.plist').write_bytes(b'invalid')
    with pytest.raises((ValueError, plistlib.InvalidFileException)):
        validate_test_app(app)


def make_test_plan(products):
    host = products / 'Debug-iphonesimulator/OnionaryUITests-Runner.app'
    (host / 'PlugIns/OnionaryUITests.xctest').mkdir(parents=True)
    (products / 'Debug-iphonesimulator/Onionary.app').mkdir()
    target = dict(BlueprintName='OnionaryUITests', IsUITestBundle=True,
                  PreferredScreenCaptureFormat='screenshots',
                  TestHostPath='__TESTROOT__/Debug-iphonesimulator/OnionaryUITests-Runner.app',
                  TestBundlePath='__TESTHOST__/PlugIns/OnionaryUITests.xctest',
                  UITargetAppPath='__TESTROOT__/Debug-iphonesimulator/Onionary.app')
    path = products / 'Onionary_iphonesimulator27.1-arm64.xctestrun'
    path.write_bytes(plistlib.dumps({'OnionaryUITests': target, '__xctestrun_metadata__': {'FormatVersion': 1}}))
    return path


def test_selects_complete_compiled_plan_with_existing_products(tmp_path):
    path = make_test_plan(tmp_path)
    assert select_test_plan(tmp_path) == path.resolve()


@pytest.mark.parametrize('change', ['absent', 'ambiguous', 'format', 'wrong-target', 'not-ui',
                                  'video', 'skip', 'only', 'wrong-host', 'missing-bundle'])
def test_compiled_plan_rejects_ambiguity_missing_products_or_lost_coverage(tmp_path, change):
    path = make_test_plan(tmp_path)
    plan = plistlib.loads(path.read_bytes()); target = plan['OnionaryUITests']
    if change == 'absent': path.unlink()
    elif change == 'ambiguous': (tmp_path / 'Onionary_iphonesimulator27.0-arm64.xctestrun').write_bytes(path.read_bytes())
    elif change == 'format': plan['__xctestrun_metadata__']['FormatVersion'] = 2
    elif change == 'wrong-target': plan['OtherUITests'] = plan.pop('OnionaryUITests')
    elif change == 'not-ui': target['IsUITestBundle'] = False
    elif change == 'video': target['PreferredScreenCaptureFormat'] = 'screenRecording'
    elif change == 'skip': target['SkipTestIdentifiers'] = ['OnionaryUITests/testExample']
    elif change == 'only': target['OnlyTestIdentifiers'] = ['OnionaryUITests/testExample']
    elif change == 'wrong-host': target['TestHostPath'] = '__TESTROOT__/Other.app'
    elif change == 'missing-bundle': (tmp_path / 'Debug-iphonesimulator/OnionaryUITests-Runner.app/PlugIns/OnionaryUITests.xctest').rmdir()
    if change not in {'absent', 'ambiguous'}: path.write_bytes(plistlib.dumps(plan))
    with pytest.raises(ValueError): select_test_plan(tmp_path)
