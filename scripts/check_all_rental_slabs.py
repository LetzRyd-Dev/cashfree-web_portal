from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

print("=== portal_rental_plans ===")
res = db.execute(text("SELECT * FROM portal_rental_plans LIMIT 5")).mappings().fetchall()
for r in res:
    print(dict(r))

print("\n=== rental_rate_slabs ===")
res2 = db.execute(text("SELECT * FROM rental_rate_slabs LIMIT 5")).mappings().fetchall()
for r in res2:
    print(dict(r))

print("\n=== rental_model_baselines ===")
res3 = db.execute(text("SELECT * FROM rental_model_baselines LIMIT 5")).mappings().fetchall()
for r in res3:
    print(dict(r))

db.close()
