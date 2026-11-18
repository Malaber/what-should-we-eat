import hashlib
import shutil
from zipfile import ZipFile

from PIL import Image, ImageDraw
import pytest

from execution.marketing_device_frames import prepare_frame
from execution.package_marketing_screenshots import (
    DEVICE_FAMILIES, DUO_CAPTURES, LIVE_ACTIVITY_CAPTURE, LIVE_ACTIVITY_PORTRAIT, package, source_captures, validate_dimensions,
)
from execution.render_marketing_assets import render, CREATIVE_SIZES
from marketing.creative.render import SAFE_AREA, validate_safe_area


def fixture(root, family):
    root.mkdir(parents=True)
    size = {'iphone': (1206, 2622), 'ipad': (2064, 2752), 'duo': (1398, 2034)}[family]
    for name in source_captures(family):
        Image.new('RGB', size, '#eebbaa').save(root / name)
    return root


def test_render_and_package_current_captures(tmp_path, monkeypatch):
    def mock_frame(size):
        from execution.marketing_device_frames import DeviceFrame

        w, h = size
        bezel = Image.new("RGBA", (w + 32, h + 32), "black")
        ImageDraw.Draw(bezel).rectangle((16, 16, w + 15, h + 15), fill=(0, 0, 0, 0))
        return DeviceFrame(bezel, Image.new("L", size, 255), (16, 16))

    monkeypatch.setattr("execution.render_marketing_assets.load_frame", mock_frame)
    monkeypatch.setattr("marketing.creative.render.load_frame", mock_frame)
    for family in DEVICE_FAMILIES:
        root = fixture(tmp_path / f'onionary-appstore-{family}-en-US/en-US', family)
        source = root / '02-cooking-companion.png'
        before = hashlib.sha256(source.read_bytes()).hexdigest()
        outputs = render(root, family, include_creative=family == 'iphone')
        assert hashlib.sha256(source.read_bytes()).hexdigest() == before
        assert len(outputs) == (6 if family == 'iphone' else 3)
        for output in outputs:
            with Image.open(output) as image:
                assert image.mode == 'RGB'
                assert image.info['icc_profile']
                if output.name in CREATIVE_SIZES:
                    assert image.size == CREATIVE_SIZES[output.name]
                else:
                    validate_dimensions(output, family)
        if family == 'iphone':
            for placement in ('header', 'search-results'):
                with Image.open(root / f'creative/{placement}-safe-area-preview.png') as preview:
                    assert preview.size == (SAFE_AREA[2] - SAFE_AREA[0], SAFE_AREA[3] - SAFE_AREA[1])
            creative = tmp_path / 'onionary-appstore-creative-en-US/en-US/creative'
            creative.parent.mkdir(parents=True)
            shutil.move(root / 'creative', creative)
        if family == 'duo':
            (root / 'inner').mkdir()
            name, size = DUO_CAPTURES[180]
            Image.new('RGB', size).save(root / 'inner' / name)
        (root.parent / 'private-test-log.txt').write_text('exclude')
    archives = package(tmp_path, tmp_path / 'output')
    assert [archive.name for archive in archives] == [
        f'onionary-appstore-{family}-en-US.zip' for family in (*DEVICE_FAMILIES, 'creative')
    ]
    for family, archive in zip(DEVICE_FAMILIES, archives[:3], strict=True):
        with ZipFile(archive) as zipped:
            names = zipped.namelist()
            assert len(names) == {'iphone': 9, 'ipad': 7, 'duo': 8}[family]
            assert not any('/creative/' in name for name in names)
            assert 'en-US/portraits/05-cooking-with-onionary.png' in names
            assert 'en-US/portraits/06-your-recipe-book.png' in names
            assert 'en-US/portraits/07-make-it-your-size.png' in names
            assert all(name.endswith('.png') for name in names)
            if family == 'duo':
                assert f'en-US/inner/{DUO_CAPTURES[180][0]}' in names
            if family == 'iphone':
                assert f'en-US/{LIVE_ACTIVITY_CAPTURE}' in names
                assert f'en-US/portraits/{LIVE_ACTIVITY_PORTRAIT}' in names
    with ZipFile(archives[3]) as zipped:
        assert set(zipped.namelist()) == {
            f'en-US/creative/{name}{suffix}'
            for name in ('header', 'search-results')
            for suffix in ('.png', '.svg', '-safe-area-preview.png')
        }
    # A later capture must not accidentally ship with earlier artwork.
    source = tmp_path / 'onionary-appstore-iphone-en-US/en-US/01-recipe-book.png'
    Image.new('RGB', (1206, 2622), 'blue').save(source)
    with pytest.raises(ValueError, match='current capture'):
        package(tmp_path, tmp_path / 'stale')
    assert not (tmp_path / 'stale').exists()
    Image.new('RGB', (1206, 2622), '#eebbaa').save(source)
    header = creative / 'header.png'
    Image.new('RGBA', (3840, 1646), (255, 255, 255, 0)).save(header)
    with pytest.raises(ValueError, match='opaque RGB'):
        package(tmp_path, tmp_path / 'transparent')
    assert not (tmp_path / 'transparent').exists()


def test_partial_capture_cannot_be_published(tmp_path):
    with pytest.raises(ValueError, match='5 raw and 4 marketing'):
        package(tmp_path, tmp_path / 'output')
    assert not (tmp_path / 'output').exists()


def test_renderer_rejects_missing_or_ambiguous_source(tmp_path):
    with pytest.raises(ValueError, match='exactly one'):
        render(tmp_path, 'iphone')
    fixture(tmp_path / 'canonical', 'iphone')
    for suffix in ('a', 'b'):
        Image.new('RGB', (1206, 2622)).save(tmp_path / 'canonical' / f'02-cooking-companion-{suffix}.png')
    with pytest.raises(ValueError, match='exactly one'):
        render(tmp_path / 'canonical', 'iphone')


def test_frame_uses_its_display_aperture_and_keeps_hardware_pixels():
    bezel = Image.new("RGBA", (60, 100))
    draw = ImageDraw.Draw(bezel)
    draw.rounded_rectangle((3, 3, 56, 96), radius=10, fill=(25, 30, 40, 255))
    draw.rounded_rectangle((8, 8, 51, 91), radius=8, fill=(0, 0, 0, 0))
    draw.ellipse((24, 12, 36, 15), fill=(0, 0, 0, 255))
    frame = prepare_frame(bezel)
    assert frame.display_mask.size == (44, 84)
    assert frame.display_origin == (5, 5)
    photo = frame.compose(Image.new("RGB", (44, 84), "white"))
    assert photo.getpixel((0, 0))[3] == 0
    assert photo.getpixel((5, 30)) == (255, 255, 255, 255)
    assert photo.getpixel((1, 30)) == (25, 30, 40, 255)
    assert photo.getpixel((27, 10)) == (0, 0, 0, 255)


def test_critical_artwork_outside_safe_area_is_rejected(tmp_path):
    import shutil

    inkscape = shutil.which('inkscape') or '/Applications/Inkscape.app/Contents/MacOS/inkscape'
    svg = tmp_path / 'bad.svg'
    svg.write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="5244" height="2950">
      <g id="safe-content"><rect x="1900" y="700" width="500" height="400"/></g>
    </svg>''')
    with pytest.raises(ValueError, match='outside Apple'):
        validate_safe_area(inkscape, svg)


def test_pro_max_is_rejected_for_medium_iphone_slot(tmp_path):
    path = tmp_path / 'wrong.png'
    Image.new('RGB', (1320, 2868)).save(path)
    with pytest.raises(ValueError, match='Wrong iphone'):
        validate_dimensions(path, 'iphone')
