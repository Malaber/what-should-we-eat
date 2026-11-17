"""Validate export of the exact scenes captured by the normal native suite."""
import json
from pathlib import Path
import pytest
from PIL import Image, ImageOps
from execution import marketing_screenshots as capture

SCENES = ['01-recipe-book', '02-cooking-companion', '03-flexible-portions', '04-every-tap-remembered']


@pytest.fixture
def export_fixture(monkeypatch, tmp_path):
    result = tmp_path/'passed.xcresult'; result.mkdir()
    output = tmp_path/'output'
    state = {'scenes': list(SCENES), 'size': (1206, 2622), 'rendered': [],
             'summary': {'result': 'Passed', 'passedTests': 19, 'failedTests': 0, 'skippedTests': 0}}
    monkeypatch.setattr(capture.subprocess, 'check_output', lambda *args, **kwargs: json.dumps(state['summary']))
    def export(command, **kwargs):
        assert command[:4] == ['xcrun', 'xcresulttool', 'export', 'attachments']
        assert command[command.index('--path')+1] == str(result)
        attachments = Path(command[command.index('--output-path')+1]); attachments.mkdir()
        entries = []
        for i, scene in enumerate(state['scenes']):
            filename = f'{i}.png'
            Image.new('RGB', state['size'], (90+i, 20, 40)).save(attachments/filename)
            if state.get('corrupt') and i == 0:
                data = (attachments/filename).read_bytes()
                (attachments/filename).write_bytes(data[:35])
            entries.append({'suggestedHumanReadableName': f'marketing-{scene}_0_UUID.png', 'exportedFileName': filename})
        for angle, size in state.get('duo_displays', {}).items():
            filename = f'display-{angle}.png'
            Image.new('RGB', size, 'blue').save(attachments/filename)
            entries.append({'suggestedHumanReadableName': f'Duo-workspace-{angle}_0_UUID.png',
                            'exportedFileName': filename, 'timestamp': 1})
        (attachments/'manifest.json').write_text(json.dumps([{'attachments': entries}]))
    monkeypatch.setattr(capture.subprocess, 'run', export)
    monkeypatch.setattr(capture, 'render_capture', lambda *args: state['rendered'].append(args))
    return result, output, state


@pytest.mark.parametrize('family,size', [('iphone', (1206, 2622)), ('ipad', (2064, 2752))])
def test_exports_four_original_scenes_without_starting_tests(export_fixture, family, size):
    result, output, state = export_fixture; state['size'] = size
    capture.export_captures(result, output, family, True)
    assert sorted(p.stem for p in (output/'en-US').glob('*.png')) == sorted(SCENES)
    for i, scene in enumerate(SCENES):
        assert (output/'en-US'/f'{scene}.png').read_bytes() == (output/'attachments'/f'{i}.png').read_bytes()
    assert state['rendered'] == [(output/'en-US', family, True)]


@pytest.mark.parametrize('scenes', [SCENES[:3], SCENES+[SCENES[0]], SCENES+['invented-scene']])
def test_missing_duplicate_or_unknown_scene_cannot_render(export_fixture, scenes):
    result, output, state = export_fixture; state['scenes'] = scenes
    with pytest.raises(ValueError): capture.export_captures(result, output, 'iphone')
    assert state['rendered'] == []
    assert not (output/'en-US').exists()


def test_rejects_wrong_device_dimensions(export_fixture):
    result, output, state = export_fixture
    with pytest.raises(ValueError): capture.export_captures(result, output, 'ipad')
    assert state['rendered'] == []


def test_rejects_png_that_cannot_decode_completely(export_fixture):
    result, output, state = export_fixture; state['corrupt'] = True
    with pytest.raises((OSError, ValueError)): capture.export_captures(result, output, 'iphone')
    assert state['rendered'] == []


def test_existing_output_is_preserved(export_fixture):
    result, output, state = export_fixture
    output.mkdir(); (output/'keep.txt').write_text('existing')
    with pytest.raises(FileExistsError): capture.export_captures(result, output, 'iphone')
    assert (output/'keep.txt').read_text() == 'existing'


def test_exports_both_duo_displays_at_native_upload_sizes(tmp_path):
    exported = tmp_path / "attachments"
    exported.mkdir()
    outer = Image.new("RGB", (1398, 2034), "green")
    outer.save(exported / "outer.png")
    inner = Image.new("RGB", (2006, 2852), "blue")
    inner.putpixel((0, 0), (255, 0, 0))
    exif = inner.getexif()
    exif[274] = 6
    inner.save(exported / "inner.png", exif=exif)
    Image.new("RGB", (2, 2)).save(exported / "old.png")
    manifest = [{"attachments": [
        {"suggestedHumanReadableName": "Duo-workspace-0_0_UUID.png", "exportedFileName": "outer.png", "timestamp": 1},
        {"suggestedHumanReadableName": "Duo-workspace-180_0_UUID.png", "exportedFileName": "inner.png", "timestamp": 3},
        {"suggestedHumanReadableName": "Duo-workspace-180_0_UUID.png", "exportedFileName": "old.png", "timestamp": 2},
        {"suggestedHumanReadableName": "Duo-workspace-90_0_UUID.png", "exportedFileName": "old.png", "timestamp": 4},
    ]}]
    capture.export_duo_captures(manifest, exported, tmp_path)
    result = tmp_path / "en-US"
    with Image.open(result / "01-duo-outer-cooking.png") as actual:
        assert actual.size == (1398, 2034) and actual.mode == "RGB"
        assert actual.tobytes() == outer.tobytes()
    with Image.open(result / "02-duo-inner-cooking.png") as actual:
        assert actual.size == (2853, 2007) and actual.mode == "RGB"
        assert actual.getexif().get(274, 1) == 1
        assert actual.crop((0, 0, 2852, 2006)).tobytes() == ImageOps.exif_transpose(inner).tobytes()
        assert actual.getpixel((2852, 2006)) == actual.getpixel((2851, 2005))


def test_duo_cannot_publish_with_only_one_display(tmp_path):
    manifest = [{"attachments": [{"suggestedHumanReadableName": "Duo-workspace-0.png"}]}]
    with pytest.raises(ValueError, match="outer and inner"):
        capture.export_duo_captures(manifest, tmp_path, tmp_path)


def test_duo_release_uses_one_passing_marketing_result(export_fixture):
    result, output, state = export_fixture
    state['size'] = capture.DUO_CAPTURES[0][1]
    state['duo_displays'] = {angle: size for angle, (_, size) in capture.DUO_CAPTURES.items()}
    capture.export_captures(result, output, 'duo', True, result)
    captures = output/'en-US'
    assert sorted(p.stem for p in captures.glob('*.png')) == sorted(SCENES)
    name, size = capture.DUO_CAPTURES[180]
    with Image.open(captures/'inner'/name) as inner:
        assert inner.size == size
    assert state['rendered'] == [(captures, 'duo', True)]


@pytest.mark.parametrize('summary', [
    {'result': 'Failed', 'passedTests': 18, 'failedTests': 1, 'skippedTests': 0},
    {'result': 'Passed', 'passedTests': 18, 'failedTests': 0, 'skippedTests': 1},
    {'result': 'Passed', 'passedTests': 0, 'failedTests': 0, 'skippedTests': 0},
])
def test_failed_skipped_or_empty_suite_cannot_publish(export_fixture, summary):
    result, output, state = export_fixture; state['summary'] = summary
    with pytest.raises(ValueError, match='passing native result'):
        capture.export_captures(result, output, 'iphone')
    assert not output.exists()
    assert state['rendered'] == []
