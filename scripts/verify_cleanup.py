from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

# Check the 1 remaining overlap
remaining = db.execute(text("""
    SELECT d.app_driver_id, d.driver_code, d.full_name, d.phone, d.operator_id,
           o.app_operator_id, o.company_name, o.total_vehicles
    FROM app_drivers d
    JOIN app_operators o ON d.phone = o.phone
""")).mappings().fetchall()
for r in remaining:
    print("Remaining overlap:", dict(r))

# Quick sanity check: Gaadylo should be gone from drivers
gaadylo = db.execute(text("SELECT count(*) FROM app_drivers WHERE phone = '9004200105'")).scalar()
print(f"Gaadylo in app_drivers: {gaadylo} (should be 0)")

gaadylo_op = db.execute(text("SELECT app_operator_id, company_name, total_vehicles FROM app_operators WHERE phone = '9004200105'")).mappings().first()
print(f"Gaadylo in app_operators: {dict(gaadylo_op) if gaadylo_op else 'NOT FOUND'}")

db.close()
