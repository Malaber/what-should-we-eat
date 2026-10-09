"""Immutable recipe snapshots and bounded, DNS-pinned public HTTPS imports."""
import hashlib
import http.client
import ipaddress
import json
import re
import socket
import ssl
from urllib.parse import urlsplit
from pydantic import ValidationError
from execution.api.schemas import RecipeCreate

MAX_BYTES = 1_000_000
TOKEN = re.compile(r'^[A-Za-z0-9_-]{43}$')


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def share_location(url):
    parts = urlsplit(url)
    if (parts.scheme != 'https' or not parts.hostname or parts.username or parts.password
            or parts.port not in (None, 443) or parts.path != '/share.html' or parts.query
            or not TOKEN.fullmatch(parts.fragment)):
        raise ValueError('Use an HTTPS Onionary recipe-copy link including its fragment.')
    return parts.hostname, parts.fragment


def public_addresses(host):
    try:
        addresses = list(dict.fromkeys(row[4][0] for row in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)))
    except OSError as exc:
        raise ValueError("Could not resolve the recipe server.") from exc
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise ValueError('Recipe copies can only be fetched from public HTTPS servers.')
    return addresses


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, address):
        super().__init__(host, timeout=8, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        # Connect to the validated address, while retaining TLS hostname verification.
        raw = socket.create_connection((self.address, 443), timeout=self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except BaseException:
            raw.close()
            raise


def validate_snapshot(value):
    if not isinstance(value, dict) or value.get('format') != 'onionary.recipe.v1':
        raise ValueError('Unsupported Onionary recipe-copy format.')
    try:
        recipe = RecipeCreate.model_validate(value.get('recipe'))
    except ValidationError as exc:
        raise ValueError('Invalid recipe copy.') from exc
    if (not recipe.name.strip() or len(recipe.name) > 255 or len(recipe.notes or '') > 100_000
            or len(recipe.ingredients) > 1000 or len(recipe.instruction_steps) > 1000
            or len(recipe.tags) > 100 or any(len(tag) > 100 for tag in recipe.tags)
            or any(not i.name.strip() or len(i.name) > 255 or len(i.unit or '') > 50
                   or (i.quantity is not None and not (0 <= i.quantity <= 1e12)) for i in recipe.ingredients)
            or any(not s.description.strip() or len(s.description) > 100_000 for s in recipe.instruction_steps)):
        raise ValueError('Recipe copy exceeds supported limits or has invalid quantities.')
    return recipe


def fetch_snapshot(url):
    host, token = share_location(url)
    connection = PinnedHTTPSConnection(host, public_addresses(host)[0])
    try:
        # No Authorization, cookies, proxy inheritance, redirects, or arbitrary URL paths.
        connection.request('POST', '/recipe-shares/resolve', body=json.dumps({'token': token}),
                           headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        response = connection.getresponse()
        if response.status != 200 or response.getheader('Content-Type', '').split(';')[0] != 'application/json':
            raise ValueError('Recipe link is unavailable, expired, or revoked.')
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('Recipe copy is too large.')
        return validate_snapshot(json.loads(raw))
    except (OSError, http.client.HTTPException, json.JSONDecodeError) as exc:
        raise ValueError('Could not read the recipe copy from that server.') from exc
    finally:
        connection.close()
