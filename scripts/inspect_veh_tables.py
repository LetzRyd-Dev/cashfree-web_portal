from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== TABLES WITH 'veh' IN NAME ===")
    res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name ILIKE '%veh%'")).fetchall()
    for r in res:
        print(" ", r[0])

    print("\n=== SAMPLE DATA FROM core_vehicle_allocation ===")
    sample = conn.execute(text("SELECT id, vehicle_number, car_model, hub_name, vehicle_manager_poc, city FROM core_vehicle_allocation LIMIT 5")).fetchall()
    for s in sample:
        print(" ", s)

    print("\n=== CHECK core_allocation_id LINK IN app_driver_allocations ===")
    link_count = conn.execute(text("SELECT count(*) FROM app_driver_allocations WHERE core_allocation_id IS NOT NULL")).scalar()
    print("Allocations with core_allocation_id:", link_count)
    
    sample_alloc = conn.execute(text("""
        SELECT a.app_allocation_id, a.core_allocation_id, a.app_driver_id, a.vehicle_number, a.daily_rental_rate, a.allocation_status,
               c.car_model, c.hub_name, c.vehicle_manager_poc, c.city
        FROM app_driver_allocations a
        LEFT JOIN core_vehicle_allocation c ON a.core_allocation_id = c.id
        LIMIT 5
    """)).fetchall()
    for sa in sample_alloc:
        print(" ", sa)
