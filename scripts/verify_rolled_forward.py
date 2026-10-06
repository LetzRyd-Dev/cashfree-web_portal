from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

for phone in ["9140631755", "9901484683"]:
    d = db.execute(text("SELECT app_driver_id, full_name, cw_os, cw_to_collect, cw_to_pay FROM app_drivers WHERE phone = :p"), {"p": phone}).mappings().first()
    print(dict(d))
    h = db.execute(text("SELECT week_number, period_start, period_end, status, to_pay, to_collect FROM app_hisaabs WHERE app_driver_id = :did ORDER BY week_number DESC LIMIT 3"), {"did": d['app_driver_id']}).mappings().fetchall()
    for row in h:
        print("  ", dict(row))

db.close()
