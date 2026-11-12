"""Run one Duo continuity scenario with a simulator-only fold controller.

The loopback service controls only the dedicated simulator, never app data or
production processes. No termination RPC or retries; all fold failures fail tests.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import subprocess
import sys
import threading
from hinge_process import HingeProcess


class FoldController:
    """One session, started only after XCTest has established a working app UI."""
    def __init__(self, command):
        self.command = command
        self.helper = None
        self.attempted = False

    def start(self):
        if self.helper is not None:
            return
        if self.attempted:
            raise RuntimeError('Duo helper startup already failed; no retry')
        self.attempted = True
        self.helper = HingeProcess(self.command)

    def pose(self, angle):
        self.start()
        self.helper.pose(angle)

    def close(self):
        if self.helper is not None:
            self.helper.close()


def test_bundle(command):
    if command.count('-derivedDataPath') != 1:
        raise ValueError('Duo tests require one explicit -derivedDataPath from the build command')
    derived = Path(command[command.index('-derivedDataPath') + 1]).resolve()
    bundle = derived / 'Build/Products/Debug-iphonesimulator/OnionaryUITests-Runner.app/PlugIns/OnionaryUITests.xctest'
    if not bundle.is_dir():
        raise FileNotFoundError(f'Build the Duo test bundle before starting the simulator: {bundle}')
    return bundle


def prepare(result):
    root = Path(result).resolve()
    root.mkdir(parents=True, exist_ok=True)
    binary = root / 'duo-hinge'
    subprocess.run(['xcrun', '--sdk', 'iphonesimulator', 'clang', '-target',
                    'arm64-apple-ios27.1-simulator', '-fobjc-arc', '-framework', 'Foundation',
                    str(Path(__file__).with_name('duo_hinge.m')), '-o', str(binary)], check=True, timeout=120)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if args[0] == '--prepare':
        prepare(args[1])
        return 0
    simulator, result, *command = args
    root = Path(result).resolve()
    bundle = test_bundle(command)
    binary = root / 'duo-hinge'
    if not binary.is_file():
        raise FileNotFoundError(f'Compile the Duo helper before boot using --prepare {root}')
    hinge = FoldController(['xcrun', 'simctl', 'spawn', simulator, str(binary), '--serve'])

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path not in ('/ready', '/pose/0', '/pose/90', '/pose/180'):
                self.send_error(404); return
            try:
                if self.path == '/ready':
                    hinge.start()
                else:
                    hinge.pose(int(self.path.rsplit('/', 1)[1]))
                self.send_response(204); self.end_headers()
            except (subprocess.SubprocessError, OSError, RuntimeError) as error:
                print(f"Duo controller {self.path}: {error}", file=sys.stderr, flush=True)
                self.send_error(500, str(error))
        def log_message(self, *_):
            pass

    server = None
    serving = False
    try:
        server = HTTPServer(('127.0.0.1', 0), Handler)
        (bundle / 'duo-port.txt').write_text(str(server.server_port))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        serving = True
        return subprocess.run(command, check=False).returncode
    finally:
        if serving:
            server.shutdown()
        if server is not None:
            server.server_close()
        hinge.close()



if __name__ == '__main__':
    raise SystemExit(main())
