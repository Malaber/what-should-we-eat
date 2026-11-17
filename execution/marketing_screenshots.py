"""Export App Store captures from the normal, successful native UI test result.

This command never starts a simulator or runs tests. It exports images from the
marketing test or the iPhone Duo cooking test in the same successful run.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from execution.package_marketing_screenshots import CAPTURES, DUO_CAPTURES, validate_dimensions, validate_duo_bundle

NAMES = {Path(name).stem for name in CAPTURES}


def render_capture(screenshots, family, defer_creative):
    from execution.render_marketing_assets import render
    render(screenshots, family, include_creative=not defer_creative)


def attachment_path(exported, attachment):
    source = (exported/attachment['exportedFileName']).resolve()
    if not source.is_relative_to(exported.resolve()):
        raise ValueError('Capture path is outside the attachment export')
    return source


def export_duo_captures(manifest, exported, output):
    from PIL import Image, ImageCms, ImageOps

    captures = {}
    for test in manifest:
        for attachment in test.get('attachments', []):
            match = re.match(r'Duo-workspace-(0|180)(?:_|\.png|$)', attachment.get('suggestedHumanReadableName', ''))
            if not match:
                continue
            angle = int(match.group(1))
            if angle not in captures or attachment['timestamp'] > captures[angle]['timestamp']:
                captures[angle] = attachment
    if captures.keys() != DUO_CAPTURES.keys():
        raise ValueError('Expected successful outer and inner iPhone Duo cooking captures')

    screenshots = output/'en-US'
    screenshots.mkdir()
    srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    for angle, (name, size) in DUO_CAPTURES.items():
        with Image.open(attachment_path(exported, captures[angle])) as image:
            image.load()
            if image.format != 'PNG' or image.mode != 'RGB':
                raise ValueError(f'Expected an RGB PNG from the Duo test: {name}')
            frame = ImageOps.exif_transpose(image)
            # XCTest can round the unfolded window down by one pixel in each
            # dimension. Preserve its pixels and replicate only the outer edge.
            if angle == 180 and frame.size == (size[0] - 1, size[1] - 1):
                width, height = frame.size
                padded = Image.new('RGB', size)
                padded.paste(frame, (0, 0))
                padded.paste(frame.crop((width - 1, 0, width, height)), (width, 0))
                padded.paste(padded.crop((0, height - 1, width + 1, height)), (0, height))
                frame = padded
            if frame.size != size:
                raise ValueError(f'Wrong Duo capture dimensions {frame.size}, expected {size}: {name}')
            frame.save(screenshots/name, icc_profile=srgb)
    validate_duo_bundle(screenshots)
    print(f'Exported both iPhone Duo cooking screens to {screenshots}')


def require_passing_result(result):
    if not result.is_dir():
        raise ValueError(f'Native result bundle does not exist: {result}')
    summary = json.loads(subprocess.check_output(
        ['xcrun', 'xcresulttool', 'get', 'test-results', 'summary', '--path', str(result.resolve())], text=True))
    if (summary.get('result') != 'Passed' or summary.get('failedTests') != 0
            or summary.get('skippedTests', 0) != 0 or summary.get('passedTests', 0) < 1):
        raise ValueError('Captures require a completed, passing native result with no failed/skipped tests')


def export_attachments(result, exported):
    subprocess.run(['xcrun', 'xcresulttool', 'export', 'attachments', '--path', str(result.resolve()),
                    '--output-path', str(exported)], check=True)
    return json.loads((exported/'manifest.json').read_text())


def export_captures(result, output, family, defer_creative=False, duo_fold_result=None):
    require_passing_result(result)
    if duo_fold_result is not None and family != 'duo':
        raise ValueError('A fold result is only supported for iPhone Duo')
    separate_fold_result = duo_fold_result is not None and duo_fold_result.resolve() != result.resolve()
    if separate_fold_result:
        require_passing_result(duo_fold_result)
    output.mkdir(parents=True, exist_ok=False)
    exported = output/'attachments'
    manifest = export_attachments(result, exported)
    if family == 'duo' and duo_fold_result is None:
        # Recover the two display captures from an earlier fold-only run.
        export_duo_captures(manifest, exported, output)
        return
    captures = {}
    for test in manifest:
        for attachment in test.get('attachments', []):
            name = attachment.get('suggestedHumanReadableName', '')
            if not name.startswith('marketing-'):
                continue
            match = re.match(r'marketing-([^._]+)(?:_|\.png|$)', name)
            key = match.group(1) if match else ''
            if key not in NAMES or key in captures:
                raise ValueError(f'Unexpected or duplicate marketing capture: {name}')
            source = attachment_path(exported, attachment)
            validate_dimensions(source, family)
            from PIL import Image
            with Image.open(source) as image:
                image.load()
            captures[key] = source
    if set(captures) != NAMES:
        raise ValueError(f'Expected four marketing scenes; missing {sorted(NAMES - set(captures))}')
    screenshots = output/'en-US'
    screenshots.mkdir()
    for key, source in captures.items():
        shutil.copy2(source, screenshots/(key+'.png'))
    if duo_fold_result is not None:
        fold = output/'fold'
        fold.mkdir()
        if separate_fold_result:
            fold_export = fold/'attachments'
            export_duo_captures(export_attachments(duo_fold_result, fold_export), fold_export, fold)
        else:
            export_duo_captures(manifest, exported, fold)
        inner_name = DUO_CAPTURES[180][0]
        inner = screenshots/'inner'
        inner.mkdir()
        shutil.copy2(fold/'en-US'/inner_name, inner/inner_name)
    render_capture(screenshots, family, defer_creative)
    print(f'Exported four original {family} captures from {result} to {screenshots}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result-bundle', type=Path, required=True)
    parser.add_argument('--family', choices=['iphone', 'ipad', 'duo'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--defer-creative', action='store_true')
    parser.add_argument('--duo-fold-result', type=Path, help='Include the unfolded Duo screen from this or another passing result')
    args = parser.parse_args()
    export_captures(args.result_bundle, args.output, args.family, args.defer_creative, args.duo_fold_result)


if __name__ == '__main__':
    main()
