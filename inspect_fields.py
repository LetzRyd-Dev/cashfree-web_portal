from app.database import SessionLocal
from sqlalchemy import text
from app.models.app_models import AppDrivers, AppOperators

db = SessionLocal()
tables = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")).fetchall()
print("Tables in DB:", [t[0] for t in tables])

# Check how addresses and manager names are populated in app_drivers and app_operators
drv_addr_null = db.query(AppDrivers).filter(AppDrivers.address == None).count()
drv_addr_empty = db.query(AppDrivers).filter(AppDrivers.address == '').count()
drv_total = db.query(AppDrivers).count()
print(f"Drivers: total={drv_total}, null_address={drv_addr_null}, empty_address={drv_addr_empty}")

op_addr_null = db.query(AppOperators).filter(AppOperators.address == None).count()
op_addr_empty = db.query(AppOperators).filter(AppOperators.address == '').count()
op_total = db.query(AppOperators).count()
print(f"Operators: total={op_total}, null_address={op_addr_null}, empty_address={op_addr_empty}")

drv_mgr_null = db.query(AppDrivers).filter(AppDrivers.assigned_manager_name == None).count()
print(f"Drivers: null_manager={drv_mgr_null}")

op_mgr_null = db.query(AppOperators).filter(AppOperators.assigned_manager_name == None).count()
print(f"Operators: null_manager={op_mgr_null}")

# Check our 4 archetypes specifically:
phones = ["9656907001", "9640404017", "7899861394", "8008663719", "6206009022", "7400234053"]
for p in phones:
    d = db.query(AppDrivers).filter(AppDrivers.phone == p).first()
    o = db.query(AppOperators).filter(AppOperators.phone == p).first()
    print(f"\n--- Phone {p} ---")
    if d:
        print(f"  Driver: name={d.full_name}, veh={d.vehicle_reg_number}, mgr={d.assigned_manager_name}, addr={d.address}, op_id={d.operator_id}")
    if o:
        print(f"  Operator: comp={o.company_name}, contact={o.contact_person_name}, mgr={o.assigned_manager_name}, addr={o.address}")

db.close()
