import os
from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

def run_audit():
    print("="*60)
    print("1. SEARCHING FOR MANAGER / SUPERVISOR COLUMNS IN DB")
    print("="*60)
    with engine.connect() as conn:
        q = text("""
            SELECT table_name, column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
              AND (column_name ILIKE '%manager%' OR column_name ILIKE '%supervisor%')
            ORDER BY table_name, column_name;
        """)
        rows = conn.execute(q).fetchall()
        for r in rows:
            print(f"  {r[0]}.{r[1]}")

        print("\n" + "="*60)
        print("2. CHECKING DRIVER MANAGER DATA IN APP TABLES")
        print("="*60)
        q_drv_mgr = text("""
            SELECT 
                COUNT(*) as total_drivers,
                COUNT(assigned_manager_name) as with_mgr_name,
                COUNT(assigned_manager_phone) as with_mgr_phone,
                COUNT(DISTINCT assigned_manager_name) as distinct_mgr_names
            FROM app_drivers;
        """)
        d_mgr = conn.execute(q_drv_mgr).mappings().first()
        print(f"app_drivers manager stats: {dict(d_mgr)}")

        # Sample manager names from app_drivers
        sample_mgr = conn.execute(text("""
            SELECT assigned_manager_name, assigned_manager_phone, count(*) 
            FROM app_drivers 
            GROUP BY assigned_manager_name, assigned_manager_phone
            ORDER BY count(*) DESC
            LIMIT 10;
        """)).fetchall()
        print("Top managers in app_drivers:")
        for sm in sample_mgr:
            print(f"  Name: {sm[0]}, Phone: {sm[1]}, Count: {sm[2]}")

        print("\n" + "="*60)
        print("3. CHECKING OPERATOR MANAGER DATA IN APP TABLES")
        print("="*60)
        q_op_mgr = text("""
            SELECT 
                COUNT(*) as total_operators,
                COUNT(assigned_manager_name) as with_mgr_name,
                COUNT(assigned_manager_phone) as with_mgr_phone,
                COUNT(DISTINCT assigned_manager_name) as distinct_mgr_names
            FROM app_operators;
        """)
        op_mgr = conn.execute(q_op_mgr).mappings().first()
        print(f"app_operators manager stats: {dict(op_mgr)}")

        sample_op_mgr = conn.execute(text("""
            SELECT assigned_manager_name, assigned_manager_phone, count(*) 
            FROM app_operators 
            GROUP BY assigned_manager_name, assigned_manager_phone
            ORDER BY count(*) DESC
            LIMIT 10;
        """)).fetchall()
        print("Top managers in app_operators:")
        for som in sample_op_mgr:
            print(f"  Name: {som[0]}, Phone: {som[1]}, Count: {som[2]}")

        print("\n" + "="*60)
        print("4. CHECKING IDs INTEGRITY: DRIVERS")
        print("="*60)
        drv_ids = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(app_driver_id) as count_app_driver_id,
                COUNT(DISTINCT app_driver_id) as uniq_app_driver_id,
                COUNT(driver_id) as count_driver_id,
                COUNT(driver_code) as count_driver_code,
                COUNT(DISTINCT driver_code) as uniq_driver_code,
                COUNT(CASE WHEN driver_code IS NULL OR driver_code = '' THEN 1 END) as empty_driver_code,
                COUNT(phone) as count_phone,
                COUNT(DISTINCT phone) as uniq_phone,
                COUNT(CASE WHEN phone IS NULL OR phone = '' THEN 1 END) as empty_phone
            FROM app_drivers;
        """)).mappings().first()
        print(f"app_drivers ID integrity: {dict(drv_ids)}")

        # Driver code patterns
        drv_code_samples = conn.execute(text("""
            SELECT SUBSTRING(driver_code FROM 1 FOR 7) as prefix, count(*) 
            FROM app_drivers 
            GROUP BY prefix 
            ORDER BY count(*) DESC 
            LIMIT 10;
        """)).fetchall()
        print("Driver code prefixes:")
        for dcs in drv_code_samples:
            print(f"  Prefix: {dcs[0]}, Count: {dcs[1]}")

        print("\n" + "="*60)
        print("5. CHECKING IDs INTEGRITY: OPERATORS")
        print("="*60)
        op_ids = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(app_operator_id) as count_app_operator_id,
                COUNT(DISTINCT app_operator_id) as uniq_app_operator_id,
                COUNT(operator_id) as count_operator_id,
                COUNT(operator_code) as count_operator_code,
                COUNT(DISTINCT operator_code) as uniq_operator_code,
                COUNT(CASE WHEN operator_code IS NULL OR operator_code = '' THEN 1 END) as empty_operator_code,
                COUNT(phone) as count_phone,
                COUNT(DISTINCT phone) as uniq_phone,
                COUNT(CASE WHEN phone IS NULL OR phone = '' THEN 1 END) as empty_phone
            FROM app_operators;
        """)).mappings().first()
        print(f"app_operators ID integrity: {dict(op_ids)}")

        op_code_samples = conn.execute(text("""
            SELECT SUBSTRING(operator_code FROM 1 FOR 7) as prefix, count(*) 
            FROM app_operators 
            GROUP BY prefix 
            ORDER BY count(*) DESC 
            LIMIT 10;
        """)).fetchall()
        print("Operator code prefixes:")
        for ocs in op_code_samples:
            print(f"  Prefix: {ocs[0]}, Count: {ocs[1]}")

        print("\n" + "="*60)
        print("6. CHECKING VEHICLES & ALLOCATIONS INTEGRITY")
        print("="*60)
        alloc_stats = conn.execute(text("""
            SELECT 
                COUNT(*) as total_allocations,
                COUNT(DISTINCT app_driver_id) as drivers_with_alloc,
                COUNT(DISTINCT vehicle_number) as distinct_vehicles,
                COUNT(CASE WHEN vehicle_number IS NULL OR vehicle_number = '' THEN 1 END) as empty_veh,
                COUNT(assigned_manager) as with_assigned_manager
            FROM app_driver_allocations;
        """)).mappings().first()
        print(f"app_driver_allocations stats: {dict(alloc_stats)}")

        drv_veh_stats = conn.execute(text("""
            SELECT 
                COUNT(*) as total_drivers,
                COUNT(vehicle_reg_number) as with_vehicle_reg,
                COUNT(CASE WHEN vehicle_reg_number IS NULL OR vehicle_reg_number = '' THEN 1 END) as without_vehicle_reg
            FROM app_drivers;
        """)).mappings().first()
        print(f"app_drivers vehicle stats: {dict(drv_veh_stats)}")

        print("\n" + "="*60)
        print("7. CHECKING CORE TABLES FOR MANAGER & ALLOCATIONS DATA")
        print("="*60)
        core_tables = ['core_vehicle_allocation', 'july_allocation_form', 'driver_onboarding', 'july_driver_onboarding', 'july_employees']
        for ct in core_tables:
            try:
                cnt = conn.execute(text(f"SELECT COUNT(*) FROM {ct}")).scalar()
                cols = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{ct}'")).fetchall()
                col_names = [c[0] for c in cols]
                print(f"Table {ct}: {cnt} rows, cols: {col_names[:8]}...")
            except Exception as e:
                print(f"Table {ct} error: {e}")

if __name__ == '__main__':
    run_audit()
