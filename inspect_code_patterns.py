from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    print("--- DRIVER CODE PREFIX PATTERNS ---")
    driver_codes = conn.execute(text("SELECT SUBSTRING(driver_code FROM 1 FOR 7) as prefix, count(*) FROM app_drivers GROUP BY SUBSTRING(driver_code FROM 1 FOR 7) ORDER BY count(*) DESC")).fetchall()
    for r in driver_codes:
        print(dict(r._mapping))

    print("\n--- OPERATOR CODE PREFIX PATTERNS ---")
    op_codes = conn.execute(text("SELECT SUBSTRING(operator_code FROM 1 FOR 7) as prefix, count(*) FROM app_operators GROUP BY SUBSTRING(operator_code FROM 1 FOR 7) ORDER BY count(*) DESC")).fetchall()
    for r in op_codes:
        print(dict(r._mapping))
