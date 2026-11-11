"""One bounded, acknowledged simulator helper session; never retry a fold."""
import os
import select
import subprocess
import time


class HingeProcess:
    def __init__(self, command, timeout=20):
        self.timeout = timeout
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        try:
            self._expect('READY')
        except Exception:
            self.close()
            raise

    def _expect(self, expected):
        deadline = time.monotonic() + self.timeout
        line = bytearray()
        while len(line) < 128:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([self.process.stdout], [], [], remaining)[0]:
                raise TimeoutError(f'Hinge helper did not acknowledge {expected!r} within {self.timeout}s')
            char = os.read(self.process.stdout.fileno(), 1)
            if not char:
                raise RuntimeError(f'Hinge helper exited before {expected!r}: {line!r}')
            if char == b'\n':
                received = line.decode('ascii')
                if received != expected:
                    raise RuntimeError(f'Hinge helper expected {expected!r}, received {received!r}')
                return
            line.extend(char)
        raise RuntimeError('Oversized hinge acknowledgement')

    def pose(self, angle):
        if angle not in (0, 90, 180):
            raise ValueError('Unsupported hinge angle')
        if self.process.poll() is not None:
            raise RuntimeError('Hinge helper is no longer running')
        try:
            self.process.stdin.write(f'{angle}\n'.encode('ascii'))
            self.process.stdin.flush()
            self._expect(f'OK {angle}')
        except Exception:
            # A late acknowledgement must never satisfy a later request.
            self.close()
            raise

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.process.stdin.close()
        self.process.stdout.close()
