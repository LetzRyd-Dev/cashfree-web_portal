"""
platform_aggregator.py — Raw Data Aggregation Pipeline for LetzRyd Backend
===========================================================================
Aggregates raw tables (raw_uber_data, raw_ola_data, raw_rapido_data, raw_traffic_challans,
raw_accidents_registry, raw_partner_adjustments, raw_gps_logs) grouped by vehicle_number
and week_number, then runs hisaab_calculator and updates app_hisaabs, app_drivers, app_operators.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from typing import Optional

from app.models.app_models import AppDrivers, AppOperators, AppHisaabs
from app.services.hisaab_calculator import calculate_hisaab_breakdown

def aggregate_raw_platform_data(db: Session, week_number: Optional[int] = None):
    """
    Reads raw platform data tables directly and aggregates into app_hisaabs.
    If week_number is None, automatically detects all week numbers present in raw tables
    or defaults to current ISO calendar week.
    """
    # 1. Determine week numbers to process
    if week_number is None:
        weeks_query = text("""
            SELECT DISTINCT week_num FROM (
                SELECT EXTRACT(WEEK FROM week_start)::INTEGER AS week_num FROM raw_uber_data WHERE week_start IS NOT NULL
                UNION
                SELECT EXTRACT(WEEK FROM week_start)::INTEGER AS week_num FROM raw_ola_data WHERE week_start IS NOT NULL
                UNION
                SELECT EXTRACT(WEEK FROM week_start)::INTEGER AS week_num FROM raw_rapido_data WHERE week_start IS NOT NULL
            ) w_all;
        """)
        weeks = [r[0] for r in db.execute(weeks_query).fetchall() if r[0] is not None]
        if not weeks:
            weeks = [datetime.now().isocalendar().week]
    else:
        weeks = [week_number]

    total_processed = 0

    for current_week in weeks:
        # Fetch distinct vehicles in raw platform data for the specified week
        vehicles_query = text("""
            SELECT DISTINCT vehicle_number FROM (
                SELECT vehicle_number FROM raw_uber_data
                UNION
                SELECT vehicle_number FROM raw_ola_data
                UNION
                SELECT vehicle_number FROM raw_rapido_data
            ) v_all;
        """)
        vehicles = db.execute(vehicles_query).fetchall()
        
        for v_row in vehicles:
            v_num = v_row[0]
            if not v_num:
                continue
                
            # Aggregate raw Uber data
            u_stmt = text("""
                SELECT 
                    COUNT(*) AS trips,
                    COALESCE(SUM(net_revenue), 0) AS rev,
                    COALESCE(SUM(cash_collected), 0) AS cash,
                    COALESCE(SUM(tolls), 0) AS toll,
                    COALESCE(SUM(incentives), 0) AS inc,
                    COALESCE(SUM(subscription_fee), 0) AS sub,
                    COALESCE(SUM(distance_km), 0) AS km
                FROM raw_uber_data WHERE vehicle_number = :v;
            """)
            u_data = db.execute(u_stmt, {"v": v_num}).fetchone()
            
            # Aggregate raw Ola data
            o_stmt = text("""
                SELECT 
                    COUNT(*) AS trips,
                    COALESCE(SUM(net_revenue), 0) AS rev,
                    COALESCE(SUM(cash_collected), 0) AS cash,
                    COALESCE(SUM(tolls), 0) AS toll,
                    COALESCE(SUM(incentives), 0) AS inc,
                    COALESCE(SUM(subscription_fee), 0) AS sub,
                    COALESCE(SUM(actual_kms), 0) AS km
                FROM raw_ola_data WHERE vehicle_number = :v;
            """)
            o_data = db.execute(o_stmt, {"v": v_num}).fetchone()
            
            # Aggregate raw Rapido data
            r_stmt = text("""
                SELECT 
                    COUNT(*) AS trips,
                    COALESCE(SUM(net_revenue), 0) AS rev,
                    COALESCE(SUM(cash_collected), 0) AS cash,
                    COALESCE(SUM(tolls), 0) AS toll,
                    COALESCE(SUM(incentives), 0) AS inc,
                    0 AS sub,
                    COALESCE(SUM(distance_kms), 0) AS km
                FROM raw_rapido_data WHERE vehicle_number = :v;
            """)
            r_data = db.execute(r_stmt, {"v": v_num}).fetchone()
            
            # Aggregate Challans, Accidents, Adjustments, GPS
            challan_stmt = text("SELECT COALESCE(SUM(challan_amount), 0) FROM raw_traffic_challans WHERE vehicle_number = :v;")
            challan_amt = float(db.execute(challan_stmt, {"v": v_num}).scalar() or 0.0)
            
            accident_stmt = text("SELECT COALESCE(SUM(repair_cost + fine_amount), 0) FROM raw_accidents_registry WHERE vehicle_number = :v;")
            accident_amt = float(db.execute(accident_stmt, {"v": v_num}).scalar() or 0.0)

            adj_stmt = text("SELECT COALESCE(SUM(amount), 0) FROM raw_partner_adjustments WHERE vehicle_number = :v;")
            adj_amt = float(db.execute(adj_stmt, {"v": v_num}).scalar() or 0.0)

            gps_stmt = text("SELECT COALESCE(SUM(km_driven), 0) FROM raw_gps_logs WHERE vehicle_number = :v;")
            gps_km = float(db.execute(gps_stmt, {"v": v_num}).scalar() or 0.0)

            # Run Calculation Engine
            raw_inputs = {
                "uber_revenue": float(u_data.rev),
                "uber_cash": float(u_data.cash),
                "uber_incentive": float(u_data.inc),
                "uber_km": float(u_data.km),
                
                "ola_revenue": float(o_data.rev),
                "ola_cash": float(o_data.cash),
                "ola_incentive": float(o_data.inc),
                "ola_km": float(o_data.km),
                
                "rapido_revenue": float(r_data.rev),
                "rapido_cash": float(r_data.cash),
                "rapido_incentive": float(r_data.inc),
                "rapido_km": float(r_data.km),
                
                "days_count": 7,
                "vehicle_daily_rate": 1100.0,
                "maintenance_daily_rate": 30.0,
                "challan_amount": challan_amt,
                "accident_charge": accident_amt,
                "other_adjustment": adj_amt,
                "gps_total_km": gps_km,
                "previous_outstanding": 0.0
            }

            calc_result = calculate_hisaab_breakdown(raw_inputs)
            
            # Find or create Driver & Operator
            driver = db.query(AppDrivers).filter(AppDrivers.vehicle_reg_number == v_num).first()
            if not driver:
                driver = db.query(AppDrivers).first()
                
            operator = db.query(AppOperators).first()
            
            if driver and operator:
                hisaab = db.query(AppHisaabs).filter(
                    AppHisaabs.app_driver_id == driver.app_driver_id,
                    AppHisaabs.week_number == current_week
                ).first()
                
                if not hisaab:
                    hisaab = AppHisaabs(
                        allocation_id=1,
                        hisaab_id=1,
                        app_driver_id=driver.app_driver_id,
                        app_operator_id=operator.app_operator_id,
                        vehicle_id=1,
                        hisaab_number=f"HIS-2026-0{current_week}-{v_num}",
                        week_number=current_week,
                        period_start="2026-07-06",
                        period_end="2026-07-12",
                        days_count=7
                    )
                    db.add(hisaab)

                # Update Hisaab fields
                hisaab.uber_trips = int(u_data.trips)
                hisaab.uber_revenue = float(u_data.rev)
                hisaab.uber_cash = float(u_data.cash)
                hisaab.uber_toll = float(u_data.toll)
                hisaab.uber_incentive = float(u_data.inc)
                hisaab.uber_km = float(u_data.km)
                
                hisaab.ola_trips = int(o_data.trips)
                hisaab.ola_revenue = float(o_data.rev)
                hisaab.ola_cash = float(o_data.cash)
                hisaab.ola_toll = float(o_data.toll)
                hisaab.ola_incentive = float(o_data.inc)
                hisaab.ola_km = float(o_data.km)

                hisaab.rapido_trips = int(r_data.trips)
                hisaab.rapido_revenue = float(r_data.rev)
                hisaab.rapido_cash = float(r_data.cash)
                hisaab.rapido_toll = float(r_data.toll)
                hisaab.rapido_incentive = float(r_data.inc)
                hisaab.rapido_km = float(r_data.km)

                hisaab.vehicle_rent = calc_result["vehicle_rent"]
                hisaab.maintenance_charge = calc_result["maintenance_charge"]
                hisaab.tds_amount = calc_result["tds_amount"]
                hisaab.challan_amount = calc_result["challan_amount"]
                hisaab.accident_charge = calc_result["accident_charge"]
                hisaab.other_adjustment = calc_result["other_adjustment"]
                hisaab.gps_total_km = calc_result["gps_total_km"]
                hisaab.gps_dead_km = calc_result["gps_dead_km"]
                hisaab.gps_dead_penalty = calc_result["gps_dead_penalty"]
                hisaab.total_gross_earnings = calc_result["total_gross_earnings"]
                hisaab.total_deductions = calc_result["total_deductions"]
                hisaab.current_period_os = calc_result["current_period_os"]
                hisaab.to_collect = calc_result["to_collect"]
                hisaab.to_pay = calc_result["to_pay"]
                
                # Update driver cw_* fields cleanly
                driver.cw_uber_trips = hisaab.uber_trips or 0
                driver.cw_uber_revenue = hisaab.uber_revenue or 0.0
                driver.cw_ola_trips = hisaab.ola_trips or 0
                driver.cw_ola_revenue = hisaab.ola_revenue or 0.0
                driver.cw_rapido_trips = hisaab.rapido_trips or 0
                driver.cw_rapido_revenue = hisaab.rapido_revenue or 0.0
                driver.cw_gross_earnings = hisaab.total_gross_earnings or 0.0
                driver.cw_vehicle_rent = hisaab.vehicle_rent or 0.0
                driver.cw_os = hisaab.current_period_os or 0.0
                driver.cw_to_collect = hisaab.to_collect or 0.0
                driver.cw_to_pay = hisaab.to_pay or 0.0

                # Set default 0 for lw_* fields if first week
                if driver.lw_gross_earnings is None:
                    driver.lw_trips = 0
                    driver.lw_gross_earnings = 0.0
                    driver.lw_os = 0.0
                    driver.lw_to_collect = 0.0
                    driver.lw_to_pay = 0.0
                    driver.lw_status = "unpaid"

                # Update operator cw_fleet_* fields
                if operator:
                    fleet_stats = db.execute(
                        text("""
                            SELECT 
                                COALESCE(SUM(total_gross_earnings), 0.0) AS gross,
                                COALESCE(SUM(current_period_os), 0.0) AS net_os,
                                COALESCE(SUM(to_collect), 0.0) AS collect,
                                COALESCE(SUM(to_pay), 0.0) AS pay
                            FROM app_hisaabs 
                            WHERE app_operator_id = :op_id AND week_number = :wk;
                        """),
                        {"op_id": operator.app_operator_id, "wk": current_week}
                    ).fetchone()

                    operator.cw_fleet_gross_earnings = float(fleet_stats.gross)
                    operator.cw_fleet_net_os = float(fleet_stats.net_os)
                    operator.cw_to_collect = float(fleet_stats.collect)

                    if operator.lw_fleet_gross_earnings is None:
                        operator.lw_fleet_gross_earnings = 0.0
                        operator.lw_fleet_net_os = 0.0
                        operator.lw_to_collect = 0.0

                total_processed += 1

    db.commit()
    return total_processed
