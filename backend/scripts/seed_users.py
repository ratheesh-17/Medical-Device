"""
scripts/seed_users.py
Run after seed_db.py:
    python -m scripts.seed_users
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func
from app.database import engine, Base, SessionLocal
from app.models.db_models import User, Manufacturer, Device
from app.core.security import hash_password


def seed_users():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        print("Hashing passwords...")
        user_hash = hash_password("user123")   # hashed once, reused
        mfr_hash  = hash_password("mfr123")    # hashed once, reused

        print("Querying manufacturers...")
        mfrs = (
            db.query(Manufacturer.id, Manufacturer.name)
            .join(Device, Device.manufacturer_id == Manufacturer.id)
            .group_by(Manufacturer.id, Manufacturer.name)
            .order_by(func.count(Device.id).desc())
            .all()
        )

        print(f"Seeding {len(mfrs)} manufacturer accounts + 1 user account...")
        db.query(User).delete()
        db.commit()

        users = [User(username="user", hashed_password=user_hash, role="user", manufacturer_id=None)]
        users += [
            User(username=f"mfr_{mfr_id}", hashed_password=mfr_hash, role="manufacturer", manufacturer_id=mfr_id)
            for mfr_id, _ in mfrs
        ]

        db.bulk_save_objects(users)
        db.commit()
        print(f"Done. Seeded {len(users)} accounts.")
        print("  user      / user123")
        print("  mfr_<id>  / mfr123")
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()
