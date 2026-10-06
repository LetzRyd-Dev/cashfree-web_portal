from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

# For Operator 475 (Gaadylo), let's aggregate their hisaabs by week_number
agg = db.execute(text("""
    SELECT 
        h.week_number,
        MIN(h.period_start) as period_start,
        MAX(h.period_end) as period_end,
        COUNT(DISTINCT h.app_driver_id) as active_vehicles,
        SUM(COALESCE(h.completed_trips, 0)) as total_trips,
        SUM(COALESCE(h.total_gross_earnings, 0)) as total_gross,
        SUM(COALESCE(h.total_deductions, 0)) as total_deductions,
        SUM(COALESCE(h.to_pay, 0)) as total_to_pay,
        SUM(COALESCE(h.to_collect, 0)) as total_to_collect,
        SUM(COALESCE(h.uber_trips, 0)) as uber_trips,
        SUM(COALESCE(h.uber_revenue, 0)) as uber_revenue,
        SUM(COALESCE(h.ola_trips, 0)) as ola_trips,
        SUM(COALESCE(h.ola_revenue, 0)) as ola_revenue,
        SUM(COALESCE(h.rapido_trips, 0)) as rapido_trips,
        SUM(COALESCE(h.rapido_revenue, 0)) as rapido_revenue,
        SUM(COALESCE(h.vehicle_rent, 0)) as total_rent
    FROM app_hisaabs h
    WHERE h.app_operator_id = 475
    GROUP BY h.week_number
    ORDER BY h.week_number DESC
    LIMIT 10
""")).mappings().fetchall()

print("Gaadylo weekly aggregates:")
for a in agg:
    print(dict(a))

db.close()
