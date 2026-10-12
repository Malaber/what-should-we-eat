"""Compose marketing artwork around real captures; never invent or stretch app UI."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from execution.package_marketing_screenshots import validate_dimensions

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'marketing'
PLUM = '#59223f'
INK = '#332832'
CREATIVE_SIZES = {'header.png': (3840, 1646), 'search-results.png': (3000, 2000)}


def font(size, serif=False):
    face = ImageFont.truetype(str(ASSETS / 'fonts' / ('Lora.ttf' if serif else 'Manrope.ttf')), round(size))
    face.set_variation_by_axes([500])
    return face


def text(image, xy, lines, size, serif=False, color=PLUM):
    draw = ImageDraw.Draw(image)
    for i, line in enumerate(lines):
        draw.text((round(xy[0]), round(xy[1] + i * size * 1.22)), line, font=font(size, serif), fill=color)


def feather(size):
    # Blend illustration edges into the paper background, retaining its focal point.
    w, h = size
    mask = Image.new('L', size)
    mask.putdata([round(255 * min(1, y / (h*.15)) * min(1, (w-x) / (w*.20)))
                  for y in range(h) for x in range(w)])
    return mask


def device(canvas, screen, box):
    x, y, w, h = box
    fitted = ImageOps.contain(screen, (round(w - 32), round(h - 32)), Image.Resampling.LANCZOS)
    sw, sh = fitted.size
    x, y = round(x + (w - sw) / 2), round(y + (h - sh) / 2)
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((x-17, y-17, x+sw+17, y+sh+17), radius=50, fill='#29242a', outline='#776773', width=4)
    # Preserve the captured UI exactly, including its status bar; round only corners.
    mask = Image.new('L', fitted.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, sw-1, sh-1), radius=35, fill=255)
    canvas.paste(fitted, (x, y), mask)


def render(root: Path, family: str):
    sources = sorted(root.glob('02-cooking-companion*.png'))
    if len(sources) != 1:
        raise ValueError('Expected exactly one current cooking-companion screenshot')
    source = sources[0]
    validate_dimensions(source, family)
    with Image.open(source) as original:
        screen = original.convert('RGB')
    with Image.open(ASSETS / 'assets/onionary-kitchen.png') as original:
        art = original.convert('RGB')
    creative = root / 'creative'
    creative.mkdir(exist_ok=True)
    outputs = []
    for name, size in CREATIVE_SIZES.items():
        w, h = size
        canvas = Image.new('RGB', size, '#fbf2e3')
        decor = ImageOps.contain(art, (round(w*.60), round(h*.52)), Image.Resampling.LANCZOS)
        canvas.paste(decor, (0, h-decor.height), feather(decor.size))
        text(canvas, (w*.065, h*.07), ['ONIONARY'], h*.035)
        text(canvas, (w*.065, h*.16), ['Your recipes.', 'Your rhythm.'], h*.085, serif=True)
        text(canvas, (w*.065, h*.39), ['Scale portions. Cook step by step.'], h*.031, color=INK)
        device(canvas, screen, (w*.64, h*.09, w*.30, h*.82))
        path = creative / name
        canvas.save(path, icc_profile=srgb())
        outputs.append(path)
    w, h = screen.size
    canvas = Image.new('RGB', (w, h), '#fbf2e3')
    decor = ImageOps.fit(art, (w, round(h*.42)), Image.Resampling.LANCZOS)
    canvas.paste(decor, (0, round(h*.58)))
    text(canvas, (w*.08, h*.045), ['ONIONARY'], w*.038)
    text(canvas, (w*.08, h*.085), ['A little less juggling.', 'A lot more cooking.'], min(w*.067, h*.04), serif=True)
    text(canvas, (w*.08, h*.205), ['Flexible portions. Every step remembered.'], min(w*.035, h*.025), color=INK)
    device(canvas, screen, (w*.10, h*.29, w*.80, h*.66))
    path = root / '05-cooking-with-onionary.png'
    canvas.save(path, icc_profile=srgb())
    outputs.append(path)
    manifest = {'source': source.name, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'family': family, 'outputs': {str(p.relative_to(root)): list(image_size(p)) for p in outputs}}
    (creative / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return outputs


def image_size(path):
    with Image.open(path) as image:
        return image.size


def srgb():
    from PIL import ImageCms
    return ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('screenshots', type=Path)
    parser.add_argument('--family', choices=['iphone', 'ipad'], required=True)
    args = parser.parse_args()
    for path in render(args.screenshots, args.family):
        print(path)
