from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# 1. Update missing contact_person_name in app_operators
res1 = db.execute(text("UPDATE app_operators SET contact_person_name = company_name WHERE contact_person_name IS NULL OR contact_person_name = ''"))
print('Operators contact_person_name updated:', res1.rowcount)

# 2. Sync driver address from operator where available
res2 = db.execute(text("UPDATE app_drivers d SET address = o.address FROM app_operators o WHERE d.phone = o.phone AND (d.address IS NULL OR d.address = '') AND o.address IS NOT NULL AND o.address != ''"))
print('Driver addresses synced from operators:', res2.rowcount)

# 3. Default address for remaining drivers and operators with null address
res3 = db.execute(text("UPDATE app_operators SET address = 'LetzRyd Operations Hub, Bengaluru' WHERE address IS NULL OR address = ''"))
print('Operators default address set:', res3.rowcount)

res4 = db.execute(text("UPDATE app_drivers SET address = 'LetzRyd Operations Hub, Bengaluru' WHERE address IS NULL OR address = ''"))
print('Drivers default address set:', res4.rowcount)

# 4. Sync assigned manager from fleet operator
res5 = db.execute(text("UPDATE app_drivers d SET assigned_manager_name = COALESCE(NULLIF(o.company_name, ''), o.contact_person_name, 'Fleet Operations'), assigned_manager_phone = COALESCE(NULLIF(o.phone, ''), '080-4568-1234') FROM app_operators o WHERE (d.operator_id = o.app_operator_id OR d.operator_id = o.operator_id) AND d.operator_id > 0 AND (d.assigned_manager_name IS NULL OR d.assigned_manager_name = '')"))
print('Managed drivers manager synced:', res5.rowcount)

# 5. Default manager for independent drivers
res6 = db.execute(text("UPDATE app_drivers SET assigned_manager_name = 'LetzRyd Fleet Operations', assigned_manager_phone = '080-4568-1234' WHERE assigned_manager_name IS NULL OR assigned_manager_name = ''"))
print('Independent drivers default manager set:', res6.rowcount)

# 6. Default manager for operators
res7 = db.execute(text("UPDATE app_operators SET assigned_manager_name = 'LetzRyd Fleet Operations', assigned_manager_phone = '080-4568-1234' WHERE assigned_manager_name IS NULL OR assigned_manager_name = ''"))
print('Operators default manager set:', res7.rowcount)

db.commit()
db.close()
print("Synchronization completed successfully.")
