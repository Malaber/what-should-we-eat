"""
init_db.py — Create all database tables.

Usage:
    python -m execution.db.init_db
"""

from execution.db.database import Base, engine, SessionLocal

# Import models so they register with Base.metadata
from execution.db import models  # noqa: F401
from execution.db.models import Household

def init():
    """Create all tables defined by the ORM models."""
    print("Creating database tables …")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Done.")

    db = SessionLocal()
    if not db.query(Household).first():
        h = Household(name="Demo Kitchen")
        db.add(h)
        db.commit()

if __name__ == "__main__":
    init()
