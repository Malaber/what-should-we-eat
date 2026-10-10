from pathlib import Path
import struct
from zipfile import ZipFile

import pytest

from execution.package_marketing_screenshots import package


def test_archives_contain_only_pngs_for_each_device(tmp_path):
    for family in ('iphone', 'ipad'):
        root = tmp_path / f'onionary-appstore-{family}-en-US'
        (root / 'en-US').mkdir(parents=True)
        for i in range(4):
            (root / 'en-US' / f'{i}.png').write_bytes(b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + b'IHDR' + struct.pack('>II', *((1206, 2622) if family == 'iphone' else (2064, 2752))))
        (root / 'private-test-log.txt').write_text('exclude')
    archives = package(tmp_path, tmp_path / 'output')
    assert len(archives) == 2
    for archive in archives:
        with ZipFile(archive) as zip_file:
            assert zip_file.namelist() == [f'en-US/{i}.png' for i in range(4)]


def test_partial_capture_cannot_be_published(tmp_path):
    with pytest.raises(ValueError, match='four nonempty'):
        package(tmp_path, tmp_path / 'output')
    assert not (tmp_path / 'output').exists()


def test_pro_max_is_rejected_for_medium_iphone_slot(tmp_path):
    from execution.package_marketing_screenshots import validate_dimensions
    image = tmp_path / 'wrong.png'
    image.write_bytes(b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + b'IHDR' + struct.pack('>II', 1320, 2868))
    with pytest.raises(ValueError, match='Wrong iphone'):
        validate_dimensions(image, 'iphone')
