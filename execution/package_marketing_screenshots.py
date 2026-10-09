"""Package successful screenshot artifacts for GitHub Releases, excluding test logs."""
import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def package(source: Path, output: Path) -> list[Path]:
    # Validate both devices before producing anything suitable for publishing.
    captures = {}
    for family in ("iphone", "ipad"):
        root = source / f"onionary-appstore-{family}-en-US" / "en-US"
        pngs = sorted(root.glob("*.png"))
        if len(pngs) != 4 or any(p.stat().st_size == 0 for p in pngs):
            raise ValueError(f"Expected four nonempty {family} PNGs in {root}")
        captures[family] = pngs
    output.mkdir(parents=True, exist_ok=True)
    archives = []
    for family, pngs in captures.items():
        target = output / f"onionary-appstore-{family}-en-US.zip"
        with ZipFile(target, "w", ZIP_DEFLATED) as archive:
            for png in pngs:
                archive.write(png, f"en-US/{png.name}")
        archives.append(target)
    return archives


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    for archive in package(args.source, args.output):
        print(archive)
