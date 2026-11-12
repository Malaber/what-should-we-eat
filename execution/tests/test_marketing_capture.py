"""Validate export of the exact scenes captured by the normal native suite."""
import json
from pathlib import Path
import pytest
from PIL import Image
from execution import marketing_screenshots as capture

SCENES = ['01-recipe-book', '02-cooking-companion', '03-flexible-portions', '04-every-tap-remembered']


@pytest.fixture
def export_fixture(monkeypatch, tmp_path):
    result = tmp_path/'passed.xcresult'; result.mkdir()
    output = tmp_path/'output'
    state = {'scenes': list(SCENES), 'size': (1206, 2622), 'rendered': []}
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
