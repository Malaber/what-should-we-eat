"""Editable SVG -> outlined, embedded SVG -> Inkscape -> fully decoded RGB PNG."""
import argparse
import base64
from io import BytesIO
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from execution.marketing_device_frames import load_frame

SIZE = (5244, 2950)
SAFE_AREA = (1921, 660, 3323, 1622)
SVG = 'http://www.w3.org/2000/svg'
XLINK = 'http://www.w3.org/1999/xlink'
ET.register_namespace('', SVG)
ET.register_namespace('xlink', XLINK)


def outline(element):
    family = element.attrib.pop('font-family')
    font = TTFont(ROOT / 'marketing/fonts' / f'{family}.ttf')
    if 'fvar' in font:
        font = instantiateVariableFont(font, {'wght': 500})
    glyphs, cmap = font.getGlyphSet(), font.getBestCmap()
    size = float(element.attrib.pop('font-size'))
    scale = size / font['head'].unitsPerEm
    x, y = element.attrib.pop('x'), element.attrib.pop('y')
    spacing = float(element.attrib.pop('letter-spacing', 0)) / scale
    text = element.text or ''
    element.tag = f'{{{SVG}}}g'
    element.text = None
    element.set('aria-label', text)
    element.set('transform', f'translate({x} {y}) scale({scale} {-scale})')
    cursor = 0
    for char in text:
        name = cmap.get(ord(char))
        if name is None:
            raise ValueError(f'Missing glyph {char!r} in {family}')
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(pen)
        ET.SubElement(element, f'{{{SVG}}}path', {'d': pen.getCommands(), 'transform': f'translate({cursor} 0)'})
        cursor += font['hmtx'][name][0] + spacing
    font.close()


def validate(path):
    with Image.open(path) as image:
        image.load()
        if image.size != SIZE or image.mode != 'RGB':
            raise ValueError(f'Expected opaque RGB {SIZE}: {path}')


def validate_safe_area(inkscape, svg):
    # Measure the outlined text and device together in the actual renderer.
    # SVG coordinates alone do not tell us where the last glyph ends.
    rows = subprocess.check_output([inkscape, '--query-all', str(svg)], text=True).splitlines()
    group = next((row for row in rows if row.startswith('safe-content,')), None)
    if group is None:
        raise ValueError(f'Missing safe-content artwork: {svg}')
    x, y, width, height = map(float, group.split(',')[1:])
    left, top, right, bottom = SAFE_AREA
    if not (width > 0 and height > 0 and x >= left and y >= top
            and x + width <= right and y + height <= bottom):
        raise ValueError(f'Artwork extends outside Apple’s safe area: {svg}: {group}')

def png_bytes(image):
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def position(x, y, width, height):
    return {key: str(value) for key, value in zip(("x", "y", "width", "height"), (x, y, width, height), strict=True)}


def device_layers(capture_size):
    frame = load_frame(capture_size)
    scale = min(565 / frame.bezel.width, 880 / frame.bezel.height)
    width, height = frame.bezel.width * scale, frame.bezel.height * scale
    x, y = 3260 - width, (SAFE_AREA[1] + SAFE_AREA[3] - height) / 2
    bezel = position(x, y, width, height)
    screen = position(x + frame.display_origin[0] * scale, y + frame.display_origin[1] * scale,
                      frame.display_mask.width * scale, frame.display_mask.height * scale)
    return {"bezel": bezel, "screenshot": screen, "display-mask": screen}, {
        "bezel": png_bytes(frame.bezel), "display-mask": png_bytes(frame.display_mask),
    }


def render(screenshot, output):
    inkscape = shutil.which('inkscape')
    if not inkscape:
        candidate = Path('/Applications/Inkscape.app/Contents/MacOS/inkscape')
        inkscape = str(candidate) if candidate.exists() else None
    if not inkscape:
        raise RuntimeError('Install Inkscape before rendering creative assets.')
    output.mkdir(parents=True, exist_ok=True)
    icon = ROOT / 'ios/Onionary/AppIcon.icon/Assets/Onionary.png'
    with Image.open(screenshot) as captured:
        captured.load()
        positions, layers = device_layers(captured.size)
    layers.update(icon=icon.read_bytes(), screenshot=screenshot.read_bytes())
    for name in ('header', 'search-results'):
        tree = ET.parse(Path(__file__).parent / f'{name}.svg')
        for element in tree.getroot().iter():
            if element.attrib.get('id') == 'screen':
                element.attrib.update(positions["screenshot"])
            if element.tag == f'{{{SVG}}}text':
                outline(element)
            elif element.tag == f'{{{SVG}}}image':
                source = element.attrib.pop('data-source')
                if source in positions:
                    element.attrib.update(positions[source])
                element.set(f'{{{XLINK}}}href', 'data:image/png;base64,' + base64.b64encode(layers[source]).decode())
        svg = output / f'{name}.svg'
        tree.write(svg, encoding='utf-8', xml_declaration=True)
        validate_safe_area(inkscape, svg)
        png = output / f'{name}.png'
        subprocess.run([inkscape, str(svg), f'--export-filename={png}', '--export-width=5244', '--export-height=2950', '--export-background=#fbf2e3', '--export-background-opacity=255'], check=True)
        with Image.open(png) as image:
            image.load()
            image.convert('RGB').save(png, icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes())
        validate(png)
        with Image.open(png) as image:
            preview = image.crop(SAFE_AREA)
            preview.save(output / f'{name}-safe-area-preview.png', icc_profile=image.info['icc_profile'])
    return [output / 'header.png', output / 'search-results.png']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--screenshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for path in render(args.screenshot.resolve(), args.output.resolve()):
        print(path)
