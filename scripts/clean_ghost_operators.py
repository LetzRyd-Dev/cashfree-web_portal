from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

# Check ghost operators in app_operators:
# Operators that have:
# 1. 0 vehicles (total_vehicles == 0)
# 2. 0 drivers referencing them in app_drivers (WHERE operator_id = app_operator_id)
# 3. 0 hisaabs in app_hisaabs (WHERE app_operator_id = app_operators.app_operator_id)
# 4. 0 payments in app_payments (WHERE payer_id = app_operators.app_operator_id AND payer_type = "operator")

ghosts = db.execute(text("""
    SELECT o.app_operator_id, o.operator_id, o.company_name, o.phone, o.operator_code
    FROM app_operators o
    WHERE COALESCE(o.total_vehicles, 0) = 0
      AND NOT EXISTS (SELECT 1 FROM app_drivers d WHERE d.operator_id = o.app_operator_id)
      AND NOT EXISTS (SELECT 1 FROM app_hisaabs h WHERE h.app_operator_id = o.app_operator_id)
      AND NOT EXISTS (SELECT 1 FROM app_payments p WHERE p.payer_id = o.app_operator_id AND p.payer_type = 'operator')
""")).mappings().fetchall()

print(f"Identified {len(ghosts)} ghost operator records to purge from app_operators.")
if ghosts:
    print("Sample ghosts:")
    for g in ghosts[:5]:
        print("  ", dict(g))

# Let's verify Rubel Ahmed is among them
rubel_in_ghosts = [g for g in ghosts if g['phone'] == '6900883581']
print("Rubel Ahmed in ghosts:", [dict(r) for r in rubel_in_ghosts])

# Let's delete them cleanly
ghost_ids = [g['app_operator_id'] for g in ghosts]
if ghost_ids:
    db.execute(text("DELETE FROM app_operators WHERE app_operator_id = ANY(:ids)"), {"ids": ghost_ids})
    db.commit()
    print(f"Successfully deleted {len(ghost_ids)} ghost operators from app_operators.")

# Check remaining count
remaining = db.execute(text("SELECT count(*) FROM app_operators")).scalar()
print(f"Remaining legitimate operators in app_operators: {remaining}")

db.close()
