"""Compose three App Store portraits around this run's native screenshots."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from execution.package_marketing_screenshots import CAPTURES, PORTRAIT_SOURCES, validate_dimensions

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "marketing"
CREATIVE_SIZES = {"header.png": (5244, 2950), "search-results.png": (5244, 2950)}
# One concept per screenshot, with enough contrast to read at thumbnail size.
PORTRAIT_DESIGNS = {
    "05-cooking-with-onionary.png": (
        "IN THE KITCHEN", ("Cook at", "your pace."), "Check off ingredients and steps.",
        "#2e1929", "#66374e", "#fff6ee", "#f0bdcc",
    ),
    "06-your-recipe-book.png": (
        "THE RECIPE BOOK", ("Find your", "next favorite."), "Browse recipes by tag.",
        "#fcf4e9", "#e6bab9", "#492239", "#714853",
    ),
    "07-make-it-your-size.png": (
        "FLEXIBLE PORTIONS", ("Make it", "your size."), "Scale to what you have.",
        "#e8efdc", "#aebf9f", "#233b30", "#38563f",
    ),
}


def font(size, serif=False, weight=500):
    face = ImageFont.truetype(str(ASSETS / "fonts" / ("Lora.ttf" if serif else "Manrope.ttf")), round(size))
    face.set_variation_by_axes([weight])
    return face


def device(canvas, screen, box):
    x, y, w, h = box
    fitted = ImageOps.contain(screen, (w, h), Image.Resampling.LANCZOS)
    sw, sh = fitted.size
    x, y = round(x + (w - sw) / 2), round(y + (h - sh) / 2)
    bevel = max(9, round(canvas.width * .012))
    radius = round(sw * .055)
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((x-bevel, y-bevel, x+sw+bevel, y+sh+bevel), radius=radius+bevel,
                           fill="#241e24", outline="#8e7782", width=max(2, bevel//4))
    mask = Image.new("L", fitted.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, sw-1, sh-1), radius=radius, fill=255)
    canvas.paste(fitted, (x, y), mask)


def portrait_background(size, start, end, ink, muted):
    w, h = size
    gradient = Image.linear_gradient("L").resize(size)
    paper = ImageOps.colorize(gradient, start, end)
    # Overlapping translucent ellipses make the curved layers. Keep the upper
    # copy area quiet and let the layers fan out behind the device.
    layers = (
        ((.11, .38, 1.64, 1.20), ink, muted, 152),
        ((.24, .40, 1.44, 1.22), end, start, 190),
        ((.40, .48, 1.68, 1.04), muted, ink, 128),
        ((-.92, .42, .45, 1.09), muted, end, 145),
        ((-.87, .59, .46, 1.23), ink, end, 115),
        ((-.55, .73, .50, 1.22), end, start, 178),
    )
    for bounds, light, shade, opacity in layers:
        mask = Image.new("L", size)
        ImageDraw.Draw(mask).ellipse((bounds[0]*w, bounds[1]*h, bounds[2]*w, bounds[3]*h), fill=opacity)
        paper.paste(ImageOps.colorize(gradient, light, shade), mask=mask)

    outline = Image.new("L", size)
    draw = ImageDraw.Draw(outline)
    for inset in (0, .04, .09):
        draw.ellipse(((.22+inset)*w, (.41+inset)*h, (1.43+inset)*w, 1.19*h),
                     outline=95, width=max(2, round(w*.002)))
        draw.ellipse(((-.76-inset)*w, (.60+inset)*h, (.50+inset)*w, (1.21+inset)*h),
                     outline=78, width=max(2, round(w*.002)))
    fade = Image.linear_gradient("L").resize((w, round(h*.32)))
    opacity = Image.new("L", size, 255)
    opacity.paste(fade, (0, 0))
    paper.paste(start, mask=ImageChops.multiply(outline, opacity))
    return paper


def draw_portrait(screen, design):
    kicker, headline, detail, start, end, ink, muted = design
    w, h = screen.size
    canvas = portrait_background(screen.size, start, end, ink, muted)
    draw = ImageDraw.Draw(canvas)
    draw.text((w*.09, h*.055), kicker, font=font(w*.029, weight=700), fill=muted, anchor="lt")
    headline_size = min(w*.097, h*.059)
    headline_font = font(headline_size, serif=True, weight=600)
    for index, line in enumerate(headline):
        draw.text((w*.085, h*.093 + index * headline_size * 1.08),
                  line, font=headline_font, fill=ink, anchor="lt")
    draw.text((w*.09, h*.230), detail, font=font(w*.035), fill=muted, anchor="lt")
    device(canvas, screen, (round(w*.10), round(h*.288), round(w*.80), round(h*.652)))
    return canvas


def render(root: Path, family: str, *, include_creative: bool = True):
    paths = {name: root / name for name in CAPTURES}
    for name, path in paths.items():
        candidates = list(root.glob(f"{path.stem}*.png"))
        if candidates != [path]:
            raise ValueError(f"Expected exactly one canonical {name} in {root}")
        validate_dimensions(path, family)
        with Image.open(path) as image:
            image.load()

    creative = root / "creative"
    portraits = root / "portraits"
    creative.mkdir(exist_ok=True)
    portraits.mkdir(exist_ok=True)
    screenshot = paths[CAPTURES[1]]
    outputs = []
    if include_creative:
        from marketing.creative.render import render as render_vectors
        outputs.extend(render_vectors(screenshot, creative))
    hashes = {}
    profile = srgb()
    for name, source in PORTRAIT_SOURCES.items():
        with Image.open(paths[source]) as captured:
            portrait = draw_portrait(captured.convert("RGB"), PORTRAIT_DESIGNS[name])
        path = portraits / name
        portrait.save(path, icc_profile=profile)
        outputs.append(path)
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    captures = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}
    manifest = {
        "source": screenshot.name, "source_sha256": captures[screenshot.name],
        "family": family, "captures": captures, "portrait_sources": PORTRAIT_SOURCES,
        "portrait_sha256": hashes,
    }
    (creative / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return outputs


def srgb():
    from PIL import ImageCms
    return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("screenshots", type=Path)
    parser.add_argument("--family", choices=["iphone", "ipad"], required=True)
    args = parser.parse_args()
    for path in render(args.screenshots, args.family):
        print(path)
