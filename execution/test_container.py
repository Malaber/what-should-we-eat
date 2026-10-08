"""Exercise the deployment image with isolated disposable PostgreSQL resources.

Usage: python execution/test_container.py --image onionary:local
Build the image first. No host ports, production credentials, or existing volumes
are used. Only resources created by this invocation are removed.
"""
import argparse
import subprocess
import time
import uuid
from urllib.parse import quote


def docker(*args, check=True):
    return subprocess.run(['docker', *args], check=check, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    args = parser.parse_args()
    prefix = 'onionary-check-' + uuid.uuid4().hex[:12]
    db, api = prefix + '-db', prefix + '-api'
    password = 'Disposable$database/password@with#punctuation%'
    env = ['-e', f'DATABASE_URL=postgresql://onionary:{quote(password, safe="")}@{db}:5432/onionary',
           '-e', 'SECRET_KEY=disposable-container-test-signing-key-only',
           '-e', 'APP_BASE_URL=http://localhost:8000',
           '-e', 'ALLOW_LEGACY_PASSWORD_AUTH=false']
    try:
        docker('network', 'create', prefix)
        docker('run', '-d', '--name', db, '--network', prefix,
               '-e', 'POSTGRES_USER=onionary', '-e', 'POSTGRES_DB=onionary',
               '-e', f'POSTGRES_PASSWORD={password}', 'postgres:16-alpine')
        for _ in range(60):
            if docker('exec', db, 'pg_isready', '-U', 'onionary', check=False).returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError('PostgreSQL failed readiness')
        for _ in range(2):
            docker('run', '--rm', '--network', prefix, '--user', '1008:1008',
                   *env, args.image, 'python', '-m', 'execution.db.init_db')
        print('Fresh migration and repeated migration passed', flush=True)
        docker('run', '-d', '--name', api, '--network', prefix, '--user', '1008:1008', *env, args.image)
        check = '''import httpx, os, sys
assert sys.version_info[:2] == (3, 14), sys.version
assert os.getuid() == 1008
client = httpx.Client(base_url="http://localhost:8000")
assert client.get("/health").json() == {"status": "ok"}
assert client.get("/").status_code == 200
assert client.get("/auth/login").status_code == 200
assert client.get("/recipes").status_code == 401
r = client.post("/auth/register/options", headers={"Origin": "http://localhost:8000"}, json={"email": "test@example.org", "display_name": "Container Test"})
assert r.status_code == 200, r.text
assert "challenge" in r.json()
'''
        for _ in range(30):
            result = docker('exec', api, 'python', '-c', check, check=False)
            if result.returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError('API check failed: ' + result.stdout)
        count = docker('exec', db, 'psql', '-U', 'onionary', '-Atc',
                       "SELECT count(*) FROM auth_flows;").stdout.strip()
        assert int(count) >= 1, 'Passkey challenge was not persisted'
        docker('restart', api)
        print('Python 3.14/non-root API, frontend, protected recipes, and PostgreSQL passkey writes passed', flush=True)
    except subprocess.CalledProcessError as exc:
        # Synthetic URL can appear in migration errors; redact it for clarity.
        raise RuntimeError(exc.stdout.replace(password, '[test-password]').replace(quote(password, safe=''), '[test-password]')) from None
    finally:
        for name in (api, db):
            docker('rm', '-f', '-v', name, check=False)
        docker('network', 'rm', prefix, check=False)


if __name__ == '__main__':
    main()
