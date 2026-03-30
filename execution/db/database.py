"""
database.py — SQLAlchemy engine, session factory, and declarative base.

Connection string is read from DATABASE_URL in .env.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv(".env.local")
load_dotenv(".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://recipes_user:recipes_pass@localhost:5432/recipes_db",
)

if "{{" in DATABASE_URL:
    DATABASE_URL = "postgresql://recipes_user:recipes_pass@localhost:5432/recipes_db"

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
