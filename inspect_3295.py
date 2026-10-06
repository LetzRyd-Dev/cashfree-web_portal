from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    print("--- APP DRIVER 3295 ---")
    row = conn.execute(text("SELECT * FROM app_drivers WHERE app_driver_id = 3295")).fetchone()
    if row:
        print(dict(row._mapping))

    print("\n--- APP OPERATORS WITH ID 432 ---")
    rows = conn.execute(text("SELECT * FROM app_operators WHERE app_operator_id = 432 OR operator_id = 432")).fetchall()
    for r in rows:
        print(dict(r._mapping))
