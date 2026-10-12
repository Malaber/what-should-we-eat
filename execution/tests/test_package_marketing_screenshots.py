import hashlib
from zipfile import ZipFile

from PIL import Image
import pytest

from execution.package_marketing_screenshots import package, validate_dimensions
from execution.render_marketing_assets import render, CREATIVE_SIZES


def fixture(root, family):
    root.mkdir(parents=True)
    size = (1206, 2622) if family == 'iphone' else (2064, 2752)
    for name in ('01-recipe-book', '02-cooking-companion', '03-flexible-portions', '04-every-tap-remembered'):
        Image.new('RGB', size, '#eebbaa').save(root / f'{name}.png')
    return root


def test_render_and_package_current_captures(tmp_path):
    for family in ('iphone', 'ipad'):
        root = fixture(tmp_path / f'onionary-appstore-{family}-en-US/en-US', family)
        source = root / '02-cooking-companion.png'
        before = hashlib.sha256(source.read_bytes()).hexdigest()
        outputs = render(root, family)
        assert hashlib.sha256(source.read_bytes()).hexdigest() == before
        assert len(outputs) == 3
        for output in outputs:
            with Image.open(output) as image:
                assert image.mode == 'RGB'
                assert image.info['icc_profile']
                if output.name in CREATIVE_SIZES:
                    assert image.size == CREATIVE_SIZES[output.name]
                else:
                    validate_dimensions(output, family)
        (root.parent / 'private-test-log.txt').write_text('exclude')
    archives = package(tmp_path, tmp_path / 'output')
    assert len(archives) == 2
    for archive in archives:
        with ZipFile(archive) as zipped:
            names = zipped.namelist()
            assert len(names) == 7
            assert 'en-US/creative/header.png' in names
            assert 'en-US/creative/search-results.png' in names
            assert 'en-US/05-cooking-with-onionary.png' in names
            assert all(name.endswith('.png') for name in names)
    # A later capture must not accidentally ship with earlier artwork.
    source = tmp_path / 'onionary-appstore-iphone-en-US/en-US/02-cooking-companion.png'
    Image.new('RGB', (1206, 2622), 'blue').save(source)
    with pytest.raises(ValueError, match='current capture'):
        package(tmp_path, tmp_path / 'stale')
    assert not (tmp_path / 'stale').exists()
    Image.new('RGB', (1206, 2622), '#eebbaa').save(source)
    header = source.parent / 'creative/header.png'
    Image.new('RGBA', (3840, 1646), (255, 255, 255, 0)).save(header)
    with pytest.raises(ValueError, match='opaque RGB'):
        package(tmp_path, tmp_path / 'transparent')
    assert not (tmp_path / 'transparent').exists()


def test_partial_capture_cannot_be_published(tmp_path):
    with pytest.raises(ValueError, match='five nonempty'):
        package(tmp_path, tmp_path / 'output')
    assert not (tmp_path / 'output').exists()


def test_renderer_rejects_missing_or_ambiguous_source(tmp_path):
    with pytest.raises(ValueError, match='exactly one'):
        render(tmp_path, 'iphone')
    for suffix in ('a', 'b'):
        Image.new('RGB', (1206, 2622)).save(tmp_path / f'02-cooking-companion-{suffix}.png')
    with pytest.raises(ValueError, match='exactly one'):
        render(tmp_path, 'iphone')


def test_pro_max_is_rejected_for_medium_iphone_slot(tmp_path):
    path = tmp_path / 'wrong.png'
    Image.new('RGB', (1320, 2868)).save(path)
    with pytest.raises(ValueError, match='Wrong iphone'):
        validate_dimensions(path, 'iphone')
