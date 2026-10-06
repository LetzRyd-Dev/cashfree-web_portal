import os
import sys
from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

def run_investigation():
    with engine.connect() as conn:
        print("=" * 80)
        print("SECTION 1: OPERATOR ID RESOLUTION & DRIVER FILTERING (DATA LEAKAGE RISK)")
        print("=" * 80)
        # Check operator IDs in app_operators
        ops = conn.execute(text("""
            SELECT app_operator_id, operator_id, operator_code, company_name, phone, total_drivers, total_vehicles
            FROM app_operators
            ORDER BY app_operator_id;
        """)).fetchall()
        print(f"Total operators: {len(ops)}")
        for op in ops[:10]:
            print(f"  app_op_id={op[0]}, op_id={op[1]}, code={op[2]}, name={op[3]}, phone={op[4]}, total_drvs={op[5]}")

        # Check for NULL or 0 operator_id in app_operators
        null_op_ids = conn.execute(text("""
            SELECT count(*) FROM app_operators WHERE operator_id IS NULL OR operator_id = 0;
        """)).scalar()
        print(f"\nOperators with NULL or 0 operator_id: {null_op_ids}")

        # Check where app_operator_id != operator_id in app_operators
        diff_ids = conn.execute(text("""
            SELECT app_operator_id, operator_id, company_name FROM app_operators WHERE app_operator_id != operator_id;
        """)).fetchall()
        print(f"Operators where app_operator_id != operator_id: {len(diff_ids)}")
        for d in diff_ids[:5]:
            print(f"  app_op_id={d[0]}, op_id={d[1]}, name={d[2]}")

        # Check collision: does an operator's operator_id match ANOTHER operator's app_operator_id?
        collision = conn.execute(text("""
            SELECT o1.app_operator_id as o1_app_id, o1.operator_id as o1_op_id, o1.company_name as o1_name,
                   o2.app_operator_id as o2_app_id, o2.operator_id as o2_op_id, o2.company_name as o2_name
            FROM app_operators o1
            JOIN app_operators o2 ON o1.operator_id = o2.app_operator_id AND o1.app_operator_id != o2.app_operator_id;
        """)).fetchall()
        print(f"\nCollisions (o1.operator_id == o2.app_operator_id): {len(collision)}")
        for c in collision[:5]:
            print(f"  Collision: Op {c[0]} ({c[2]}) has op_id={c[1]}, matching Op {c[3]} ({c[5]}) app_operator_id!")

        print("\n" + "=" * 80)
        print("SECTION 1B: INDEPENDENT DRIVERS (operator_id IS NULL OR operator_id = 0)")
        print("=" * 80)
        drv_op_dist = conn.execute(text("""
            SELECT 
                COUNT(*) as total_drivers,
                COUNT(CASE WHEN operator_id IS NULL THEN 1 END) as null_operator_id,
                COUNT(CASE WHEN operator_id = 0 THEN 1 END) as zero_operator_id,
                COUNT(CASE WHEN operator_id > 0 THEN 1 END) as positive_operator_id
            FROM app_drivers;
        """)).mappings().first()
        print(f"Driver operator_id distribution: {dict(drv_op_dist)}")

        # Check if an operator with operator_id = NULL would match independent drivers in SQLAlchemy:
        # In SQLAlchemy: filter((AppDrivers.operator_id == op.app_operator_id) | (AppDrivers.operator_id == op.operator_id))
        # If op.operator_id is None, does SQLAlchemy generate `operator_id IS NULL`?
        # YES! (Column == None) produces "operator_id IS NULL"!
        # Let's test which operators have operator_id IS NULL:
        ops_with_null = conn.execute(text("""
            SELECT app_operator_id, operator_code, company_name FROM app_operators WHERE operator_id IS NULL;
        """)).fetchall()
        print(f"\nOperators with operator_id IS NULL: {len(ops_with_null)}")
        for o in ops_with_null:
            print(f"  CRITICAL BUG ALERT: app_operator_id={o[0]}, code={o[1]}, name={o[2]} has operator_id=NULL!")

        print("\n" + "=" * 80)
        print("SECTION 2: VEHICLE ACCURACY & HARDCODED 'KA05AQ7692' AUDIT")
        print("=" * 80)
        # Check KA05AQ7692 in the database:
        # 1. Who actually has KA05AQ7692 in app_drivers?
        ka_drivers = conn.execute(text("""
            SELECT app_driver_id, full_name, phone, vehicle_reg_number, operator_id
            FROM app_drivers
            WHERE UPPER(REPLACE(REPLACE(vehicle_reg_number, ' ', ''), '-', '')) = 'KA05AQ7692';
        """)).fetchall()
        print(f"Drivers actually assigned KA05AQ7692 in app_drivers: {len(ka_drivers)}")
        for kd in ka_drivers:
            print(f"  app_driver_id={kd[0]}, name={kd[1]}, phone={kd[2]}, veh={kd[3]}, op_id={kd[4]}")

        # 2. Who has KA05AQ7692 in app_driver_allocations?
        ka_allocs = conn.execute(text("""
            SELECT app_allocation_id, app_driver_id, vehicle_number, app_operator_id, assigned_manager
            FROM app_driver_allocations
            WHERE UPPER(REPLACE(REPLACE(vehicle_number, ' ', ''), '-', '')) = 'KA05AQ7692';
        """)).fetchall()
        print(f"\nAllocations with KA05AQ7692: {len(ka_allocs)}")
        for ka in ka_allocs:
            print(f"  alloc_id={ka[0]}, drv_id={ka[1]}, veh={ka[2]}, op_id={ka[3]}, mgr={ka[4]}")

        # 3. How many drivers in app_drivers have NO vehicle_reg_number AND NO allocation?
        missing_veh_stats = conn.execute(text("""
            SELECT 
                COUNT(*) as total_drivers,
                COUNT(CASE WHEN d.vehicle_reg_number IS NOT NULL AND d.vehicle_reg_number != '' THEN 1 END) as has_veh_in_table,
                COUNT(CASE WHEN (d.vehicle_reg_number IS NULL OR d.vehicle_reg_number = '') AND a.vehicle_number IS NOT NULL THEN 1 END) as missing_in_table_but_has_alloc,
                COUNT(CASE WHEN (d.vehicle_reg_number IS NULL OR d.vehicle_reg_number = '') AND (a.vehicle_number IS NULL OR a.vehicle_number = '') THEN 1 END) as missing_both_receives_fallback
            FROM app_drivers d
            LEFT JOIN (
                SELECT DISTINCT ON (app_driver_id) app_driver_id, vehicle_number
                FROM app_driver_allocations
                WHERE vehicle_number IS NOT NULL AND vehicle_number != ''
                ORDER BY app_driver_id, app_allocation_id DESC
            ) a ON d.app_driver_id = a.app_driver_id;
        """)).mappings().first()
        print(f"\nVehicle assignment breakdown: {dict(missing_veh_stats)}")

        # 4. Check KA05AQ7692 in app_hisaabs
        ka_hisaabs = conn.execute(text("""
            SELECT count(*), count(distinct app_driver_id), count(distinct app_operator_id)
            FROM app_hisaabs
            WHERE hisaab_number ILIKE '%KA05AQ7692%';
        """)).fetchall()
        print(f"Hisaabs with KA05AQ7692 in hisaab_number: count={ka_hisaabs[0][0]}, distinct_drvs={ka_hisaabs[0][1]}, distinct_ops={ka_hisaabs[0][2]}")

        print("\n" + "=" * 80)
        print("SECTION 3: HISAABS & FINANCIAL DISCREPANCIES AUDIT")
        print("=" * 80)
        # Check corrupted / impossible numbers in app_hisaabs
        corrupt_hisaabs = conn.execute(text("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN completed_trips < 0 THEN 1 END) as negative_trips,
                COUNT(CASE WHEN total_gross_earnings < 0 THEN 1 END) as negative_earnings,
                COUNT(CASE WHEN total_km < 0 THEN 1 END) as negative_km,
                COUNT(CASE WHEN total_deductions < 0 THEN 1 END) as negative_deductions,
                COUNT(CASE WHEN vehicle_rent < 0 THEN 1 END) as negative_rent,
                COUNT(CASE WHEN to_pay > 0 AND to_collect > 0 THEN 1 END) as both_pay_and_collect,
                COUNT(CASE WHEN completed_trips > 500 THEN 1 END) as absurdly_high_trips,
                COUNT(CASE WHEN total_gross_earnings > 500000 THEN 1 END) as absurdly_high_earnings
            FROM app_hisaabs;
        """)).mappings().first()
        print(f"app_hisaabs corruption checks: {dict(corrupt_hisaabs)}")

        # Check driver vs fleet financial aggregation match
        # Compare sum of drivers under operator vs app_operators stored values
        op_sum_comparison = conn.execute(text("""
            SELECT 
                o.app_operator_id,
                o.operator_code,
                o.company_name,
                o.cw_to_pay as op_cw_to_pay,
                o.cw_to_collect as op_cw_to_collect,
                o.cw_fleet_gross_earnings as op_cw_gross,
                o.cw_fleet_trips as op_cw_trips,
                COALESCE(SUM(d.cw_to_pay), 0) as calc_drv_cw_to_pay,
                COALESCE(SUM(d.cw_to_collect), 0) as calc_drv_cw_to_collect,
                COALESCE(SUM(d.cw_gross_earnings), 0) as calc_drv_cw_gross,
                COALESCE(SUM(d.cw_trips), 0) as calc_drv_cw_trips,
                COUNT(d.app_driver_id) as driver_count
            FROM app_operators o
            LEFT JOIN app_drivers d ON (d.operator_id = o.app_operator_id OR d.operator_id = o.operator_id)
            GROUP BY o.app_operator_id, o.operator_code, o.company_name, o.cw_to_pay, o.cw_to_collect, o.cw_fleet_gross_earnings, o.cw_fleet_trips
            ORDER BY driver_count DESC
            LIMIT 15;
        """)).mappings().fetchall()
        print("\nOperator Stored vs Drivers Sum Comparison (Top 15 operators by driver count):")
        for row in op_sum_comparison:
            diff_pay = abs(float(row['op_cw_to_pay'] or 0) - float(row['calc_drv_cw_to_pay']))
            diff_col = abs(float(row['op_cw_to_collect'] or 0) - float(row['calc_drv_cw_to_collect']))
            diff_gross = abs(float(row['op_cw_gross'] or 0) - float(row['calc_drv_cw_gross']))
            print(f"Op {row['app_operator_id']} ({row['company_name']}) [Drvs: {row['driver_count']}]:")
            print(f"  Stored: to_pay={row['op_cw_to_pay']}, to_collect={row['op_cw_to_collect']}, gross={row['op_cw_gross']}, trips={row['op_cw_trips']}")
            print(f"  SumDrv: to_pay={row['calc_drv_cw_to_pay']}, to_collect={row['calc_drv_cw_to_collect']}, gross={row['calc_drv_cw_gross']}, trips={row['calc_drv_cw_trips']}")
            if diff_pay > 1 or diff_col > 1 or diff_gross > 1:
                print(f"  -> DISCREPANCY DETECTED! diff_pay={diff_pay:.2f}, diff_col={diff_col:.2f}, diff_gross={diff_gross:.2f}")

        # Check hisaab-level vs driver-level cw_os / cw_to_pay / cw_to_collect
        active_hisaabs = conn.execute(text("""
            SELECT 
                h.app_driver_id,
                h.week_number,
                h.current_period_os,
                h.to_pay,
                h.to_collect,
                d.cw_os,
                d.cw_to_pay,
                d.cw_to_collect
            FROM app_hisaabs h
            JOIN app_drivers d ON h.app_driver_id = d.app_driver_id
            WHERE h.week_number = 30 AND h.is_locked = FALSE
            LIMIT 15;
        """)).mappings().fetchall()
        print(f"\nSample Week 30 hisaab vs driver cw figures (15 rows):")
        for ah in active_hisaabs:
            print(f"  Drv {ah['app_driver_id']}: hisaab(os={ah['current_period_os']}, to_pay={ah['to_pay']}, to_collect={ah['to_collect']}) vs drv(os={ah['cw_os']}, to_pay={ah['cw_to_pay']}, to_collect={ah['cw_to_collect']})")

if __name__ == '__main__':
    run_investigation()
