from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== Sample allocations for null vehicle drivers ===")
    sample = conn.execute(text("""
        SELECT a.app_allocation_id, a.app_driver_id, a.vehicle_number, a.allocation_date, a.dropoff_date, a.allocation_status, a.daily_rental_rate
        FROM app_driver_allocations a
        JOIN app_drivers d ON d.app_driver_id = a.app_driver_id
        WHERE d.vehicle_reg_number IS NULL
        ORDER BY a.app_driver_id, a.allocation_date DESC
        LIMIT 10
    """)).fetchall()
    for s in sample:
        print(" ", s)
