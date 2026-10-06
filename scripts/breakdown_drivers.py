from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== BREAKDOWN OF CURRENT APP_DRIVERS ===")
    
    total = conn.execute(text("SELECT count(*) FROM app_drivers")).scalar()
    with_veh = conn.execute(text("SELECT count(*) FROM app_drivers WHERE vehicle_reg_number IS NOT NULL AND vehicle_reg_number != ''")).scalar()
    null_veh = conn.execute(text("SELECT count(*) FROM app_drivers WHERE vehicle_reg_number IS NULL OR vehicle_reg_number = ''")).scalar()
    
    print(f"Total: {total}")
    print(f"With vehicle: {with_veh}")
    print(f"Null vehicle: {null_veh}")

    # Of the null_veh drivers, how many have an allocation in app_driver_allocations?
    has_alloc = conn.execute(text("""
        SELECT count(DISTINCT d.app_driver_id)
        FROM app_drivers d
        JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
        WHERE d.vehicle_reg_number IS NULL OR d.vehicle_reg_number = ''
    """)).scalar()
    print(f"Null vehicle drivers who HAVE an allocation: {has_alloc}")

    no_alloc = conn.execute(text("""
        SELECT count(DISTINCT d.app_driver_id)
        FROM app_drivers d
        WHERE (d.vehicle_reg_number IS NULL OR d.vehicle_reg_number = '')
          AND NOT EXISTS (SELECT 1 FROM app_driver_allocations a WHERE a.app_driver_id = d.app_driver_id)
    """)).scalar()
    print(f"Null vehicle drivers who DO NOT HAVE an allocation: {no_alloc}")
