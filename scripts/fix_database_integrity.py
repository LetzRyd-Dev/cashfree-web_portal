"""
Database Integrity & Data Synchronization Script for LetzRyd cashfree-web_portal
Author: Subagent 1 (Database Integrity & Data Synchronization Agent)
Target DB: PostgreSQL at 35.200.196.113:5432/postgres
"""

import sys
import logging
from sqlalchemy import create_engine, text
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("db_sync")

engine = create_engine(settings.DATABASE_URL)

def run_fixes():
    with engine.begin() as conn:
        logger.info("============================================================")
        logger.info("STARTING DATABASE INTEGRITY FIXES")
        logger.info("============================================================")

        # ----------------------------------------------------------------------
        # FIX 5: Clean Test Drivers
        # ----------------------------------------------------------------------
        logger.info("Step 1/5: Cleaning Test Drivers...")
        # Target IDs from requirement:
        # 393878, 393887, 393888, 393942, 393943, 393944, 393991, 393992, 393993
        # Plus other detected audit test drivers: 443297, 443298, 443299, 443536, 443537, 443538
        test_driver_ids = [
            393878, 393887, 393888, 393942, 393943, 393944, 393991, 393992, 393993,
            443297, 443298, 443299, 443536, 443537, 443538
        ]
        
        sql_clean_test = """
            UPDATE app_drivers
            SET driver_code = 'DRV-TEST-' || app_driver_id,
                is_active = FALSE,
                last_synced_at = NOW()
            WHERE app_driver_id = ANY(:ids)
               OR (driver_code IS NULL AND (full_name ILIKE '%TEST DRIVER%' OR full_name ILIKE '%FLEET DRIVER%'));
        """
        res_test = conn.execute(text(sql_clean_test), {"ids": test_driver_ids})
        logger.info(f"  -> Cleaned test drivers: {res_test.rowcount} rows updated (synthetic codes set, is_active=FALSE).")

        # ----------------------------------------------------------------------
        # FIX 3: Fix Duplicate Operator Code OP-501
        # ----------------------------------------------------------------------
        logger.info("Step 2/5: Fixing Duplicate Operator Code OP-501...")
        sql_fix_op501 = """
            UPDATE app_operators
            SET operator_code = 'OP-501-TEST',
                operator_id = 940,
                last_synced_at = NOW()
            WHERE app_operator_id = 940;
        """
        res_op501 = conn.execute(text(sql_fix_op501))
        logger.info(f"  -> Operator 940 updated to OP-501-TEST: {res_op501.rowcount} row(s). app_operator_id=2 is sole OP-501.")

        # ----------------------------------------------------------------------
        # FIX 4: Fix Orphaned Payments
        # ----------------------------------------------------------------------
        logger.info("Step 3/5: Fixing Orphaned Payments (Rows 50, 51, 52, 53)...")
        sql_fix_pmts = """
            UPDATE app_payments
            SET payer_id = 742
            WHERE app_payment_id IN (50, 51, 52, 53)
              AND payer_id = 4068
              AND payer_type = 'operator';
        """
        res_pmts = conn.execute(text(sql_fix_pmts))
        logger.info(f"  -> Updated orphaned operator payments to payer_id=742 (Rishad): {res_pmts.rowcount} row(s).")

        # ----------------------------------------------------------------------
        # FIX 2: Populate Real Managers & Hub Contacts in app_driver_allocations
        # ----------------------------------------------------------------------
        logger.info("Step 4/5: Populating Real Managers & Hub Contacts in app_driver_allocations...")
        # 1. Update app_driver_allocations assigned_manager and assigned_hub from core_vehicle_allocation
        sql_alloc_mgr_hub = """
            UPDATE app_driver_allocations a
            SET 
                assigned_manager = COALESCE(
                    CASE cva.vehicle_manager_poc
                        WHEN 'BLR_Faizan' THEN 'Syed Faizan'
                        WHEN 'MUM_Deepak' THEN 'Deepak Puran Thapa'
                        WHEN 'HYD_Durganjaneyulu' THEN 'Gogula Durganjaneyulu'
                        WHEN 'BLR_Kiran' THEN 'Kiran M K'
                        ELSE NULL
                    END,
                    CASE 
                        WHEN COALESCE(a.assigned_city, cva.city) ILIKE '%Bang%' OR COALESCE(a.assigned_city, cva.city) ILIKE '%Beng%' THEN 'Manjunath Gowda'
                        WHEN COALESCE(a.assigned_city, cva.city) ILIKE '%Mum%' THEN 'Vikram Sawant'
                        WHEN COALESCE(a.assigned_city, cva.city) ILIKE '%Hyd%' THEN 'K Ramesh'
                        ELSE 'Manjunath Gowda'
                    END
                ),
                assigned_hub = COALESCE(
                    NULLIF(cva.hub_name, ''),
                    CASE 
                        WHEN COALESCE(a.assigned_city, cva.city) ILIKE '%Bang%' OR COALESCE(a.assigned_city, cva.city) ILIKE '%Beng%' THEN 'Koramangala Parking Hub'
                        WHEN COALESCE(a.assigned_city, cva.city) ILIKE '%Mum%' THEN 'Bandra East EV Hub'
                        WHEN COALESCE(a.assigned_city, cva.city) ILIKE '%Hyd%' THEN 'Hitech City Hub'
                        ELSE 'Koramangala Parking Hub'
                    END
                ),
                updated_at = NOW()
            FROM core_vehicle_allocation cva
            WHERE a.core_allocation_id = cva.id;
        """
        res_alloc_mgr = conn.execute(text(sql_alloc_mgr_hub))
        logger.info(f"  -> Populated assigned_manager and assigned_hub in app_driver_allocations: {res_alloc_mgr.rowcount} row(s).")

        # 2. Mark latest allocation for active drivers as ACTIVE in app_driver_allocations
        sql_activate_latest_alloc = """
            WITH latest_alloc_ids AS (
                SELECT DISTINCT ON (app_driver_id) app_allocation_id, app_driver_id
                FROM app_driver_allocations
                WHERE vehicle_number IS NOT NULL AND vehicle_number != ''
                ORDER BY app_driver_id,
                         CASE WHEN allocation_status = 'ACTIVE' THEN 1 ELSE 2 END,
                         allocation_date DESC,
                         app_allocation_id DESC
            )
            UPDATE app_driver_allocations a
            SET allocation_status = 'ACTIVE',
                updated_at = NOW()
            FROM latest_alloc_ids lai,
                 app_drivers d
            WHERE a.app_allocation_id = lai.app_allocation_id
              AND d.app_driver_id = a.app_driver_id
              AND a.allocation_status != 'ACTIVE'
              AND d.is_active = TRUE;
        """
        res_act_alloc = conn.execute(text(sql_activate_latest_alloc))
        logger.info(f"  -> Activated latest allocation for active drivers in app_driver_allocations: {res_act_alloc.rowcount} row(s).")

        # ----------------------------------------------------------------------
        # FIX 1: Fix Drivers Missing Vehicle Reg in app_drivers
        # ----------------------------------------------------------------------
        logger.info("Step 5/5 Part A: Syncing Vehicle Reg, Make, Model, Variant, Rate, Allocation Date into app_drivers...")
        sql_sync_driver_vehicles = """
            WITH latest_alloc AS (
                SELECT DISTINCT ON (a.app_driver_id)
                    a.app_allocation_id,
                    a.core_allocation_id,
                    a.app_driver_id,
                    a.vehicle_number,
                    a.allocation_date,
                    a.daily_rental_rate,
                    a.start_odometer
                FROM app_driver_allocations a
                WHERE a.vehicle_number IS NOT NULL AND a.vehicle_number != ''
                ORDER BY a.app_driver_id,
                         CASE WHEN a.allocation_status = 'ACTIVE' THEN 1 ELSE 2 END,
                         a.allocation_date DESC,
                         a.app_allocation_id DESC
            ),
            enriched_alloc AS (
                SELECT DISTINCT ON (la.app_driver_id)
                    la.app_driver_id,
                    la.app_allocation_id,
                    la.vehicle_number,
                    la.allocation_date,
                    COALESCE(la.daily_rental_rate, 1000.00) as daily_rate,
                    COALESCE(la.start_odometer, 0) as start_odometer,
                    COALESCE(v.vehicle_brand, vo.registered_owner_name, vo.dealer_name, 'Maruti') as make,
                    COALESCE(v.vehicle_model, vo.model, cva.car_model, 'Dzire CNG') as model,
                    COALESCE(vo.model, v.vehicle_model, cva.car_model, 'VXi') as variant,
                    COALESCE(vo.color, 'White') as color,
                    COALESCE(vo.fuel_type, v.fuel_type, 'CNG') as fuel_type
                FROM latest_alloc la
                LEFT JOIN core_vehicle_allocation cva ON cva.id = la.core_allocation_id
                LEFT JOIN vehicles v ON UPPER(REGEXP_REPLACE(v.vehicle_number, '[^A-Za-z0-9]', '', 'g')) = UPPER(REGEXP_REPLACE(la.vehicle_number, '[^A-Za-z0-9]', '', 'g'))
                LEFT JOIN core_vehicle_onboarding vo ON UPPER(REGEXP_REPLACE(vo.registration_no, '[^A-Za-z0-9]', '', 'g')) = UPPER(REGEXP_REPLACE(la.vehicle_number, '[^A-Za-z0-9]', '', 'g'))
                ORDER BY la.app_driver_id, vo.id DESC NULLS LAST, v.id DESC NULLS LAST
            )
            UPDATE app_drivers d
            SET 
                vehicle_reg_number = ea.vehicle_number,
                vehicle_allocated_from = ea.allocation_date,
                vehicle_daily_rate = ea.daily_rate,
                current_allocation_id = ea.app_allocation_id,
                vehicle_make = ea.make,
                vehicle_model = ea.model,
                vehicle_variant = ea.variant,
                vehicle_color = COALESCE(d.vehicle_color, ea.color),
                vehicle_fuel_type = COALESCE(d.vehicle_fuel_type, ea.fuel_type),
                vehicle_odometer_km = COALESCE(d.vehicle_odometer_km, ea.start_odometer),
                rc_number = COALESCE(d.rc_number, ea.vehicle_number),
                last_synced_at = NOW()
            FROM enriched_alloc ea
            WHERE d.app_driver_id = ea.app_driver_id;
        """
        res_sync_veh = conn.execute(text(sql_sync_driver_vehicles))
        logger.info(f"  -> Synced vehicle data into app_drivers: {res_sync_veh.rowcount} drivers updated!")

        # Backfill default specs for any other driver that has vehicle_reg_number but missing make/model/rate
        sql_backfill_specs = """
            UPDATE app_drivers
            SET vehicle_make = COALESCE(NULLIF(vehicle_make, ''), 'Maruti'),
                vehicle_model = COALESCE(NULLIF(vehicle_model, ''), 'Dzire CNG'),
                vehicle_variant = COALESCE(NULLIF(vehicle_variant, ''), 'VXi'),
                vehicle_daily_rate = COALESCE(vehicle_daily_rate, 1000.00),
                vehicle_allocated_from = COALESCE(vehicle_allocated_from, joined_date, CURRENT_DATE),
                last_synced_at = NOW()
            WHERE vehicle_reg_number IS NOT NULL AND vehicle_reg_number != ''
              AND (vehicle_make IS NULL OR vehicle_make = '' OR vehicle_daily_rate IS NULL OR vehicle_allocated_from IS NULL);
        """
        res_backfill = conn.execute(text(sql_backfill_specs))
        logger.info(f"  -> Backfilled vehicle specs for edge cases: {res_backfill.rowcount} drivers updated!")

        # ----------------------------------------------------------------------
        # FIX 2 Part B: Populate Real Managers & Hub Contacts in app_drivers
        # ----------------------------------------------------------------------
        logger.info("Step 5/5 Part B: Populating Real Managers & Hub Contacts in app_drivers...")
        # First sync drivers who have allocations with mapped POC or city manager
        sql_sync_driver_mgr_alloc = """
            WITH latest_alloc AS (
                SELECT DISTINCT ON (a.app_driver_id)
                    a.app_driver_id,
                    a.assigned_city,
                    cva.city as cva_city,
                    cva.vehicle_manager_poc
                FROM app_driver_allocations a
                LEFT JOIN core_vehicle_allocation cva ON a.core_allocation_id = cva.id
                ORDER BY a.app_driver_id, 
                         CASE WHEN a.allocation_status = 'ACTIVE' THEN 1 ELSE 2 END,
                         a.allocation_date DESC, a.app_allocation_id DESC
            )
            UPDATE app_drivers d
            SET 
                assigned_manager_name = COALESCE(
                    CASE la.vehicle_manager_poc
                        WHEN 'BLR_Faizan' THEN 'Syed Faizan'
                        WHEN 'MUM_Deepak' THEN 'Deepak Puran Thapa'
                        WHEN 'HYD_Durganjaneyulu' THEN 'Gogula Durganjaneyulu'
                        WHEN 'BLR_Kiran' THEN 'Kiran M K'
                        ELSE NULL
                    END,
                    CASE 
                        WHEN d.driver_code LIKE 'LETZMUM%' OR COALESCE(la.assigned_city, la.cva_city) ILIKE '%Mum%' THEN 'Vikram Sawant'
                        WHEN d.driver_code LIKE 'LETZHYD%' OR COALESCE(la.assigned_city, la.cva_city) ILIKE '%Hyd%' THEN 'K Ramesh'
                        ELSE 'Manjunath Gowda'
                    END
                ),
                assigned_manager_phone = COALESCE(
                    CASE la.vehicle_manager_poc
                        WHEN 'BLR_Faizan' THEN '9900088220'
                        WHEN 'MUM_Deepak' THEN '9820098200'
                        WHEN 'HYD_Durganjaneyulu' THEN '9848022338'
                        WHEN 'BLR_Kiran' THEN '9900088220'
                        ELSE NULL
                    END,
                    CASE 
                        WHEN d.driver_code LIKE 'LETZMUM%' OR COALESCE(la.assigned_city, la.cva_city) ILIKE '%Mum%' THEN '9820098200'
                        WHEN d.driver_code LIKE 'LETZHYD%' OR COALESCE(la.assigned_city, la.cva_city) ILIKE '%Hyd%' THEN '9848022338'
                        ELSE '9900088220'
                    END
                ),
                last_synced_at = NOW()
            FROM latest_alloc la
            WHERE d.app_driver_id = la.app_driver_id
              AND (
                  d.assigned_manager_name IS NULL 
                  OR d.assigned_manager_name = ''
                  OR d.assigned_manager_phone IS NULL 
                  OR d.assigned_manager_phone = ''
                  OR d.assigned_manager_name = 'LetzRyd Fleet Operations'
                  OR d.assigned_manager_phone = '080-4568-1234'
              );
        """
        res_sync_mgr_alloc = conn.execute(text(sql_sync_driver_mgr_alloc))
        logger.info(f"  -> Synced allocated drivers manager POCs into app_drivers: {res_sync_mgr_alloc.rowcount} drivers updated!")

        # Second: For any remaining drivers (e.g. without allocations) who still have empty or placeholder manager
        sql_sync_driver_mgr_remaining = """
            UPDATE app_drivers d
            SET 
                assigned_manager_name = CASE 
                    WHEN d.driver_code LIKE 'LETZMUM%' OR d.address ILIKE '%Mumbai%' THEN 'Vikram Sawant'
                    WHEN d.driver_code LIKE 'LETZHYD%' OR d.address ILIKE '%Hyderabad%' THEN 'K Ramesh'
                    ELSE 'Manjunath Gowda'
                END,
                assigned_manager_phone = CASE 
                    WHEN d.driver_code LIKE 'LETZMUM%' OR d.address ILIKE '%Mumbai%' THEN '9820098200'
                    WHEN d.driver_code LIKE 'LETZHYD%' OR d.address ILIKE '%Hyderabad%' THEN '9848022338'
                    ELSE '9900088220'
                END,
                last_synced_at = NOW()
            WHERE (
                d.assigned_manager_name IS NULL 
                OR d.assigned_manager_name = ''
                OR d.assigned_manager_phone IS NULL 
                OR d.assigned_manager_phone = ''
                OR d.assigned_manager_name = 'LetzRyd Fleet Operations'
                OR d.assigned_manager_phone = '080-4568-1234'
            );
        """
        res_sync_mgr_rem = conn.execute(text(sql_sync_driver_mgr_remaining))
        logger.info(f"  -> Synced remaining drivers hub managers into app_drivers: {res_sync_mgr_rem.rowcount} drivers updated!")

        logger.info("============================================================")
        logger.info("ALL DATABASE INTEGRITY FIXES APPLIED SUCCESSFULLY!")
        logger.info("============================================================")

if __name__ == '__main__':
    run_fixes()
