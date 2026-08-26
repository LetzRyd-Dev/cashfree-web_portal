"""
seed_driver_operator_users.py
================================
Populates sample driver profiles (july_driver_users) and operator profiles (july_operator_users)
in PostgreSQL Cloud SQL so the frontend profile APIs return valid data immediately.
"""

import os
from pathlib import Path
import psycopg2

_env_path = Path(__file__).parent / ".env"
if not _env_path.exists():
    _env_path = Path(__file__).parent / "ola-sync" / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:8S5%5DU3%40L%5EXz%29%5CFH%7D@35.200.196.113:5432/postgres")
conn = psycopg2.connect(dsn=db_url)
conn.autocommit = True
cur = conn.cursor()

print("[SEED] Connected to PostgreSQL Cloud SQL!")

# 1. Driver Users
drivers = [
    ("DRV-1001", "7483731338", "Bharath B R",     "OP-501", "MH03ES4920", "2026-01-15", 6000, 5000, 1000, 0),
    ("DRV-1002", "9876543210", "Rajesh Verma",    "OP-501", "MH03ES2306", "2026-02-01", 6000, 6000, 0,    0),
    ("DRV-1003", "9876543211", "Sunil Chhetri",   "OP-502", "TS09FA1234", "2026-02-15", 6000, 4000, 2000, 500),
    ("DRV-1004", "9876543212", "Suresh Kumar",    "OP-502", "KA01MB5678", "2026-03-01", 6000, 5000, 1000, 0),
    ("DRV-1005", "9876543213", "Ramesh Babu",     "OP-501", "DL01AB3456", "2026-03-10", 6000, 6000, 0,    0),
]

for did, phone, name, op_code, veh, jdate, dep_req, dep_paid, dep_pend, owed in drivers:
    cur.execute("""
        INSERT INTO july_driver_users (
            driver_id, phone, name, operator_code, vehicle_number, joined_date,
            deposit_total_required, deposit_paid_so_far, deposit_pending, cumulative_owed
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (phone) DO UPDATE SET
            name = EXCLUDED.name,
            vehicle_number = EXCLUDED.vehicle_number,
            operator_code = EXCLUDED.operator_code,
            deposit_paid_so_far = EXCLUDED.deposit_paid_so_far,
            deposit_pending = EXCLUDED.deposit_pending,
            updated_at = NOW();
    """, (did, phone, name, op_code, veh, jdate, dep_req, dep_paid, dep_pend, owed))
    print(f"  + Driver User: {did} — {name} ({phone})")

# 2. Operator Users
operators = [
    ("OP-501", "7483731338", "Samvreeddhi Mobility Fleet", "Fleet Operator", 25000, 20000, 5000),
    ("OP-502", "9876543214", "LetzRyd Operations Ltd",      "Fleet Operator", 25000, 25000, 0),
]

for op_code, phone, name, optype, dep_req, dep_paid, dep_pend in operators:
    cur.execute("""
        INSERT INTO july_operator_users (
            operator_code, phone, operator_name, operator_type,
            deposit_total_required, deposit_paid_so_far, deposit_pending
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (phone) DO UPDATE SET
            operator_name = EXCLUDED.operator_name,
            operator_type = EXCLUDED.operator_type,
            deposit_paid_so_far = EXCLUDED.deposit_paid_so_far,
            deposit_pending = EXCLUDED.deposit_pending,
            updated_at = NOW();
    """, (op_code, phone, name, optype, dep_req, dep_paid, dep_pend))
    print(f"  + Operator User: {op_code} — {name} ({phone})")

conn.close()
print("\n[SUCCESS] Driver & Operator sample users seeded in PostgreSQL!")
