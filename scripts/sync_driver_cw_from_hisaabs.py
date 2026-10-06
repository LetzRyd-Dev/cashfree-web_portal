from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

# Sync app_drivers from the latest hisaab in app_hisaabs
# Find latest week for each driver
update_sql = """
WITH latest_hisaab AS (
    SELECT DISTINCT ON (app_driver_id)
        app_driver_id,
        week_number,
        completed_trips,
        total_gross_earnings,
        total_deductions,
        to_pay,
        to_collect,
        current_period_os,
        status
    FROM app_hisaabs
    WHERE app_driver_id IS NOT NULL
    ORDER BY app_driver_id, week_number DESC
)
UPDATE app_drivers d
SET 
    cw_trips = COALESCE(lh.completed_trips, 0),
    cw_gross_earnings = COALESCE(lh.total_gross_earnings, 0.00),
    cw_total_deductions = COALESCE(lh.total_deductions, 0.00),
    cw_to_pay = COALESCE(lh.to_pay, 0.00),
    cw_to_collect = COALESCE(lh.to_collect, 0.00),
    cw_os = COALESCE(lh.to_collect, 0.00)
FROM latest_hisaab lh
WHERE d.app_driver_id = lh.app_driver_id;
"""

res = db.execute(text(update_sql))
db.commit()
print(f"Updated app_drivers from latest hisaabs: {res.rowcount} drivers updated.")

# Also update app_drivers rental plan and rate from core_vehicle_allocation where available
plan_sync_sql = """
WITH active_plan AS (
    SELECT DISTINCT ON (c.app_driver_id)
        c.app_driver_id,
        c.rental_plan,
        c.type_of_plan,
        c.driver_plan
    FROM app_driver_allocations c
    WHERE c.app_driver_id IS NOT NULL AND c.is_active = true
    ORDER BY c.app_driver_id, c.app_allocation_id DESC
)
SELECT count(*) FROM active_plan;
"""
active_p = db.execute(text(plan_sync_sql)).scalar()
print(f"Active driver allocations with plan: {active_p}")

db.close()
