from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

# First, preview what will be deleted
preview = db.execute(text("""
    SELECT d.app_driver_id, d.driver_code, d.full_name, d.phone,
           o.app_operator_id, o.company_name, o.total_vehicles
    FROM app_drivers d
    JOIN app_operators o ON d.phone = o.phone
    WHERE (o.total_vehicles IS NOT NULL AND o.total_vehicles > 0)
       OR EXISTS (SELECT 1 FROM app_hisaabs h WHERE h.app_operator_id = o.app_operator_id)
    ORDER BY o.total_vehicles DESC
""")).mappings().fetchall()

print(f"Operator phone numbers found in app_drivers (to be removed): {len(preview)}")
for r in preview[:10]:
    print(f"  app_driver_id={r['app_driver_id']} | {r['full_name']} | {r['phone']} | operator: {r['company_name']} ({r['total_vehicles']} vehicles)")

# Now delete them
res = db.execute(text("""
    DELETE FROM app_drivers
    WHERE phone IN (
        SELECT o.phone FROM app_operators o
        WHERE (o.total_vehicles IS NOT NULL AND o.total_vehicles > 0)
           OR EXISTS (SELECT 1 FROM app_hisaabs h WHERE h.app_operator_id = o.app_operator_id)
    )
"""))
db.commit()
print(f"\nDeleted {res.rowcount} operator phone entries from app_drivers.")

# Verify
remaining = db.execute(text("""
    SELECT count(*) FROM app_drivers d
    JOIN app_operators o ON d.phone = o.phone
""")).scalar()
print(f"Remaining operator-driver phone overlaps: {remaining}")

print(f"\nTotal app_drivers remaining: {db.execute(text('SELECT count(*) FROM app_drivers')).scalar()}")
print(f"Total app_operators remaining: {db.execute(text('SELECT count(*) FROM app_operators')).scalar()}")

db.close()
