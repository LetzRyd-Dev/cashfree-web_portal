from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

# Check sample operators and where their IDs or data came from
ops = db.execute(text("SELECT app_operator_id, operator_id, operator_code, company_name, phone, operator_type FROM app_operators ORDER BY app_operator_id LIMIT 10")).mappings().fetchall()
for o in ops:
    print(dict(o))

# Check how operator_type is distributed
types = db.execute(text("SELECT operator_type, count(*) FROM app_operators GROUP BY operator_type")).fetchall()
print("Operator types:", types)

# Check why Rubel Ahmed is in app_operators
rubel = db.execute(text("SELECT * FROM app_operators WHERE phone = '6900883581'")).mappings().first()
print("Rubel in app_operators:", dict(rubel) if rubel else None)

# Where does operator_id = 438 come from?
chk_438 = db.execute(text("SELECT * FROM drivers WHERE id = 438 OR driver_id = 438")).mappings().fetchall() if 'drivers' in tables else []
print("In drivers table with id 438:", len(chk_438))

db.close()
