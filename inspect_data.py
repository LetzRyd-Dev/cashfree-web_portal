from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    print('--- COUNT OF APP_DRIVERS AND APP_OPERATORS ---')
    drv_cnt = conn.execute(text('SELECT count(*), count(distinct phone), count(distinct driver_code) FROM app_drivers')).fetchone()
    op_cnt = conn.execute(text('SELECT count(*), count(distinct phone), count(distinct operator_code) FROM app_operators')).fetchone()
    print('app_drivers (total, distinct_phone, distinct_code):', drv_cnt)
    print('app_operators (total, distinct_phone, distinct_code):', op_cnt)

    print('\n--- MUBASHIR KK IN DRIVERS ---')
    rows = conn.execute(text("SELECT app_driver_id, driver_code, full_name, phone, operator_id, assigned_manager_name FROM app_drivers WHERE full_name ILIKE '%Mubashir%' OR phone LIKE '%8848086860%'")).fetchall()
    for r in rows:
        print(dict(r._mapping))

    print('\n--- MUBASHIR KK IN OPERATORS ---')
    rows = conn.execute(text("SELECT app_operator_id, operator_code, company_name, contact_person_name, phone FROM app_operators WHERE company_name ILIKE '%Mubashir%' OR contact_person_name ILIKE '%Mubashir%' OR phone LIKE '%8848086860%'")).fetchall()
    for r in rows:
        print(dict(r._mapping))

    print('\n--- SAMPLE DRIVER CODES ---')
    rows = conn.execute(text("SELECT app_driver_id, driver_code, full_name, phone FROM app_drivers LIMIT 10")).fetchall()
    for r in rows:
        print(dict(r._mapping))

    print('\n--- SAMPLE OPERATOR CODES ---')
    rows = conn.execute(text("SELECT app_operator_id, operator_code, company_name, contact_person_name, phone FROM app_operators LIMIT 10")).fetchall()
    for r in rows:
        print(dict(r._mapping))

    print('\n--- PHONE OVERLAP BETWEEN DRIVERS AND OPERATORS ---')
    overlap = conn.execute(text("SELECT d.phone, d.full_name as driver_name, o.company_name as operator_company FROM app_drivers d JOIN app_operators o ON d.phone = o.phone")).fetchall()
    print(f"Total overlapping phone numbers: {len(overlap)}")
    for r in overlap[:15]:
        print(dict(r._mapping))
