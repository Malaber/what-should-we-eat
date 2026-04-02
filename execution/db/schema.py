"""
schema.py — lightweight schema compatibility helpers for local development.
"""

from sqlalchemy import text

from execution.db.database import engine


def ensure_schema_compatibility():
    """Apply small additive schema changes for existing local databases."""
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE recipes ADD COLUMN IF NOT EXISTS notes TEXT"))
