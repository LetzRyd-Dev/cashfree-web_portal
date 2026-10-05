import os, psycopg2
from dotenv import load_dotenv

load_dotenv('cashfree-web_portal-main/.env')
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# 1. Update fn_trg_sync_allocation_to_app
cur.execute("""
CREATE OR REPLACE FUNCTION public.fn_trg_sync_allocation_to_app()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $function$
DECLARE
    v_clean_phone VARCHAR(15);
    v_driver_id INT;
    v_veh_num VARCHAR(20);
    v_operator_id INT := 0;
BEGIN
    IF TG_OP = 'DELETE' THEN
        DELETE FROM public.app_driver_allocations WHERE core_allocation_id = OLD.id;
        RETURN OLD;
    END IF;

    v_clean_phone := RIGHT(REGEXP_REPLACE(COALESCE(NEW.driver_phone, ''), '[^0-9]', '', 'g'), 10);
    v_veh_num := UPPER(REGEXP_REPLACE(COALESCE(NEW.vehicle_number, ''), '[^A-Za-z0-9]', '', 'g'));

    SELECT app_driver_id INTO v_driver_id FROM public.app_drivers WHERE phone = v_clean_phone LIMIT 1;

    -- Resolve operator_id if partner_type is Operator
    IF NEW.partner_type = 'Operator' AND NEW.partner_id IS NOT NULL AND NEW.partner_id != '' THEN
        SELECT op.app_operator_id INTO v_operator_id
        FROM public.app_operators op
        WHERE op.operator_code = NEW.partner_id
           OR op.phone = RIGHT(REGEXP_REPLACE(NEW.partner_id, '[^0-9]', '', 'g'), 10)
        LIMIT 1;
        IF v_operator_id IS NULL THEN
            v_operator_id := 0;
        END IF;
    END IF;

    IF v_driver_id IS NULL AND LENGTH(v_clean_phone) = 10 THEN
        INSERT INTO public.app_drivers (full_name, phone, initials, driver_code, is_active, operator_id)
        VALUES (TRIM(COALESCE(NEW.driver_name, 'Driver')), v_clean_phone, 'DR', 'DRV-AL-' || NEW.id::text, TRUE, v_operator_id)
        RETURNING app_driver_id INTO v_driver_id;
    END IF;

    IF v_driver_id IS NOT NULL THEN
        INSERT INTO public.app_driver_allocations (
            core_allocation_id, app_driver_id, app_operator_id, vehicle_number, allocation_date, start_odometer,
            daily_rental_rate, allocation_status, assigned_city, updated_at
        ) VALUES (
            NEW.id, v_driver_id, v_operator_id, v_veh_num, NEW.allocation_date, COALESCE(NEW.odometer_reading, 0),
            1000.00,
            CASE WHEN NEW.is_deleted = TRUE THEN 'CLOSED' ELSE 'ACTIVE' END,
            NEW.city, NOW()
        )
        ON CONFLICT (core_allocation_id) DO UPDATE SET
            app_driver_id = EXCLUDED.app_driver_id,
            app_operator_id = EXCLUDED.app_operator_id,
            vehicle_number = EXCLUDED.vehicle_number,
            allocation_date = EXCLUDED.allocation_date,
            start_odometer = EXCLUDED.start_odometer,
            allocation_status = EXCLUDED.allocation_status,
            assigned_city = EXCLUDED.assigned_city,
            updated_at = NOW();

        IF NEW.is_deleted = FALSE OR NEW.is_deleted IS NULL THEN
            UPDATE public.app_drivers
            SET 
                vehicle_reg_number = v_veh_num,
                vehicle_allocated_from = NEW.allocation_date,
                vehicle_odometer_km = COALESCE(NEW.odometer_reading, 0),
                operator_id = CASE WHEN v_operator_id > 0 THEN v_operator_id ELSE operator_id END,
                last_synced_at = NOW()
            WHERE app_driver_id = v_driver_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$function$;
""")
print("Trigger fn_trg_sync_allocation_to_app updated!")

# 2. Update fn_trg_sync_dropoffs_to_app
cur.execute("""
CREATE OR REPLACE FUNCTION public.fn_trg_sync_dropoffs_to_app()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $function$
DECLARE
    v_veh_num VARCHAR(20);
BEGIN
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    v_veh_num := UPPER(REGEXP_REPLACE(COALESCE(NEW.vehicle_number, ''), '[^A-Za-z0-9]', '', 'g'));

    IF v_veh_num != '' AND NEW.return_date IS NOT NULL THEN
        UPDATE public.app_driver_allocations
        SET 
            dropoff_date = NEW.return_date,
            allocation_status = 'RETURNED',
            updated_at = NOW()
        WHERE vehicle_number = v_veh_num
          AND allocation_date <= NEW.return_date
          AND (dropoff_date IS NULL OR dropoff_date = NEW.return_date);

        -- Clear vehicle_reg_number and current_vehicle_id when vehicle is dropped off
        UPDATE public.app_drivers
        SET 
            vehicle_reg_number = NULL,
            current_vehicle_id = NULL,
            last_synced_at = NOW()
        WHERE vehicle_reg_number = v_veh_num;
    END IF;

    RETURN NEW;
END;
$function$;
""")
print("Trigger fn_trg_sync_dropoffs_to_app updated!")

# 3. Update fn_trg_sync_hisaab_vehicle_to_app
cur.execute("""
CREATE OR REPLACE FUNCTION public.fn_trg_sync_hisaab_vehicle_to_app()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $function$
DECLARE
    v_clean_phone VARCHAR(15);
    v_driver_id INT;
    v_operator_id INT := 0;
    v_hisaab_num VARCHAR(100);
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_hisaab_num := 'HSB-' || OLD.week_id || '-' || UPPER(REGEXP_REPLACE(OLD.vehicle_number, '[^A-Za-z0-9]', '', 'g')) || '-' || UPPER(REGEXP_REPLACE(COALESCE(NULLIF(TRIM(OLD.partner_id), ''), OLD.id::text), '[^A-Za-z0-9]', '', 'g'));
        DELETE FROM public.app_hisaabs WHERE hisaab_number = v_hisaab_num;
        RETURN OLD;
    END IF;

    v_clean_phone := RIGHT(REGEXP_REPLACE(COALESCE(NEW.partner_id, ''), '[^0-9]', '', 'g'), 10);
    SELECT app_driver_id, operator_id INTO v_driver_id, v_operator_id
    FROM public.app_drivers 
    WHERE (LENGTH(v_clean_phone) = 10 AND phone = v_clean_phone) OR driver_code = NEW.partner_id 
    LIMIT 1;

    IF v_driver_id IS NULL THEN
        SELECT da.app_driver_id, da.app_operator_id INTO v_driver_id, v_operator_id
        FROM public.app_driver_allocations da
        WHERE da.vehicle_number = UPPER(REGEXP_REPLACE(NEW.vehicle_number, '[^A-Za-z0-9]', '', 'g'))
        ORDER BY da.allocation_date DESC LIMIT 1;

        IF v_driver_id IS NULL THEN
            SELECT app_driver_id, operator_id INTO v_driver_id, v_operator_id FROM public.app_drivers WHERE driver_code = 'SYSTEM_ONBOARDED' LIMIT 1;
        END IF;
    END IF;

    -- If operator not yet resolved, check vehicle allocation or partner_id
    IF COALESCE(v_operator_id, 0) = 0 THEN
        SELECT op.app_operator_id INTO v_operator_id
        FROM public.app_operators op
        WHERE op.operator_code = NEW.partner_id
           OR op.phone = v_clean_phone
        LIMIT 1;
    END IF;

    IF v_driver_id IS NOT NULL THEN
        v_hisaab_num := 'HSB-' || NEW.week_id || '-' || UPPER(REGEXP_REPLACE(NEW.vehicle_number, '[^A-Za-z0-9]', '', 'g')) || '-' || UPPER(REGEXP_REPLACE(COALESCE(NULLIF(TRIM(NEW.partner_id), ''), NEW.id::text), '[^A-Za-z0-9]', '', 'g'));

        -- Correct mapping:
        -- to_collect: money owed to LetzRyd (net_to_collect_from_driver)
        -- to_pay: payout to partner (net_payout_to_driver)
        INSERT INTO public.app_hisaabs (
            app_driver_id, app_operator_id, hisaab_number, week_number, period_start, period_end,
            days_count, status, uber_trips, uber_revenue, uber_cash, uber_toll, uber_incentive,
            ola_trips, ola_revenue, ola_cash, ola_toll, ola_incentive, vehicle_daily_rate,
            vehicle_rent, tds_amount, challan_amount, accident_charge, other_adjustment,
            gps_dead_km, gps_dead_penalty, completed_trips, total_gross_earnings,
            total_deductions, current_period_os, to_pay, to_collect, updated_at
        ) VALUES (
            v_driver_id, COALESCE(v_operator_id, 0), v_hisaab_num,
            COALESCE((SUBSTRING(NEW.week_id FROM '[0-9]+$'))::INT, 28),
            NEW.week_start, NEW.week_end, COALESCE(NEW.onroad_days::INT, 7),
            CASE WHEN NEW.net_to_collect_from_driver > 0 THEN 'to_collect' ELSE 'to_pay' END,
            NEW.uber_trips, NEW.uber_total_earnings, NEW.uber_cash_collection, NEW.uber_toll, NEW.uber_incentive,
            NEW.ola_trips, NEW.ola_net_revenue, NEW.ola_cash_collection, NEW.ola_toll, NEW.ola_incentive,
            NEW.daily_rent_applied, NEW.net_weekly_lease_rental, NEW.tds_amount, NEW.challan_amount,
            NEW.accident_deduction, NEW.adjustment_amount, NEW.gps_dead_km, NEW.gps_dead_mile_penalty,
            NEW.uber_trips + NEW.ola_trips,
            NEW.uber_total_earnings + NEW.uber_incentive + NEW.ola_net_revenue + NEW.ola_incentive,
            NEW.net_weekly_lease_rental + NEW.tds_amount + NEW.challan_amount + NEW.accident_deduction + NEW.gps_dead_mile_penalty - NEW.adjustment_amount,
            NEW.current_week_os, NEW.net_payout_to_driver, NEW.net_to_collect_from_driver, NOW()
        )
        ON CONFLICT (hisaab_number) DO UPDATE SET
            app_operator_id = EXCLUDED.app_operator_id,
            uber_trips = EXCLUDED.uber_trips,
            uber_revenue = EXCLUDED.uber_revenue,
            uber_cash = EXCLUDED.uber_cash,
            ola_trips = EXCLUDED.ola_trips,
            ola_revenue = EXCLUDED.ola_revenue,
            ola_cash = EXCLUDED.ola_cash,
            vehicle_rent = EXCLUDED.vehicle_rent,
            tds_amount = EXCLUDED.tds_amount,
            challan_amount = EXCLUDED.challan_amount,
            accident_charge = EXCLUDED.accident_charge,
            other_adjustment = EXCLUDED.other_adjustment,
            gps_dead_penalty = EXCLUDED.gps_dead_penalty,
            total_gross_earnings = EXCLUDED.total_gross_earnings,
            total_deductions = EXCLUDED.total_deductions,
            current_period_os = EXCLUDED.current_period_os,
            to_pay = EXCLUDED.to_pay,
            to_collect = EXCLUDED.to_collect,
            status = EXCLUDED.status,
            updated_at = NOW();

        UPDATE public.app_drivers
        SET
            cw_trips = NEW.uber_trips + NEW.ola_trips,
            cw_uber_revenue = NEW.uber_total_earnings,
            cw_ola_revenue = NEW.ola_net_revenue,
            cw_gross_earnings = NEW.uber_total_earnings + NEW.uber_incentive + NEW.ola_net_revenue + NEW.ola_incentive,
            cw_vehicle_rent = NEW.net_weekly_lease_rental,
            cw_os = NEW.current_period_os,
            cw_to_pay = NEW.net_payout_to_driver,
            cw_to_collect = NEW.net_to_collect_from_driver,
            cumulative_owed = ABS(NEW.net_to_collect_from_driver),
            lw_hisaab_number = v_hisaab_num,
            last_synced_at = NOW()
        WHERE app_driver_id = v_driver_id;
    END IF;

    RETURN NEW;
END;
$function$;
""")
print("Trigger fn_trg_sync_hisaab_vehicle_to_app updated!")

conn.commit()
cur.close()
conn.close()
print("All triggers deployed successfully!")
