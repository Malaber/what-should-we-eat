"""Editable SVG -> outlined, embedded SVG -> Inkscape -> fully decoded RGB PNG."""
import argparse
import base64
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parents[2]
SIZE = (5244, 2950)
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


def render(screenshot, output):
    inkscape = shutil.which('inkscape')
    if not inkscape:
        candidate = Path('/Applications/Inkscape.app/Contents/MacOS/inkscape')
        inkscape = str(candidate) if candidate.exists() else None
    if not inkscape:
        raise RuntimeError('Install Inkscape before rendering creative assets.')
    output.mkdir(parents=True, exist_ok=True)
    icon = ROOT / 'ios/Onionary/AppIcon.icon/Assets/Onionary.png'
    for name in ('header', 'search-results'):
        tree = ET.parse(Path(__file__).parent / f'{name}.svg')
        for element in tree.getroot().iter():
            if element.tag == f'{{{SVG}}}text':
                outline(element)
            elif element.tag == f'{{{SVG}}}image':
                path = icon if element.attrib.pop('data-source') == 'icon' else screenshot
                with Image.open(path) as image:
                    image.load()
                element.set(f'{{{XLINK}}}href', 'data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode())
        svg = output / f'{name}.svg'
        tree.write(svg, encoding='utf-8', xml_declaration=True)
        png = output / f'{name}.png'
        subprocess.run([inkscape, str(svg), f'--export-filename={png}', '--export-width=5244', '--export-height=2950', '--export-background=#fbf2e3', '--export-background-opacity=255'], check=True)
        with Image.open(png) as image:
            image.load()
            image.convert('RGB').save(png, icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes())
        validate(png)
    return [output / 'header.png', output / 'search-results.png']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--screenshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for path in render(args.screenshot.resolve(), args.output.resolve()):
        print(path)
