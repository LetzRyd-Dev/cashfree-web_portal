from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== app_drivers columns ===")
    for c in conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'app_drivers' ORDER BY ordinal_position")).fetchall():
        print(f"  {c[0]} ({c[1]})")

    print("\n=== app_driver_allocations columns ===")
    for c in conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'app_driver_allocations' ORDER BY ordinal_position")).fetchall():
        print(f"  {c[0]} ({c[1]})")

    print("\n=== core_vehicle_allocation columns ===")
    for c in conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'core_vehicle_allocation' ORDER BY ordinal_position")).fetchall():
        print(f"  {c[0]} ({c[1]})")
