"""Export App Store captures from the normal, successful native UI test result.

This command never starts a simulator or runs tests. CI captures each device once
in testMarketingScreenshots, then exports that same run's four original images.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from execution.package_marketing_screenshots import validate_dimensions

NAMES = {'01-recipe-book', '02-cooking-companion', '03-flexible-portions', '04-every-tap-remembered'}


def render_capture(screenshots, family, defer_creative):
    from execution.render_marketing_assets import render
    render(screenshots, family, include_creative=not defer_creative)


def export_captures(result, output, family, defer_creative=False):
    if not result.is_dir():
        raise ValueError(f'Native result bundle does not exist: {result}')
    summary = json.loads(subprocess.check_output(
        ['xcrun', 'xcresulttool', 'get', 'test-results', 'summary', '--path', str(result.resolve())], text=True))
    if (summary.get('result') != 'Passed' or summary.get('failedTests') != 0
            or summary.get('skippedTests', 0) != 0 or summary.get('passedTests', 0) < 1):
        raise ValueError('Captures require a completed, passing native result with no failed/skipped tests')
    output.mkdir(parents=True, exist_ok=False)
    exported = output/'attachments'
    subprocess.run(['xcrun', 'xcresulttool', 'export', 'attachments', '--path', str(result.resolve()),
                    '--output-path', str(exported)], check=True)
    manifest = json.loads((exported/'manifest.json').read_text())
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
            source = (exported/attachment['exportedFileName']).resolve()
            if not source.is_relative_to(exported.resolve()):
                raise ValueError('Capture path is outside the attachment export')
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
    render_capture(screenshots, family, defer_creative)
    print(f'Exported four original {family} captures from {result} to {screenshots}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result-bundle', type=Path, required=True)
    parser.add_argument('--family', choices=['iphone', 'ipad'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--defer-creative', action='store_true')
    args = parser.parse_args()
    export_captures(args.result_bundle, args.output, args.family, args.defer_creative)


if __name__ == '__main__':
    main()
