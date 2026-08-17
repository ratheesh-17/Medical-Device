"""
scripts/seed_users.py

Seeds demo user accounts:
  - user / user123  (role: user / technician)
  - One manufacturer account per top-10 manufacturer (by device count)
    username: mfr_<manufacturer_id>   password: mfr123

Run after seed_db.py:
    python -m scripts.seed_users
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import engine, Base, SessionLocal
from app.models.db_models import User, Manufacturer, Device
from app.core.security import hash_password


def seed_users():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        db.query(User).delete()
        db.commit()

        users = []

        # Technician account
        users.append(User(
            username="user",
            hashed_password=hash_password("user123"),
            role="user",
            manufacturer_id=None,
        ))

        # Top manufacturers by device count
        top_mfrs = (
            db.query(Manufacturer.id, Manufacturer.name, func.count(Device.id).label("cnt"))
            .join(Device, Device.manufacturer_id == Manufacturer.id)
            .group_by(Manufacturer.id, Manufacturer.name)
            .having(func.count(Device.id) >= 10)
            .order_by(func.count(Device.id).desc())
            .limit(50)
            .all()
        )

        for mfr_id, mfr_name, cnt in top_mfrs:
            users.append(User(
                username=f"mfr_{mfr_id}",
                hashed_password=hash_password("mfr123"),
                role="manufacturer",
                manufacturer_id=mfr_id,
            ))

        db.bulk_save_objects(users)
        db.commit()

        print(f"Seeded 1 user account + {len(top_mfrs)} manufacturer accounts.")
        print("\nDemo credentials:")
        print("  Technician  →  username: user        password: user123")
        print("  Manufacturer →  username: mfr_<id>   password: mfr123")
        print("\nTop manufacturer accounts:")
        for mfr_id, mfr_name, cnt in top_mfrs[:10]:
            print(f"  mfr_{mfr_id:<6}  {mfr_name[:50]:<50}  ({cnt} devices)")
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()
