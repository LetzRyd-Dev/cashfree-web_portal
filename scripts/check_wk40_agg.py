from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

# Check what week 40 hisaabs look like across all drivers
wk40_summary = db.execute(text("""
    SELECT 
        count(*) as total_hisaabs,
        count(DISTINCT app_driver_id) as distinct_drivers,
        sum(to_pay) as total_to_pay,
        sum(to_collect) as total_to_collect
    FROM app_hisaabs
    WHERE week_number = 40
""")).mappings().first()
print("Week 40 in app_hisaabs:", dict(wk40_summary))

# Check operator hisaab aggregation from week 40
op_agg = db.execute(text("""
    SELECT 
        d.operator_id,
        count(DISTINCT d.app_driver_id) as driver_count,
        sum(h.to_pay) as fleet_to_pay,
        sum(h.to_collect) as fleet_to_collect
    FROM app_hisaabs h
    JOIN app_drivers d ON h.app_driver_id = d.app_driver_id
    WHERE h.week_number = 40 AND d.operator_id IS NOT NULL AND d.operator_id > 0
    GROUP BY d.operator_id
    ORDER BY driver_count DESC
    LIMIT 10
""")).mappings().fetchall()
print("\nSample Operator Week 40 aggregations:")
for o in op_agg:
    print(" ", dict(o))

db.close()
