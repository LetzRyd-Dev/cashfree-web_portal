from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== CHECKING DRIVERS WITH PLACEHOLDER / MISSING MANAGER ===")
    
    # Check what POCs the 466 placeholder drivers have in core_vehicle_allocation
    q_poc_check = """
        SELECT cva.vehicle_manager_poc, cva.city, count(*)
        FROM app_drivers d
        JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
        JOIN core_vehicle_allocation cva ON a.core_allocation_id = cva.id
        WHERE d.assigned_manager_name IS NULL 
           OR d.assigned_manager_name = ''
           OR d.assigned_manager_name = 'LetzRyd Fleet Operations'
        GROUP BY cva.vehicle_manager_poc, cva.city
        ORDER BY count(*) DESC;
    """
    res = conn.execute(text(q_poc_check)).fetchall()
    print("POCs for placeholder / missing manager drivers:")
    for r in res:
        print(" ", r)

    # What about the 16 drivers with IS NULL manager?
    q_null_mgr = """
        SELECT d.app_driver_id, d.full_name, d.phone, d.assigned_manager_name, d.assigned_manager_phone, d.operator_id
        FROM app_drivers d
        WHERE d.assigned_manager_name IS NULL 
           OR d.assigned_manager_name = ''
           OR d.assigned_manager_phone IS NULL 
           OR d.assigned_manager_phone = '';
    """
    res_null = conn.execute(text(q_null_mgr)).fetchall()
    print("\nThe 16 drivers without manager name or phone:")
    for r in res_null:
        print(" ", r)
