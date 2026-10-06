from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== core_vehicle_allocation.vehicle_manager_poc values ===")
    pocs = conn.execute(text("""
        SELECT vehicle_manager_poc, count(*) 
        FROM core_vehicle_allocation 
        GROUP BY vehicle_manager_poc
        ORDER BY count(*) DESC
    """)).fetchall()
    for p in pocs:
        print(" ", p)

    print("\n=== core_vehicle_allocation.hub_name values ===")
    hubs = conn.execute(text("""
        SELECT hub_name, count(*) 
        FROM core_vehicle_allocation 
        GROUP BY hub_name
        ORDER BY count(*) DESC
        LIMIT 20
    """)).fetchall()
    for h in hubs:
        print(" ", h)

    print("\n=== core_vehicle_allocation.city values ===")
    cities = conn.execute(text("""
        SELECT city, count(*) 
        FROM core_vehicle_allocation 
        GROUP BY city
        ORDER BY count(*) DESC
    """)).fetchall()
    for c in cities:
        print(" ", c)
