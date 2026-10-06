from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== Distinct assigned_manager_name, phone in app_drivers ===")
    res = conn.execute(text("""
        SELECT assigned_manager_name, assigned_manager_phone, count(*) 
        FROM app_drivers 
        WHERE assigned_manager_name IS NOT NULL
        GROUP BY assigned_manager_name, assigned_manager_phone
        ORDER BY count(*) DESC
        LIMIT 25
    """)).fetchall()
    for r in res:
        print(" ", r)

    print("\n=== Drivers with missing manager name or phone ===")
    missing_mgr = conn.execute(text("""
        SELECT count(*) FROM app_drivers 
        WHERE assigned_manager_name IS NULL OR assigned_manager_name = ''
           OR assigned_manager_phone IS NULL OR assigned_manager_phone = ''
    """)).scalar()
    print("Drivers without manager name or phone:", missing_mgr)

    # What if assigned_manager_name is 'LetzRyd Fleet Operations'?
    # Remember sync_db_profiles.py line 26:
    # UPDATE app_drivers SET assigned_manager_name = 'LetzRyd Fleet Operations', assigned_manager_phone = '080-4568-1234' WHERE assigned_manager_name IS NULL OR assigned_manager_name = ''
    # That was just a generic placeholder!
    placeholder_mgr = conn.execute(text("""
        SELECT count(*) FROM app_drivers 
        WHERE assigned_manager_name = 'LetzRyd Fleet Operations'
    """)).scalar()
    print("Drivers with generic placeholder 'LetzRyd Fleet Operations':", placeholder_mgr)

    # What about operators?
    op_mgr = conn.execute(text("""
        SELECT count(*) FROM app_operators 
        WHERE assigned_manager_name IS NULL OR assigned_manager_name = ''
           OR assigned_manager_phone IS NULL OR assigned_manager_phone = ''
           OR assigned_manager_name = 'LetzRyd Fleet Operations'
    """)).scalar()
    print("Operators without real manager or with placeholder:", op_mgr)

