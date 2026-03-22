"""
init_db.py — Create all database tables.

Usage:
    python -m execution.db.init_db
"""

from execution.db.database import Base, engine

# Import models so they register with Base.metadata
from execution.db import models  # noqa: F401


def init():
    """Create all tables defined by the ORM models."""
    print("Creating database tables …")
    Base.metadata.create_all(bind=engine)
    print("Done.")


if __name__ == "__main__":
    init()
