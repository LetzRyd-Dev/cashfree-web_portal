from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

# How many operators have matching phone in drivers?
overlap = db.execute(text("""
    SELECT o.app_operator_id, o.operator_id, o.operator_code, o.company_name, o.phone, o.total_vehicles,
           d.app_driver_id, d.driver_id, d.driver_code, d.operator_id as driver_operator_id, d.vehicle_reg_number
    FROM app_operators o
    JOIN app_drivers d ON o.phone = d.phone
""")).mappings().fetchall()
print(f"Total phone overlap between app_operators and app_drivers: {len(overlap)}")
for r in overlap[:10]:
    print(dict(r))

# What was the original seed/migration script that created app_operators?
print("\nCheck operators with 0 vehicles:")
zero_veh = db.execute(text("SELECT count(*) FROM app_operators WHERE total_vehicles = 0")).scalar()
print("Operators with 0 vehicles:", zero_veh)
total_ops = db.execute(text("SELECT count(*) FROM app_operators")).scalar()
print("Total operators:", total_ops)

# Check operators with > 0 vehicles
with_veh = db.execute(text("SELECT count(*) FROM app_operators WHERE total_vehicles > 0")).scalar()
print("Operators with > 0 vehicles:", with_veh)

# How many operators actually have drivers in app_drivers pointing to them?
mapped_ops = db.execute(text("SELECT count(DISTINCT operator_id) FROM app_drivers WHERE operator_id IS NOT NULL AND operator_id > 0")).scalar()
print("Distinct operator_ids in app_drivers:", mapped_ops)

db.close()
