"""
scripts/migrate.py

Drops tables that have the old schema and recreates them with the new schema.
Safe to run — only touches the three stale tables, leaves manufacturers intact.

Run from backend/:
    python -m scripts.migrate
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine, Base
from sqlalchemy import text

STALE_TABLES = [
    "predictions",
    "model_versions",
    "manufacturer_features",
    "events",          # old table, not in new ORM
]

def migrate():
    print("Dropping stale tables...")
    with engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in STALE_TABLES:
            conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
            print(f"  Dropped: {table}")
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        conn.commit()

    print("Recreating tables from ORM models...")
    Base.metadata.create_all(bind=engine)
    print("  Tables created.")
    print("Done. Now run: python -m scripts.seed_db")

if __name__ == "__main__":
    migrate()
