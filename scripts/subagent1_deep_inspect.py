import sys
from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

def inspect():
    with engine.connect() as conn:
        print("=== 1. APP_DRIVERS & APP_DRIVER_ALLOCATIONS SCHEMA & DATA ===")
        # columns of app_drivers
        res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'app_drivers' ORDER BY ordinal_position")).fetchall()
        print("app_drivers columns:", [(r[0], r[1]) for r in res])

        # columns of app_driver_allocations
        res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'app_driver_allocations' ORDER BY ordinal_position")).fetchall()
        print("app_driver_allocations columns:", [(r[0], r[1]) for r in res])

        # Check missing vehicle_reg_number in app_drivers
        missing_veh = conn.execute(text("""
            SELECT count(*) FROM app_drivers WHERE vehicle_reg_number IS NULL OR vehicle_reg_number = ''
        """)).scalar()
        print(f"Drivers where vehicle_reg_number IS NULL or empty: {missing_veh}")

        missing_null_only = conn.execute(text("""
            SELECT count(*) FROM app_drivers WHERE vehicle_reg_number IS NULL
        """)).scalar()
        print(f"Drivers where vehicle_reg_number IS NULL: {missing_null_only}")

        # Check how many of these have active allocations in app_driver_allocations
        alloc_counts = conn.execute(text("""
            SELECT allocation_status, count(*) 
            FROM app_driver_allocations 
            GROUP BY allocation_status
        """)).fetchall()
        print("app_driver_allocations by status:", alloc_counts)

        # Check join between app_drivers (where vehicle_reg_number IS NULL) and app_driver_allocations
        q_match = text("""
            SELECT count(DISTINCT d.app_driver_id)
            FROM app_drivers d
            JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
            WHERE d.vehicle_reg_number IS NULL
              AND a.allocation_status = 'ACTIVE';
        """)
        print("Drivers with IS NULL vehicle_reg and ACTIVE allocation:", conn.execute(q_match).scalar())

        q_match_any_status = text("""
            SELECT a.allocation_status, count(DISTINCT d.app_driver_id)
            FROM app_drivers d
            JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
            WHERE d.vehicle_reg_number IS NULL
            GROUP BY a.allocation_status;
        """)
        print("Drivers with IS NULL vehicle_reg by allocation status:", conn.execute(q_match_any_status).fetchall())

        # Check columns of app_driver_allocations vs app_drivers
        sample_alloc = conn.execute(text("""
            SELECT * FROM app_driver_allocations LIMIT 1
        """)).mappings().first()
        print("Sample app_driver_allocations row keys:", list(sample_alloc.keys()) if sample_alloc else None)
        print("Sample app_driver_allocations:", dict(sample_alloc) if sample_alloc else None)

        print("\n=== 2. MANAGERS & HUB CONTACTS ===")
        # columns of core_vehicle_allocation
        res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'core_vehicle_allocation' ORDER BY ordinal_position")).fetchall()
        print("core_vehicle_allocation columns:", [(r[0], r[1]) for r in res])

        # distinct vehicle_manager_poc in core_vehicle_allocation
        pocs = conn.execute(text("""
            SELECT vehicle_manager_poc, count(*) 
            FROM core_vehicle_allocation 
            GROUP BY vehicle_manager_poc
        """)).fetchall()
        print("core_vehicle_allocation.vehicle_manager_poc values:", pocs)

        # hubs_parking
        res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'hubs_parking' ORDER BY ordinal_position")).fetchall()
        print("hubs_parking columns:", [(r[0], r[1]) for r in res])
        hubs = conn.execute(text("SELECT * FROM hubs_parking")).mappings().fetchall()
        print("hubs_parking rows:")
        for h in hubs:
            print(" ", dict(h))

        # Check how app_driver_allocations maps to core_vehicle_allocation
        # Is there a foreign key or common id or vehicle_number + allocation_date?
        print("Sample core_vehicle_allocation row:")
        sample_core = conn.execute(text("SELECT * FROM core_vehicle_allocation LIMIT 1")).mappings().first()
        print(" ", dict(sample_core) if sample_core else None)

        # Let's see if app_driver_allocations has core_allocation_id or similar
        # Or if 7941 rows corresponds 1:1 by id or vehicle/driver
        
        print("\n=== 3. OPERATOR OP-501 ===")
        ops = conn.execute(text("""
            SELECT app_operator_id, operator_id, operator_code, company_name, phone, count_drivers
            FROM (
                SELECT o.*, 
                    (SELECT count(*) FROM app_drivers d WHERE d.operator_id = o.app_operator_id OR d.operator_id = o.operator_id) as count_drivers
                FROM app_operators o
                WHERE operator_code LIKE 'OP-501%' OR app_operator_id IN (2, 940)
            ) sub
        """)).mappings().fetchall()
        for op in ops:
            print(" ", dict(op))

        print("\n=== 4. APP_PAYMENTS ROWS 50, 51, 52, 53 ===")
        res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'app_payments' ORDER BY ordinal_position")).fetchall()
        print("app_payments columns:", [(r[0], r[1]) for r in res])

        sample_pmts = conn.execute(text("""
            SELECT * FROM app_payments 
            WHERE app_payment_id IN (50, 51, 52, 53) 
               OR payer_id = 4068
            LIMIT 10
        """)).mappings().fetchall()
        for p in sample_pmts:
            print(" ", dict(p))

        # Check operator 742 (Rishad)
        rishad = conn.execute(text("""
            SELECT * FROM app_operators WHERE app_operator_id = 742 OR operator_id = 742 OR company_name ILIKE '%rishad%'
        """)).mappings().fetchall()
        print("Rishad operator row(s):")
        for r in rishad:
            print(" ", dict(r))

        print("\n=== 5. TEST DRIVERS ===")
        test_ids = [393878, 393887, 393888, 393942, 393943, 393944, 393991, 393992, 393993]
        tdrvs = conn.execute(text(f"""
            SELECT app_driver_id, driver_id, driver_code, full_name, phone, is_active 
            FROM app_drivers 
            WHERE app_driver_id IN ({','.join(map(str, test_ids))}) OR driver_id IN ({','.join(map(str, test_ids))})
        """)).mappings().fetchall()
        for td in tdrvs:
            print(" ", dict(td))

if __name__ == '__main__':
    inspect()
