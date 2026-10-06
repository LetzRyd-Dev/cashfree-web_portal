from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

for phone in ["9140631755", "9901484683", "9691938866"]:
    d = db.execute(text(f"SELECT app_driver_id, driver_code, full_name, phone, operator_id, vehicle_reg_number FROM app_drivers WHERE phone = '{phone}'")).mappings().first()
    if d:
        print("Driver:", dict(d))
        h = db.execute(text(f"SELECT app_hisaab_id, hisaab_number, week_number, period_start, period_end, status, to_collect, to_pay FROM app_hisaabs WHERE app_driver_id = {d['app_driver_id']} ORDER BY week_number DESC")).mappings().fetchall()
        print(" Hisaabs:", len(h))
        for row in h:
            print("   ", dict(row))
    else:
        op = db.execute(text(f"SELECT app_operator_id, operator_code, company_name, phone FROM app_operators WHERE phone = '{phone}'")).mappings().first()
        print("Operator:", dict(op) if op else "None")
        if op:
            h = db.execute(text(f"SELECT app_hisaab_id, hisaab_number, week_number, period_start, period_end, status, to_collect, to_pay FROM app_hisaabs WHERE app_operator_id = {op['app_operator_id']} ORDER BY week_number DESC")).mappings().fetchall()
            print(" Operator Hisaabs:", len(h))
            for row in h:
                print("   ", dict(row))
db.close()
