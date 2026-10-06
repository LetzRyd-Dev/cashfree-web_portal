from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

query = """
UPDATE app_drivers d
SET vehicle_reg_number = sub.vehicle_number,
    current_allocation_id = sub.app_allocation_id,
    vehicle_allocated_from = sub.allocation_date
FROM (
    SELECT DISTINCT ON (app_driver_id) app_driver_id, vehicle_number, app_allocation_id, allocation_date
    FROM app_driver_allocations
    WHERE allocation_status = 'ACTIVE' AND vehicle_number IS NOT NULL AND vehicle_number != ''
    ORDER BY app_driver_id, app_allocation_id DESC
) sub
WHERE d.app_driver_id = sub.app_driver_id
  AND (d.vehicle_reg_number IS NULL OR d.vehicle_reg_number = '');
"""

res = db.execute(text(query))
print("Updated drivers with active allocations:", res.rowcount)
db.commit()

# Verify remaining missing
remaining = db.execute(text("""
    SELECT count(*) 
    FROM app_drivers d 
    JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id 
    WHERE a.allocation_status = 'ACTIVE' AND (d.vehicle_reg_number IS NULL OR d.vehicle_reg_number = '')
""")).scalar()
print("Remaining active allocations missing in app_drivers:", remaining)

db.close()
