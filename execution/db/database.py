"""
database.py — SQLAlchemy engine, session factory, and declarative base.

Connection string is read from DATABASE_URL in .env.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

load_dotenv(".env.local")
load_dotenv(".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://recipes_user:recipes_pass@localhost:5432/recipes_db",
)

if "{{" in DATABASE_URL:
    DATABASE_URL = "postgresql://recipes_user:recipes_pass@localhost:5432/recipes_db"

# In-memory SQLite needs StaticPool so all sessions share the same database,
# and check_same_thread=False for multi-threaded test runners.
if DATABASE_URL == "sqlite://":
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session, closes it on teardown."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
