from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

phone = "6900883581"
ops = db.execute(text("SELECT * FROM app_operators WHERE phone = :p"), {"p": phone}).mappings().fetchall()
drvs = db.execute(text("SELECT * FROM app_drivers WHERE phone = :p"), {"p": phone}).mappings().fetchall()

print(f"=== Operators matching {phone} ===")
for o in ops:
    print(dict(o))
    # check drivers under this operator
    op_id = o['app_operator_id']
    assigned = db.execute(text("SELECT app_driver_id, driver_code, full_name, vehicle_reg_number, operator_id FROM app_drivers WHERE operator_id = :oid"), {"oid": op_id}).mappings().fetchall()
    print(f"  Drivers assigned (by app_operator_id {op_id}): {len(assigned)}")
    for a in assigned:
        print("   ", dict(a))
    # check by o['operator_id']
    if o.get('operator_id') and o['operator_id'] != op_id:
        assigned2 = db.execute(text("SELECT app_driver_id, driver_code, full_name, vehicle_reg_number, operator_id FROM app_drivers WHERE operator_id = :oid"), {"oid": o['operator_id']}).mappings().fetchall()
        print(f"  Drivers assigned (by operator_id {o['operator_id']}): {len(assigned2)}")

print(f"\n=== Drivers matching {phone} ===")
for d in drvs:
    print(dict(d))
    # check hisaabs
    h = db.execute(text("SELECT app_hisaab_id, hisaab_number, week_number, period_start, period_end, status FROM app_hisaabs WHERE app_driver_id = :did ORDER BY week_number DESC"), {"did": d['app_driver_id']}).mappings().fetchall()
    print(f"  Hisaabs for driver {d['app_driver_id']}: {len(h)}")
    for row in h[:3]:
        print("   ", dict(row))

# Check source tables for Rubel Ahmed
print("\n=== Check raw/source tables ===")
core_alloc = db.execute(text("SELECT * FROM core_vehicle_allocation WHERE primary_contact_number = :p OR driver_contact_number = :p"), {"p": phone}).mappings().fetchall()
print(f"core_vehicle_allocation: {len(core_alloc)}")
for c in core_alloc:
    print(" ", dict(c))

july_onb = db.execute(text("SELECT * FROM july_form_onboarding WHERE contact_number = :p"), {"p": phone}).mappings().fetchall()
print(f"july_form_onboarding: {len(july_onb)}")
for j in july_onb:
    print(" ", dict(j))

db.close()
