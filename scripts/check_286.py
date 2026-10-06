from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== Checking 286 drivers without allocations ===")
    
    # Are any of them in core_vehicle_allocation?
    q_cva = """
        SELECT count(DISTINCT d.app_driver_id)
        FROM app_drivers d
        JOIN core_vehicle_allocation cva ON (
            RIGHT(REGEXP_REPLACE(COALESCE(cva.driver_phone, ''), '[^0-9]', '', 'g'), 10) = d.phone
        )
        WHERE NOT EXISTS (
            SELECT 1 FROM app_driver_allocations a WHERE a.app_driver_id = d.app_driver_id
        )
    """
    print("In core_vehicle_allocation by phone:", conn.execute(text(q_cva)).scalar())

    # Are any of them test drivers?
    q_test = """
        SELECT count(*)
        FROM app_drivers d
        WHERE NOT EXISTS (
            SELECT 1 FROM app_driver_allocations a WHERE a.app_driver_id = d.app_driver_id
        )
        AND (d.full_name ILIKE '%test%' OR d.full_name ILIKE '%fleet%' OR d.driver_code ILIKE '%TEST%')
    """
    print("Test drivers among those without allocations:", conn.execute(text(q_test)).scalar())

    # Check sample of these 286 drivers
    sample = conn.execute(text("""
        SELECT d.app_driver_id, d.driver_code, d.full_name, d.phone, d.operator_id, d.joined_date, d.created_at
        FROM app_drivers d
        WHERE NOT EXISTS (
            SELECT 1 FROM app_driver_allocations a WHERE a.app_driver_id = d.app_driver_id
        )
        LIMIT 10
    """)).fetchall()
    print("Sample unallocated drivers:")
    for s in sample:
        print(" ", s)
