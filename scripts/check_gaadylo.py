from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

phone = "9004200105"
op = db.execute(text("SELECT app_operator_id, operator_code, company_name, phone, total_vehicles FROM app_operators WHERE phone = :p"), {"p": phone}).mappings().first()
drv = db.execute(text("SELECT app_driver_id, driver_code, full_name, phone, operator_id, vehicle_reg_number FROM app_drivers WHERE phone = :p"), {"p": phone}).mappings().first()
print("Operator:", dict(op) if op else None)
print("Driver:", dict(drv) if drv else None)
db.close()
