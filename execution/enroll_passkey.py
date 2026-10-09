"""Run on the server: python -m execution.enroll_passkey chef@example.com.

Outputs a one-time additional-key link (24 hours by default). Share privately with the verified account
owner. Never send links to someone based on an unverified email claim.
"""
import argparse
from execution.api.routers.passkeys import origin
from execution.passkey_links import issue_link
from execution.db.database import SessionLocal
from execution.db.models import User


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email")
    parser.add_argument("--hours", type=int, default=24, choices=range(1, 721), metavar="1..720")
    args = parser.parse_args()
    with SessionLocal() as db:
        user = db.query(User).filter_by(email=args.email, is_active=True).one_or_none()
        if user is None:
            parser.error("No active account has that email")
        token, link = issue_link(db, user, hours=args.hours)
        print(f"{origin()}/auth/login#enroll={token}&identifier={link.id}")


if __name__ == "__main__":
    main()
