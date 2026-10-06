from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

# How many cases like this exist:
# A phone is in app_operators AND also in app_drivers where operator_id = that same app_operator_id
# i.e. the fleet owner also appears as a driver under their own fleet

overlap = db.execute(text("""
    SELECT 
        o.app_operator_id, o.company_name, o.phone, o.total_vehicles,
        d.app_driver_id, d.driver_code, d.operator_id, d.vehicle_reg_number
    FROM app_operators o
    JOIN app_drivers d ON o.phone = d.phone
    ORDER BY o.total_vehicles DESC
""")).mappings().fetchall()

print(f"Total operators who also appear as drivers: {len(overlap)}")
print("\nBreakdown:")
print("  Operators with vehicles > 0:")
veh_gt0 = [r for r in overlap if (r['total_vehicles'] or 0) > 0]
print(f"    {len(veh_gt0)} cases (the REAL overlap problem)")
for r in veh_gt0[:5]:
    print("   ", dict(r))

print("  Operators with 0 vehicles (leftover ghosts from our cleanup):")
veh_0 = [r for r in overlap if (r['total_vehicles'] or 0) == 0]
print(f"    {len(veh_0)} cases")

db.close()
