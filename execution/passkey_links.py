"""Additional-key links: raw token shown once; successful enrollment claims atomically."""
import secrets
from datetime import timedelta
from execution.api.routers.passkeys import now, digest
from execution.db.passkeys import PasskeyAddLink


def issue_link(db, user, *, admin_id=None, hours=24):
    if not user.is_active or not 1 <= hours <= 720:
        raise ValueError("Use an active account and an expiry from 1 to 720 hours.")
    token = secrets.token_urlsafe(32)
    link = PasskeyAddLink(user_id=user.id, created_by=admin_id,
                          token_hash=digest(token), expires_at=now() + timedelta(hours=hours))
    db.add(link); db.commit(); db.refresh(link)
    return token, link
