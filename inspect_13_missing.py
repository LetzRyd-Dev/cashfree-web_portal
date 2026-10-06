from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
res = db.execute(text("""
    SELECT d.app_driver_id, d.phone, d.full_name, a.vehicle_number, a.allocation_status, a.app_allocation_id
    FROM app_drivers d
    JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
    WHERE a.allocation_status = 'ACTIVE' AND (d.vehicle_reg_number IS NULL OR d.vehicle_reg_number = '')
""")).fetchall()
print('Found missing:', len(res))
for r in res:
    print(r)
db.close()
