"""
scripts/reset_db.py
Drops ALL tables and recreates them from the current ORM models.
Run from backend/: python -m scripts.reset_db
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all models so they register with Base.metadata
import app.models.db_models  # noqa: F401

from app.database import engine, Base
from sqlalchemy import text, inspect

DROP_ORDER = [
    "predictions",
    "manufacturer_features",
    "classification_features",
    "model_versions",
    "devices",
    "manufacturers",
]

def reset():
    print("Dropping all tables...")
    with engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for t in DROP_ORDER:
            conn.execute(text(f"DROP TABLE IF EXISTS `{t}`"))
            print(f"  Dropped: {t}")
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        conn.commit()

    print("Creating tables from ORM models...")
    Base.metadata.create_all(bind=engine)

    tables = inspect(engine).get_table_names()
    print(f"  Tables now: {tables}")

    if len(tables) == 6:
        print("SUCCESS — all 6 tables created.")
    else:
        print(f"WARNING — expected 6 tables, got {len(tables)}")

    print("Now run: python -m scripts.seed_db")

if __name__ == "__main__":
    reset()
