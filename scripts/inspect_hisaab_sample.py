from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

# Inspect one existing week 40 hisaab from app_hisaabs
row = db.execute(text("SELECT * FROM app_hisaabs WHERE week_number = 40 LIMIT 1")).mappings().first()
if row:
    print("Sample Week 40 hisaab columns and values:")
    for k, v in dict(row).items():
        print(f"  {k}: {repr(v)}")
else:
    # check latest hisaab in table
    row = db.execute(text("SELECT * FROM app_hisaabs ORDER BY week_number DESC LIMIT 1")).mappings().first()
    print("Sample latest hisaab:")
    for k, v in dict(row).items():
        print(f"  {k}: {repr(v)}")

db.close()
