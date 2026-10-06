from app.database import SessionLocal
from sqlalchemy import text
from app.models.app_models import AppDrivers, AppOperators

db = SessionLocal()

print("--- Active drivers missing vehicle_reg_number ---")
res = db.execute(text("""
    SELECT d.app_driver_id, d.driver_id, d.phone, d.full_name, d.is_active, d.vehicle_reg_number, d.current_vehicle_id, d.current_allocation_id
    FROM app_drivers d
    WHERE d.is_active = true AND (d.vehicle_reg_number IS NULL OR d.vehicle_reg_number = '')
    LIMIT 10
""")).fetchall()
for r in res:
    print(r)

# Check if vehicle allocation table has allocations for these drivers
print("\n--- Checking allocations for some of these drivers ---")
sample_ids = [r[0] for r in res[:5]]
for did in sample_ids:
    alloc = db.execute(text(f"""
        SELECT * FROM app_driver_allocations WHERE app_driver_id = {did}
    """)).fetchall()
    print(f"app_driver_allocations for did={did}:", alloc)

# Check core_vehicle_allocation
for r in res[:5]:
    phone = r[2]
    c_alloc = db.execute(text(f"""
        SELECT vehicle_number, driver_name, phone, status, start_date, end_date
        FROM core_vehicle_allocation
        WHERE phone LIKE '%{phone[-10:]}%'
    """)).fetchall()
    print(f"core_vehicle_allocation for phone={phone}:", c_alloc)

# Check active operators with missing company name or contact
op_missing = db.execute(text("""
    SELECT app_operator_id, operator_code, phone, company_name, contact_person_name, is_active
    FROM app_operators
    WHERE is_active = true AND (company_name IS NULL OR company_name = '' OR contact_person_name IS NULL OR contact_person_name = '')
""")).fetchall()
print(f"\nActive operators missing company or contact ({len(op_missing)}):")
for om in op_missing:
    print(om)

db.close()
