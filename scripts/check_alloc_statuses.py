from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== Checking app_driver_allocations dropoff_date vs core_dropoffs ===")
    
    # In app_driver_allocations:
    res = conn.execute(text("""
        SELECT 
            count(*) as total,
            count(CASE WHEN dropoff_date IS NOT NULL THEN 1 END) as with_dropoff,
            count(CASE WHEN dropoff_date IS NULL THEN 1 END) as without_dropoff,
            count(CASE WHEN allocation_status = 'ACTIVE' THEN 1 END) as active_count,
            count(CASE WHEN allocation_status = 'RETURNED' THEN 1 END) as returned_count
        FROM app_driver_allocations
    """)).mappings().first()
    print(dict(res))

    # For the 1895 drivers missing vehicle_reg_number:
    # What are the statuses of ALL allocations for these drivers?
    res2 = conn.execute(text("""
        SELECT a.allocation_status, count(*)
        FROM app_drivers d
        JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
        WHERE d.vehicle_reg_number IS NULL
        GROUP BY a.allocation_status
    """)).fetchall()
    print("All allocations for NULL vehicle drivers:", res2)

    # For the 402 drivers WITH vehicle_reg_number:
    # What are the statuses of their allocations?
    res3 = conn.execute(text("""
        SELECT a.allocation_status, count(*)
        FROM app_drivers d
        JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
        WHERE d.vehicle_reg_number IS NOT NULL AND d.vehicle_reg_number != ''
        GROUP BY a.allocation_status
    """)).fetchall()
    print("All allocations for populated vehicle drivers:", res3)
