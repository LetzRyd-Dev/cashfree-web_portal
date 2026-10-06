from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== INSPECTING DROP-OFFS & LATEST ALLOCATIONS ===")
    
    # How many drivers in app_drivers have hisaabs (active earnings)?
    drvs_with_hisaab = conn.execute(text("""
        SELECT count(DISTINCT d.app_driver_id)
        FROM app_drivers d
        JOIN app_hisaabs h ON d.app_driver_id = h.app_driver_id
        WHERE d.vehicle_reg_number IS NULL
    """)).scalar()
    print("Drivers with NULL vehicle_reg who have hisaabs:", drvs_with_hisaab)

    # What are the latest allocations for drivers where vehicle_reg_number IS NULL?
    # Are there any active allocations for them?
    active_allocs_for_null_drv = conn.execute(text("""
        SELECT count(DISTINCT d.app_driver_id)
        FROM app_drivers d
        JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
        WHERE d.vehicle_reg_number IS NULL AND a.allocation_status = 'ACTIVE'
    """)).scalar()
    print("Drivers with NULL vehicle_reg who have an ACTIVE allocation:", active_allocs_for_null_drv)

    # What if we pick the latest allocation for each driver?
    # Latest allocation order: allocation_date DESC, app_allocation_id DESC
    # If we take the latest allocation:
    latest_for_null = conn.execute(text("""
        SELECT count(*)
        FROM (
            SELECT DISTINCT ON (d.app_driver_id)
                d.app_driver_id, a.vehicle_number, a.allocation_date, a.daily_rental_rate, a.allocation_status
            FROM app_drivers d
            JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
            WHERE d.vehicle_reg_number IS NULL
            ORDER BY d.app_driver_id, 
                     CASE WHEN a.allocation_status = 'ACTIVE' THEN 1 ELSE 2 END,
                     a.allocation_date DESC, a.app_allocation_id DESC
        ) sub
    """)).scalar()
    print("Total drivers with NULL vehicle_reg who have a latest allocation in app_driver_allocations:", latest_for_null)
