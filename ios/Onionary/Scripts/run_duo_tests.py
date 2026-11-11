"""Run one Duo continuity scenario with a simulator-only fold controller.

The loopback service controls only the dedicated simulator, never app data or
production processes. No termination RPC or retries; all fold failures fail tests.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import subprocess
import sys
import threading


def main():
    simulator, result, *command = sys.argv[1:]
    root = Path(result).resolve()
    binary = root / 'duo-hinge'
    subprocess.run(['xcrun', '--sdk', 'iphonesimulator', 'clang', '-target',
                    'arm64-apple-ios27.1-simulator', '-fobjc-arc', '-framework', 'Foundation',
                    str(Path(__file__).with_name('duo_hinge.m')), '-o', str(binary)], check=True)

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path not in ('/pose/0', '/pose/90', '/pose/180'):
                self.send_error(404); return
            try:
                subprocess.run(['xcrun', 'simctl', 'spawn', simulator, str(binary), self.path.rsplit('/', 1)[1]], check=True, timeout=20)
                self.send_response(204); self.end_headers()
            except (subprocess.SubprocessError, OSError) as error:
                print(f"Duo controller {self.path}: {error}", file=sys.stderr, flush=True)
                self.send_error(500, str(error))
        def do_GET(self):
            if self.path not in ('/capture/0', '/capture/90', '/capture/180'):
                self.send_error(404); return
            angle = self.path.rsplit('/', 1)[1]
            capture = root / ('pose-' + angle + '.png')
            try:
                display = 'primary' if angle == '0' else 'primary-1'
                subprocess.run(['xcrun', 'simctl', 'io', simulator, 'screenshot', '--display=' + display, str(capture)], check=True, timeout=45)
                data = capture.read_bytes()
                self.send_response(200); self.send_header('Content-Type', 'image/png')
                self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
            except (subprocess.SubprocessError, OSError) as error:
                print(f"Duo controller {self.path}: {error}", file=sys.stderr, flush=True)
                self.send_error(500, str(error))
        def log_message(self, *_):
            pass

    server = HTTPServer(('127.0.0.1', 0), Handler)
    bundle = root / 'DerivedData/Build/Products/Debug-iphonesimulator/OnionaryUITests-Runner.app/PlugIns/OnionaryUITests.xctest'
    (bundle / 'duo-port.txt').write_text(str(server.server_port))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        return subprocess.run(command, check=False).returncode
    finally:
        server.shutdown(); server.server_close()


if __name__ == '__main__':
    raise SystemExit(main())
