from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
phone = "6900883581"
ops = db.execute(text("SELECT * FROM app_operators WHERE phone = :p"), {"p": phone}).mappings().fetchall()
drvs = db.execute(text("SELECT app_driver_id, driver_code, full_name, phone FROM app_drivers WHERE phone = :p"), {"p": phone}).mappings().fetchall()
print("Operators matching 6900883581:", len(ops))
print("Drivers matching 6900883581:", len(drvs))
for d in drvs:
    print(" ", dict(d))
db.close()
