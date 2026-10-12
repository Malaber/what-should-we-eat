"""Package successful screenshot artifacts for GitHub Releases, excluding test logs."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def validate_dimensions(path: Path, family: str):
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError(f"Invalid PNG: {path}")
    size = struct.unpack(">II", data[16:24])
    allowed = {"iphone": {(1179, 2556), (1206, 2622)},
               "ipad": {(2064, 2752), (2048, 2732)}}
    if size not in allowed[family]:
        raise ValueError(f"Wrong {family} App Store dimensions {size}: {path}")


def package(source: Path, output: Path) -> list[Path]:
    # Validate both devices before producing anything suitable for publishing.
    captures = {}
    for family in ("iphone", "ipad"):
        root = source / f"onionary-appstore-{family}-en-US" / "en-US"
        pngs = sorted(root.glob("*.png"))
        if len(pngs) != 5 or any(p.stat().st_size == 0 for p in pngs):
            raise ValueError(f"Expected five nonempty {family} PNGs in {root}")
        for png in pngs:
            validate_dimensions(png, family)
        creative = root / "creative"
        for name, size in {"header.png": (3840, 1646), "search-results.png": (3000, 2000)}.items():
            image = creative / name
            data = image.read_bytes()
            if (data[:8] != b"\x89PNG\r\n\x1a\n" or len(data) < 26
                    or struct.unpack(">II", data[16:24]) != size or data[25] != 2):
                raise ValueError(f"Invalid opaque RGB creative: {image}")
            pngs.append(image)
        manifest = json.loads((creative / "manifest.json").read_text())
        raw = list(root.glob("02-cooking-companion*.png"))
        if (len(raw) != 1 or manifest["source"] != raw[0].name
                or manifest["source_sha256"] != hashlib.sha256(raw[0].read_bytes()).hexdigest()):
            raise ValueError("Marketing artwork does not match the current capture")
        captures[family] = (root, pngs)
    output.mkdir(parents=True, exist_ok=True)
    archives = []
    for family, (root, pngs) in captures.items():
        target = output / f"onionary-appstore-{family}-en-US.zip"
        with ZipFile(target, "w", ZIP_DEFLATED) as archive:
            for png in pngs:
                archive.write(png, f"en-US/{png.relative_to(root)}")
        archives.append(target)
    return archives


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    for archive in package(args.source, args.output):
        print(archive)
