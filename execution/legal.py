"""Instance legal identity, configured explicitly by its operator."""
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class LegalIdentity:
    name: str
    address: str
    email: str


def legal_identity() -> LegalIdentity:
    names = ('IMPRESSUM_NAME', 'IMPRESSUM_ADDRESS', 'IMPRESSUM_EMAIL')
    values = [os.getenv(name, '').strip() for name in names]
    missing = [name for name, value in zip(names, values) if not value]
    if missing:
        raise RuntimeError('Missing required instance legal configuration: ' + ', '.join(missing))
    if '@' not in values[2] or any(c in values[2] for c in '\r\n <>"'):
        raise RuntimeError('IMPRESSUM_EMAIL must be a valid contact email address')
    return LegalIdentity(*values)
