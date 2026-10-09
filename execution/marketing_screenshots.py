"""Capture real iPhone/iPad App Store screenshots from deterministic Debug fixtures."""
import argparse
import json
from pathlib import Path
import shutil
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'ios/Onionary'

def run(*args, **kwargs):
    return subprocess.check_output(args, text=True, **kwargs)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', default='iPhone 17 Pro Max')
    parser.add_argument('--output', type=Path, default=ROOT / '.tmp/marketing')
    args = parser.parse_args()
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=True)
    runtimes = json.loads(run('xcrun','simctl','list','runtimes','--json'))['runtimes']
    runtime = next(r['identifier'] for r in reversed(runtimes) if r['isAvailable'] and '.iOS-' in r['identifier'])
    device = run('xcrun','simctl','create','Onionary Marketing',args.device,runtime).strip()
    try:
        run('xcrun','simctl','boot',device)
        run('xcrun','simctl','bootstatus',device,'-b')
        run('xcrun','simctl','ui',device,'appearance','light')
        run('xcrun','simctl','status_bar',device,'override','--time','9:41','--dataNetwork','wifi','--wifiMode','active','--wifiBars','3','--batteryState','charged','--batteryLevel','100')
        subprocess.run(['xcodegen','generate'],cwd=PACKAGE,check=True)
        result = output / 'Screenshots.xcresult'
        if result.exists():
            raise SystemExit('Use a fresh output directory; an existing result bundle will not be overwritten.')
        subprocess.run(['xcodebuild','-project','Onionary.xcodeproj','-scheme','Onionary',
            '-destination',f'platform=iOS Simulator,id={device}', '-parallel-testing-enabled','NO',
            '-only-testing:OnionaryUITests/OnionaryUITests/testMarketingScreenshots',
            '-resultBundlePath',str(result),'CODE_SIGNING_ALLOWED=NO','test'],cwd=PACKAGE,check=True)
        exported = output / 'attachments'
        run('xcrun','xcresulttool','export','attachments','--path',str(result),'--output-path',str(exported))
        manifest = json.loads((exported / 'manifest.json').read_text())
        screenshots = output / 'en-US'; screenshots.mkdir(exist_ok=True)
        count = 0
        for test in manifest:
            for attachment in test.get('attachments',[]):
                name = attachment.get('suggestedHumanReadableName','')
                if not name.startswith('marketing-'):
                    continue
                source = exported / attachment['exportedFileName']
                width,height = struct.unpack('>II',source.read_bytes()[16:24])
                allowed = {(1260,2736),(1290,2796),(1320,2868),(1284,2778),(1242,2688),(2064,2752),(2048,2732)}
                if (width,height) not in allowed:
                    raise SystemExit(f'Unexpected App Store screenshot size: {width}x{height}')
                shutil.copy2(source,screenshots / (name.removeprefix('marketing-').split('.png')[0]+'.png'))
                count += 1
        if count != 4:
            raise SystemExit(f'Expected 4 marketing screenshots, found {count}. Inspect attachment manifest.')
        print(f'Exported {count} screenshots to {screenshots}')
    finally:
        subprocess.run(['xcrun','simctl','delete',device],check=False)

if __name__ == '__main__':
    main()
