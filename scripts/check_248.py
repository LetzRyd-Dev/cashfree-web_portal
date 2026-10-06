from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== INSPECTING THE 248 DRIVERS ===")
    q = """
        SELECT d.app_driver_id, d.driver_code, d.full_name, d.phone,
               a.app_allocation_id, a.vehicle_number, a.allocation_status, a.allocation_date
        FROM app_drivers d
        JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
        WHERE d.vehicle_reg_number IS NULL OR d.vehicle_reg_number = ''
        LIMIT 15;
    """
    rows = conn.execute(text(q)).fetchall()
    for r in rows:
        print(" ", r)

    # Why did our UPDATE not update them?
    # Let's check: in latest_alloc:
    # WHERE a.vehicle_number IS NOT NULL AND a.vehicle_number != ''
    # Does 'a.vehicle_number' have whitespace? Or does it fail regex?
    empty_veh = conn.execute(text("""
        SELECT count(*)
        FROM app_drivers d
        JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
        WHERE (d.vehicle_reg_number IS NULL OR d.vehicle_reg_number = '')
          AND (a.vehicle_number IS NULL OR TRIM(a.vehicle_number) = '')
    """)).scalar()
    print("Allocations with empty or whitespace vehicle_number:", empty_veh)

    # Let's check what a.vehicle_number looks like for these 248 drivers:
    sample_veh_nums = conn.execute(text("""
        SELECT DISTINCT a.vehicle_number
        FROM app_drivers d
        JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
        WHERE d.vehicle_reg_number IS NULL OR d.vehicle_reg_number = ''
        LIMIT 10;
    """)).fetchall()
    print("Sample vehicle_numbers from their allocations:", sample_veh_nums)
