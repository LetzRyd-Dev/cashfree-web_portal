from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== vehicles table columns ===")
    for c in conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'vehicles' ORDER BY ordinal_position")).fetchall():
        print(f"  {c[0]} ({c[1]})")

    sample_veh = conn.execute(text("SELECT * FROM vehicles LIMIT 2")).mappings().fetchall()
    print("Sample vehicles:")
    for sv in sample_veh:
        print(" ", dict(sv))

    print("\n=== core_vehicle_onboarding columns ===")
    for c in conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'core_vehicle_onboarding' ORDER BY ordinal_position")).fetchall():
        print(f"  {c[0]} ({c[1]})")

    print("\n=== vehicle_models columns ===")
    for c in conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'vehicle_models' ORDER BY ordinal_position")).fetchall():
        print(f"  {c[0]} ({c[1]})")
