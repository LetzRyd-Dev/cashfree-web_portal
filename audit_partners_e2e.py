import sys
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.database import SessionLocal
from app.models.app_models import AppDrivers, AppOperators

db = SessionLocal()
client = TestClient(app)

print("="*60)
print("AUDIT SCRIPT RUNNING")
print("="*60)

# Check the given examples in DB
phones_to_check = {
    "pure_operator_1": "9656907001",
    "pure_operator_2": "9640404017",
    "indep_driver_1": "7899861394",
    "indep_driver_2": "8008663719",
    "managed_driver_1": "6206009022",
    "both_1": "7400234053",
}

for label, phone in phones_to_check.items():
    drv = db.query(AppDrivers).filter(AppDrivers.phone == phone).first()
    op = db.query(AppOperators).filter(AppOperators.phone == phone).first()
    print(f"\n{label} ({phone}):")
    print(f"  In app_drivers: {drv.full_name if drv else 'NONE'} | op_id: {drv.operator_id if drv else 'N/A'} | veh: {drv.vehicle_reg_number if drv else 'N/A'} | active: {drv.is_active if drv else 'N/A'}")
    print(f"  In app_operators: {op.company_name if op else 'NONE'} | contact: {op.contact_person_name if op else 'N/A'} | active: {op.is_active if op else 'N/A'}")

# Find second driver managed under operator
print("\n--- Finding managed drivers (operator_id > 1) ---")
managed_drivers = db.query(AppDrivers).filter(AppDrivers.operator_id > 1, AppDrivers.is_active == True).limit(5).all()
for md in managed_drivers:
    op = db.query(AppOperators).filter(AppOperators.app_operator_id == md.operator_id).first()
    print(f"Driver {md.phone} ({md.full_name}) -> Operator {md.operator_id} ({op.company_name if op else 'N/A'})")

# Find partners in both tables
print("\n--- Finding partners existing in BOTH tables ---")
both_phones = db.execute(text("""
    SELECT d.phone, d.full_name, o.company_name, o.contact_person_name
    FROM app_drivers d
    JOIN app_operators o ON d.phone = o.phone
    LIMIT 5
""")).fetchall()
for bp in both_phones:
    print(f"Both: Phone {bp[0]} | Driver: {bp[1]} | Op Company: {bp[2]} | Op Contact: {bp[3]}")

# Active drivers with missing vehicle registration
missing_veh_drivers = db.query(AppDrivers).filter(
    AppDrivers.is_active == True,
    (AppDrivers.vehicle_reg_number == None) | (AppDrivers.vehicle_reg_number == '')
).count()
total_active_drivers = db.query(AppDrivers).filter(AppDrivers.is_active == True).count()
print(f"\nActive drivers with missing vehicle reg: {missing_veh_drivers} / {total_active_drivers}")

# Sample of active drivers with missing vehicle reg
if missing_veh_drivers > 0:
    samples = db.query(AppDrivers).filter(
        AppDrivers.is_active == True,
        (AppDrivers.vehicle_reg_number == None) | (AppDrivers.vehicle_reg_number == '')
    ).limit(5).all()
    for s in samples:
        print(f"  Missing veh driver: {s.phone} | {s.full_name} | drv_id: {s.app_driver_id} | veh_id: {s.current_vehicle_id}")

# Active operators with missing company name or contact person
missing_comp_operators = db.query(AppOperators).filter(
    AppOperators.is_active == True,
    (AppOperators.company_name == None) | (AppOperators.company_name == '')
).count()
missing_contact_operators = db.query(AppOperators).filter(
    AppOperators.is_active == True,
    (AppOperators.contact_person_name == None) | (AppOperators.contact_person_name == '')
).count()
total_active_operators = db.query(AppOperators).filter(AppOperators.is_active == True).count()
print(f"\nActive operators with missing company name: {missing_comp_operators} / {total_active_operators}")
print(f"Active operators with missing contact person: {missing_contact_operators} / {total_active_operators}")
if missing_contact_operators > 0:
    samples = db.query(AppOperators).filter(
        AppOperators.is_active == True,
        (AppOperators.contact_person_name == None) | (AppOperators.contact_person_name == '')
    ).limit(5).all()
    for s in samples:
        print(f"  Missing contact op: {s.phone} | company: {s.company_name} | contact: {s.contact_person_name}")

db.close()
