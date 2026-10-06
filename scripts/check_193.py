from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== INVESTIGATING THE 193 MISSING DRIVERS ===")
    
    q = """
        SELECT d.app_driver_id, d.full_name, d.phone, d.vehicle_reg_number, a.app_allocation_id, a.vehicle_number, a.allocation_status, a.allocation_date
        FROM app_drivers d 
        JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id 
        WHERE a.allocation_status = 'ACTIVE' 
          AND (d.vehicle_reg_number IS NULL OR d.vehicle_reg_number = '')
          AND d.is_active = TRUE
        LIMIT 10;
    """
    rows = conn.execute(text(q)).fetchall()
    print("Sample missing rows:")
    for r in rows:
        print(" ", r)

    # Why didn't our update touch them?
    # Let's check our update query:
    # WITH latest_alloc AS (
    #     SELECT DISTINCT ON (a.app_driver_id) ...
    # )
    # UPDATE app_drivers d ...
    # Did the latest_alloc pick an allocation where vehicle_number was NULL, OR did multiple allocations exist?
    sample_did = rows[0][0]
    print(f"\nAll allocations for did={sample_did}:")
    all_alloc = conn.execute(text(f"""
        SELECT app_allocation_id, vehicle_number, allocation_date, allocation_status
        FROM app_driver_allocations
        WHERE app_driver_id = {sample_did}
        ORDER BY allocation_date DESC, app_allocation_id DESC
    """)).fetchall()
    for aa in all_alloc:
        print(" ", aa)
