import sys
sys.stdout.reconfigure(encoding='utf-8')
from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

print("=== core_rental_plans ===")
crp = db.execute(text("SELECT * FROM core_rental_plans LIMIT 10")).mappings().fetchall()
for r in crp:
    print(" ", dict(r))

print("\n=== Sample core_vehicle_allocation plans ===")
cvp = db.execute(text("SELECT driver_plan, type_of_plan, rental_plan, count(*) FROM core_vehicle_allocation GROUP BY driver_plan, type_of_plan, rental_plan ORDER BY count(*) DESC LIMIT 10")).fetchall()
for r in cvp:
    print(" ", r)

print("\n=== Check app_hisaabs financial figures across weeks ===")
h_summary = db.execute(text("""
    SELECT week_number, 
           count(*) as count,
           avg(total_gross_earnings) as avg_gross,
           avg(total_deductions) as avg_deduct,
           avg(to_pay) as avg_to_pay,
           avg(to_collect) as avg_to_collect
    FROM app_hisaabs
    GROUP BY week_number
    ORDER BY week_number DESC
    LIMIT 10
""")).fetchall()
for h in h_summary:
    print(" ", h)

print("\n=== Check app_operators financial figures ===")
op_fin = db.execute(text("""
    SELECT 
        count(*) as total_ops,
        count(CASE WHEN cw_to_collect > 0 THEN 1 END) as collect_gt_0,
        count(CASE WHEN cw_to_pay > 0 THEN 1 END) as pay_gt_0,
        count(CASE WHEN cw_fleet_net_os != 0 THEN 1 END) as os_non_zero
    FROM app_operators
""")).mappings().first()
print("app_operators financial breakdown:", dict(op_fin))

db.close()
