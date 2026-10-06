from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

print("=== Distribution of vehicle_daily_rate in app_drivers ===")
rates = db.execute(text("SELECT vehicle_daily_rate, count(*) FROM app_drivers GROUP BY vehicle_daily_rate ORDER BY count(*) DESC LIMIT 10")).fetchall()
for r in rates:
    print(" ", r)

print("\n=== Check rental rate in app_driver_allocations ===")
alloc_rates = db.execute(text("SELECT daily_rental_rate, count(*) FROM app_driver_allocations GROUP BY daily_rental_rate ORDER BY count(*) DESC LIMIT 10")).fetchall()
for r in alloc_rates:
    print(" ", r)

print("\n=== Check rental plan in core_vehicle_allocation ===")
core_rates = db.execute(text("SELECT rent_amount, count(*) FROM core_vehicle_allocation GROUP BY rent_amount ORDER BY count(*) DESC LIMIT 10")).fetchall()
for r in core_rates:
    print(" ", r)

print("\n=== Check cw_to_collect / cw_os in app_drivers ===")
drv_os = db.execute(text("""
    SELECT 
        count(*) as total,
        count(cw_os) as non_null_os,
        count(cw_to_collect) as non_null_collect,
        count(CASE WHEN cw_to_collect > 0 THEN 1 END) as positive_collect,
        count(CASE WHEN cw_to_pay > 0 THEN 1 END) as positive_pay
    FROM app_drivers
""")).mappings().first()
print("app_drivers financial columns:", dict(drv_os))

print("\n=== Check app_hisaabs for week 40 ===")
wk40 = db.execute(text("""
    SELECT 
        count(*) as total_wk40,
        count(CASE WHEN to_collect > 0 THEN 1 END) as collect_gt_0,
        count(CASE WHEN to_pay > 0 THEN 1 END) as pay_gt_0,
        count(CASE WHEN to_collect = 0 AND to_pay = 0 THEN 1 END) as zero_zero
    FROM app_hisaabs
    WHERE week_number = 40
""")).mappings().first()
print("Week 40 hisaabs breakdown:", dict(wk40))

db.close()
