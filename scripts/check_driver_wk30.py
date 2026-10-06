from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

for did in [1, 2]:
    rows = db.execute(text("SELECT * FROM app_hisaabs WHERE app_driver_id = :did ORDER BY week_number DESC LIMIT 1"), {"did": did}).mappings().fetchall()
    for r in rows:
        print(f"Driver {did} hisaab:")
        for k in ['hisaab_number', 'week_number', 'period_start', 'period_end', 'status', 'vehicle_daily_rate', 'vehicle_rent', 'completed_trips', 'total_gross_earnings', 'total_deductions', 'current_period_os', 'to_pay', 'to_collect']:
            print(f"  {k}: {r[k]}")

db.close()
