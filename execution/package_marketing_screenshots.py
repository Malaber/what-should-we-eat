"""Package successful screenshot artifacts for GitHub Releases, excluding test logs."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

CAPTURES = (
    "01-recipe-book.png", "02-cooking-companion.png",
    "03-flexible-portions.png", "04-every-tap-remembered.png",
)
PORTRAITS = (
    "05-cooking-with-onionary.png", "06-your-recipe-book.png", "07-make-it-your-size.png",
)
PORTRAIT_SOURCES = dict(zip(PORTRAITS, (CAPTURES[1], CAPTURES[0], CAPTURES[2]), strict=True))


def validate_dimensions(path: Path, family: str):
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError(f"Invalid PNG: {path}")
    size = struct.unpack(">II", data[16:24])
    allowed = {"iphone": {(1179, 2556), (1206, 2622)},
               "ipad": {(2064, 2752), (2048, 2732)}}
    if size not in allowed[family]:
        raise ValueError(f"Wrong {family} App Store dimensions {size}: {path}")


def validate_bundle(root: Path, family: str) -> list[Path]:
    raw = [root / name for name in CAPTURES]
    portraits = [root / "portraits" / name for name in PORTRAITS]
    if any(not p.is_file() or p.stat().st_size == 0 for p in raw + portraits):
        raise ValueError(f"Expected four raw and three marketing {family} PNGs in {root}")
    from PIL import Image
    pngs = raw + portraits
    for png in pngs:
        validate_dimensions(png, family)
        with Image.open(png) as decoded:
            decoded.load()
            if png in portraits and decoded.mode != "RGB":
                raise ValueError(f"Invalid opaque RGB portrait: {png}")
    creative = root / "creative"
    for name, size in {"header.png": (5244, 2950), "search-results.png": (5244, 2950)}.items():
        image = creative / name
        data = image.read_bytes()
        if (data[:8] != b"\x89PNG\r\n\x1a\n" or len(data) < 26
                or struct.unpack(">II", data[16:24]) != size or data[25] != 2):
            raise ValueError(f"Invalid opaque RGB creative: {image}")
        with Image.open(image) as decoded:
            decoded.load()
            if decoded.mode != "RGB":
                raise ValueError(f"Invalid opaque RGB creative: {image}")
        pngs.append(image)
        pngs.append(creative / name.replace(".png", ".svg"))
    manifest = json.loads((creative / "manifest.json").read_text())
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in raw}
    if (manifest["family"] != family or manifest["captures"] != hashes
            or manifest["portrait_sources"] != PORTRAIT_SOURCES
            or manifest["source"] != CAPTURES[1] or manifest["source_sha256"] != hashes[CAPTURES[1]]):
        raise ValueError("Marketing artwork does not match the current capture")
    if manifest['portrait_sha256'] != {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in portraits}:
        raise ValueError("Marketing portrait does not match the rendered output")
    pngs.extend(creative / f"{name}-safe-area-preview.png" for name in ("header", "search-results"))
    for name in ("header", "search-results"):
        preview = creative / f"{name}-safe-area-preview.png"
        with Image.open(preview) as decoded:
            decoded.load()
            if decoded.mode != "RGB" or decoded.size != (1402, 962):
                raise ValueError(f"Invalid Apple safe-area preview: {preview}")
        if not (creative / f"{name}.svg").is_file():
            raise ValueError(f"Missing editable {name} artwork")
    return pngs


def package(source: Path, output: Path) -> list[Path]:
    # Validate both devices before producing anything suitable for publishing.
    captures = {}
    for family in ("iphone", "ipad"):
        root = source / f"onionary-appstore-{family}-en-US" / "en-US"
        captures[family] = (root, validate_bundle(root, family))
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
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument("--validate-family", choices=["iphone", "ipad"])
    args = parser.parse_args()
    if args.validate_family:
        validate_bundle(args.source, args.validate_family)
    else:
        if args.output is None:
            parser.error("output is required when packaging")
        for archive in package(args.source, args.output):
            print(archive)
