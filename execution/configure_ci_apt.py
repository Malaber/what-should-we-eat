"""Use the canonical Ubuntu archive on ephemeral Ubuntu 24.04 CI runners.

Keep the distribution's suites, components and signed keyring. The canonical
archive also publishes noble-security, so all Ubuntu packages use one hostname.
Updates fail on errors and network operations do not retry.
"""
import os
from pathlib import Path
import re
import sys


def configure(root: Path):
    release = dict(line.split('=', 1) for line in (root/'etc/os-release').read_text().splitlines()
                   if '=' in line and not line.startswith('#'))
    if release.get('ID', '').strip('"') != 'ubuntu' or release.get('VERSION_ID', '').strip('"') != '24.04':
        raise ValueError('CI package sources require the pinned Ubuntu 24.04 runner')
    sources = root/'etc/apt/sources.list.d/ubuntu.sources'
    original = sources.read_text()
    if 'noble' not in original:
        raise ValueError('Expected Ubuntu noble package suites; refusing to alter unknown sources')
    updated, count = re.subn(r'^URIs:.*$', 'URIs: https://archive.ubuntu.com/ubuntu/', original, flags=re.MULTILINE)
    if not count:
        raise ValueError('No Ubuntu archive URI found')
    sources.write_text(updated)
    (root/'etc/apt/apt.conf.d/99-onionary-ci').write_text(
        'APT::Update::Error-Mode "any";\nAcquire::Retries "0";\n'
        'Acquire::http::Timeout "30";\nAcquire::https::Timeout "30";\n')


if __name__ == '__main__':
    if sys.platform != 'linux' or os.environ.get('GITHUB_ACTIONS') != 'true':
        raise SystemExit('This setup is only for ephemeral GitHub Actions Linux runners')
    configure(Path('/'))
