"""
init_db.py — Initialize or migrate the database with Alembic.

Usage:
    python -m execution.db.init_db
"""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from execution.db.database import engine


BASELINE_REVISION = "20260402_01"


def _alembic_config() -> Config:
    repo_root = Path(__file__).resolve().parents[2]
    return Config(str(repo_root / "alembic.ini"))


def _adopt_legacy_schema_if_needed(cfg: Config) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if not tables or "alembic_version" in tables:
        return

    # Legacy databases were created before Alembic existed.
    print(f"Legacy schema detected ({len(tables)} tables). Stamping baseline {BASELINE_REVISION} …")
    command.stamp(cfg, BASELINE_REVISION)


def init() -> None:
    """Upgrade the database to the latest Alembic revision."""
    cfg = _alembic_config()
    _adopt_legacy_schema_if_needed(cfg)
    print("Running Alembic migrations …")
    command.upgrade(cfg, "head")
    print("Done.")


if __name__ == "__main__":
    init()
