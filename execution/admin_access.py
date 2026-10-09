"""Server operator: python -m execution.admin_access you@example.com [--revoke]."""
import argparse
from execution.db.database import SessionLocal
from execution.db.models import User


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('email')
    parser.add_argument('--revoke', action='store_true')
    args = parser.parse_args()
    with SessionLocal() as db:
        user = db.query(User).filter_by(email=args.email, is_active=True).one_or_none()
        if not user:
            parser.error('Register this exact account with a passkey first.')
        user.is_admin = not args.revoke
        db.commit()
    print('Administrator access updated.')


if __name__ == '__main__':
    main()
