from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
phone = "6900883581"
ops = db.execute(text("SELECT * FROM app_operators WHERE phone = :p"), {"p": phone}).mappings().fetchall()
for o in ops:
    print(dict(o))
db.close()
