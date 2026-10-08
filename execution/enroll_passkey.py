"""Run on the server: python -m execution.enroll_passkey chef@example.com.

Outputs a 15-minute one-time link. Share privately with the verified account
owner. Never send links to someone based on an unverified email claim.
"""
import argparse
from execution.api.routers.passkeys import origin, save_flow
from execution.db.database import SessionLocal
from execution.db.models import User


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email")
    args = parser.parse_args()
    with SessionLocal() as db:
        user = db.query(User).filter_by(email=args.email, is_active=True).one_or_none()
        if user is None:
            parser.error("No active account has that email")
        token = save_flow(db, "enrollment", {"user_id": user.id}, lifetime=900)
        print(f"{origin()}/auth/login#enroll={token}")


if __name__ == "__main__":
    main()
