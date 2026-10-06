from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    d_total = conn.execute(text("SELECT count(DISTINCT app_driver_id) FROM app_driver_allocations")).scalar()
    d_active = conn.execute(text("SELECT count(DISTINCT app_driver_id) FROM app_driver_allocations WHERE allocation_status = 'ACTIVE'")).scalar()
    d_returned = conn.execute(text("SELECT count(DISTINCT app_driver_id) FROM app_driver_allocations WHERE allocation_status = 'RETURNED'")).scalar()
    drv_has_veh = conn.execute(text("SELECT count(*) FROM app_drivers WHERE vehicle_reg_number IS NOT NULL AND vehicle_reg_number != ''")).scalar()
    drv_null_veh = conn.execute(text("SELECT count(*) FROM app_drivers WHERE vehicle_reg_number IS NULL OR vehicle_reg_number = ''")).scalar()

    print(f"Distinct drivers in app_driver_allocations: {d_total}")
    print(f"Distinct drivers with ACTIVE allocation: {d_active}")
    print(f"Distinct drivers with RETURNED allocation: {d_returned}")
    print(f"Drivers in app_drivers with vehicle_reg_number populated: {drv_has_veh}")
    print(f"Drivers in app_drivers with vehicle_reg_number NULL: {drv_null_veh}")

    # Check how many drivers with vehicle_reg_number populated have an active allocation vs returned allocation
    print("\nDrivers with populated vehicle_reg_number:")
    sample = conn.execute(text("""
        SELECT d.app_driver_id, d.vehicle_reg_number, a.allocation_status, a.vehicle_number
        FROM app_drivers d
        LEFT JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
        WHERE d.vehicle_reg_number IS NOT NULL
        LIMIT 5
    """)).fetchall()
    for s in sample:
        print(" ", s)
