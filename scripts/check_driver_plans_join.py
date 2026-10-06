from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

sample = db.execute(text("""
    SELECT d.app_driver_id, d.full_name, d.phone, d.vehicle_reg_number,
           c.type_of_plan, c.rental_plan, c.driver_plan
    FROM app_drivers d
    JOIN core_vehicle_allocation c ON d.phone = c.driver_phone
    LIMIT 10
""")).mappings().fetchall()

for s in sample:
    print(dict(s))

db.close()
