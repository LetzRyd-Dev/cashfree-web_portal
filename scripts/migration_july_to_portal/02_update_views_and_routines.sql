-- =============================================================================
-- LETZRYD DATABASE MIGRATION SCRIPT 02: UPDATE VIEWS & STORED ROUTINES
-- =============================================================================
-- Purpose:
--   Updates all dependent views, 18 stored procedures/functions, and triggers
--   so they directly query and update 'portal_*' tables instead of legacy 'july_*'.
--
-- Why This Is Required:
--   PL/pgSQL functions and procedures store query text as plain text strings.
--   When tables are renamed, procedures continue executing the text string 'july_*'.
--   This script updates the procedure bodies to use 'portal_*', ensuring that:
--     1. 18 pg_cron jobs run with 0 errors.
--     2. Real-time triggers sync portal submissions directly into core_* tables.
-- =============================================================================

-- =============================================================================
-- SECTION 1: UPDATE VIEWS
-- =============================================================================

-- -----------------------------------------------------------------------------
-- View: vw_looker_form_tracking
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW public.vw_looker_form_tracking AS
 WITH dates AS (
         SELECT (generate_series((CURRENT_DATE - '180 days'::interval), (CURRENT_DATE + '30 days'::interval), '1 day'::interval))::date AS form_date
        ), all_walkins AS (
         SELECT COALESCE((((portal_new_walkins.created_at AT TIME ZONE 'UTC'::text) AT TIME ZONE 'Asia/Kolkata'::text))::date,
                CASE
                    WHEN ((portal_new_walkins.event_date)::text ~ '^\d{4}-\d{2}-\d{2}'::text) THEN (SUBSTRING((portal_new_walkins.event_date)::text FROM 1 FOR 10))::date
                    ELSE NULL::date
                END, '2026-08-01'::date) AS form_date
           FROM portal_new_walkins
        UNION ALL
         SELECT COALESCE((((portal_walkins.created_at AT TIME ZONE 'UTC'::text) AT TIME ZONE 'Asia/Kolkata'::text))::date,
                CASE
                    WHEN ((portal_walkins.event_date)::text ~ '^\d{4}-\d{2}-\d{2}'::text) THEN (SUBSTRING((portal_walkins.event_date)::text FROM 1 FOR 10))::date
                    ELSE NULL::date
                END, '2026-08-01'::date) AS form_date
           FROM portal_walkins
        UNION ALL
         SELECT COALESCE((((portal_existing_walkins.created_at AT TIME ZONE 'UTC'::text) AT TIME ZONE 'Asia/Kolkata'::text))::date,
                CASE
                    WHEN ((portal_existing_walkins.event_date)::text ~ '^\d{4}-\d{2}-\d{2}'::text) THEN (SUBSTRING((portal_existing_walkins.event_date)::text FROM 1 FOR 10))::date
                    ELSE NULL::date
                END, '2026-08-05'::date) AS form_date
           FROM portal_existing_walkins
        ), walkins_daily AS (
         SELECT all_walkins.form_date,
            count(*) AS walkin_count
           FROM all_walkins
          WHERE (all_walkins.form_date IS NOT NULL)
          GROUP BY all_walkins.form_date
        ), onboarding_daily AS (
         SELECT (((portal_form_onboarding.created_at AT TIME ZONE 'UTC'::text) AT TIME ZONE 'Asia/Kolkata'::text))::date AS form_date,
            count(*) AS onboarding_count
           FROM portal_form_onboarding
          WHERE ((portal_form_onboarding.created_at IS NOT NULL) AND ((portal_form_onboarding.approval_status IS NULL) OR (lower((portal_form_onboarding.approval_status)::text) <> 'draft'::text)))
          GROUP BY ((((portal_form_onboarding.created_at AT TIME ZONE 'UTC'::text) AT TIME ZONE 'Asia/Kolkata'::text))::date)
        ), vehicle_onboarding_daily AS (
         SELECT (((portal_vehicle_onboarding.created_at AT TIME ZONE 'UTC'::text) AT TIME ZONE 'Asia/Kolkata'::text))::date AS form_date,
            count(*) AS vehicle_onboarding_count
           FROM portal_vehicle_onboarding
          WHERE (portal_vehicle_onboarding.created_at IS NOT NULL)
          GROUP BY ((((portal_vehicle_onboarding.created_at AT TIME ZONE 'UTC'::text) AT TIME ZONE 'Asia/Kolkata'::text))::date)
        ), allocation_daily AS (
         SELECT (((portal_allocation_form.created_at AT TIME ZONE 'UTC'::text) AT TIME ZONE 'Asia/Kolkata'::text))::date AS form_date,
            count(*) AS allocation_count
           FROM portal_allocation_form
          WHERE ((portal_allocation_form.created_at IS NOT NULL) AND ((portal_allocation_form.status IS NULL) OR (lower((portal_allocation_form.status)::text) <> 'draft'::text)) AND ((portal_allocation_form.approval_status IS NULL) OR (lower((portal_allocation_form.approval_status)::text) <> 'draft'::text)))
          GROUP BY ((((portal_allocation_form.created_at AT TIME ZONE 'UTC'::text) AT TIME ZONE 'Asia/Kolkata'::text))::date)
        ), dropoff_daily AS (
         SELECT (((portal_allocation_form.created_at AT TIME ZONE 'UTC'::text) AT TIME ZONE 'Asia/Kolkata'::text))::date AS form_date,
            count(*) AS dropoff_count
           FROM portal_allocation_form
          WHERE ((portal_allocation_form.created_at IS NOT NULL) AND ((portal_allocation_form.status IS NULL) OR (lower((portal_allocation_form.status)::text) <> 'draft'::text)) AND ((portal_allocation_form.approval_status IS NULL) OR (lower((portal_allocation_form.approval_status)::text) <> 'draft'::text)) AND (((portal_allocation_form.allocation_type)::text = 'Drop-Off'::text) OR ((portal_allocation_form.sub_type)::text = ANY ((ARRAY['Drop-Off'::character varying, 'Voluntary Return'::character varying, 'Contract Completion'::character varying, 'Non-payment / Default'::character varying, 'Vehicle Breakdown / Maintenance'::character varying, 'Other'::character varying])::text[]))))
          GROUP BY ((((portal_allocation_form.created_at AT TIME ZONE 'UTC'::text) AT TIME ZONE 'Asia/Kolkata'::text))::date)
        )
 SELECT d.form_date AS date,
    COALESCE(w.walkin_count, (0)::bigint) AS walk_in_form,
    COALESCE(o.onboarding_count, (0)::bigint) AS partner_onboarding,
    COALESCE(vo.vehicle_onboarding_count, (0)::bigint) AS vehicle_onboarding,
    COALESCE(a.allocation_count, (0)::bigint) AS allocation_form,
    COALESCE(dp.dropoff_count, (0)::bigint) AS drop_off,
    ((((COALESCE(w.walkin_count, (0)::bigint) + COALESCE(o.onboarding_count, (0)::bigint)) + COALESCE(vo.vehicle_onboarding_count, (0)::bigint)) + COALESCE(a.allocation_count, (0)::bigint)) + COALESCE(dp.dropoff_count, (0)::bigint)) AS total
   FROM (((((dates d
     LEFT JOIN walkins_daily w ON ((d.form_date = w.form_date)))
     LEFT JOIN onboarding_daily o ON ((d.form_date = o.form_date)))
     LEFT JOIN vehicle_onboarding_daily vo ON ((d.form_date = vo.form_date)))
     LEFT JOIN allocation_daily a ON ((d.form_date = a.form_date)))
     LEFT JOIN dropoff_daily dp ON ((d.form_date = dp.form_date)))
  WHERE (((((COALESCE(w.walkin_count, (0)::bigint) + COALESCE(o.onboarding_count, (0)::bigint)) + COALESCE(vo.vehicle_onboarding_count, (0)::bigint)) + COALESCE(a.allocation_count, (0)::bigint)) + COALESCE(dp.dropoff_count, (0)::bigint)) > 0)
  ORDER BY d.form_date DESC;

-- -----------------------------------------------------------------------------
-- View: portal_v_kpi_summary
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW public.portal_v_kpi_summary AS
 SELECT count(DISTINCT vehicle_number) AS total_vehicles_in_hisaab,
    COALESCE(sum(ola_trips), (0)::bigint) AS total_ola_trips,
    COALESCE(sum(total_gross_earnings), (0)::numeric) AS total_gross_earnings,
    COALESCE(sum(total_cash_collected), (0)::numeric) AS total_cash_collected,
    COALESCE(sum(net_weekly_rent), (0)::numeric) AS total_rent_collected,
    COALESCE(sum(tds), (0)::numeric) AS total_tds_deducted,
    COALESCE(sum(to_collect), (0)::numeric) AS total_pending_to_collect,
    COALESCE(sum(to_pay), (0)::numeric) AS total_pending_to_pay,
    COALESCE(sum(letzryd_earning), (0)::numeric) AS total_letzryd_earnings
   FROM portal_hisaab_weekly_statement s;

-- -----------------------------------------------------------------------------
-- View: view_weekly_platform_earnings (Conditional on z_rapido_raw_16)
-- -----------------------------------------------------------------------------
DO $view_blk$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'z_rapido_raw_16') THEN
        EXECUTE $view_stmt$
CREATE OR REPLACE VIEW public.view_weekly_platform_earnings AS
 WITH ola_kpis AS (
         SELECT portal_ola_weekly_summary.vehicle_number,
            portal_ola_weekly_summary.week_start,
            portal_ola_weekly_summary.week_end,
            portal_ola_weekly_summary.trips AS ola_trips,
            portal_ola_weekly_summary.revenue AS ola_revenue,
            portal_ola_weekly_summary.cash_collection AS ola_cash_collection,
            portal_ola_weekly_summary.toll AS ola_toll,
            portal_ola_weekly_summary.incentive AS ola_incentive,
            portal_ola_weekly_summary.subscription AS ola_subscription,
            portal_ola_weekly_summary.km AS ola_km,
            portal_ola_weekly_summary.tds AS ola_tds
           FROM portal_ola_weekly_summary
        ), uber_kpis AS (
         SELECT uber_raw.number_plate AS vehicle_number,
            (date_trunc('week'::text, COALESCE((uber_raw.trip_date)::timestamp without time zone, (uber_raw.new_date)::timestamp without time zone, uber_raw.trip_request_time)))::date AS week_start,
            ((date_trunc('week'::text, COALESCE((uber_raw.trip_date)::timestamp without time zone, (uber_raw.new_date)::timestamp without time zone, uber_raw.trip_request_time)) + '6 days'::interval))::date AS week_end,
            count(*) AS uber_trips,
            sum((COALESCE(uber_raw.trip_distance, (0)::numeric) * 15.0)) AS uber_revenue,
            0.00 AS uber_cash_collection,
            0.00 AS uber_toll,
            0.00 AS uber_incentive,
            0.00 AS uber_subscription,
            sum(COALESCE(uber_raw.trip_distance, (0)::numeric)) AS uber_km
           FROM uber_raw
          WHERE ((uber_raw.number_plate IS NOT NULL) AND ((uber_raw.trip_date IS NOT NULL) OR (uber_raw.new_date IS NOT NULL) OR (uber_raw.trip_request_time IS NOT NULL)))
          GROUP BY uber_raw.number_plate, (date_trunc('week'::text, COALESCE((uber_raw.trip_date)::timestamp without time zone, (uber_raw.new_date)::timestamp without time zone, uber_raw.trip_request_time)))
        ), rapido_kpis AS (
         SELECT z_rapido_raw_16.vehicle_number,
            (date_trunc('week'::text, (z_rapido_raw_16.trip_date)::timestamp with time zone))::date AS week_start,
            ((date_trunc('week'::text, (z_rapido_raw_16.trip_date)::timestamp with time zone) + '6 days'::interval))::date AS week_end,
            count(*) AS rapido_trips,
            sum(COALESCE(z_rapido_raw_16.net_revenue, (0)::numeric)) AS rapido_revenue,
            0.00 AS rapido_cash_collection,
            sum(COALESCE(z_rapido_raw_16.tolls, (0)::numeric)) AS rapido_toll,
            0.00 AS rapido_incentive,
            0.00 AS rapido_subscription,
            sum(COALESCE(z_rapido_raw_16.distance_kms, (0)::numeric)) AS rapido_km
           FROM z_rapido_raw_16
          WHERE ((z_rapido_raw_16.vehicle_number IS NOT NULL) AND (z_rapido_raw_16.trip_date IS NOT NULL))
          GROUP BY z_rapido_raw_16.vehicle_number, (date_trunc('week'::text, (z_rapido_raw_16.trip_date)::timestamp with time zone))
        )
 SELECT COALESCE(o.vehicle_number, (u.vehicle_number)::character varying, r.vehicle_number) AS vehicle_number,
    COALESCE(o.week_start, u.week_start, r.week_start) AS week_start,
    COALESCE(o.week_end, u.week_end, r.week_end) AS week_end,
    COALESCE(o.ola_trips, 0) AS ola_trips,
    COALESCE(o.ola_revenue, (0)::numeric) AS ola_revenue,
    COALESCE(o.ola_cash_collection, (0)::numeric) AS ola_cash_collection,
    COALESCE(o.ola_toll, (0)::numeric) AS ola_toll,
    COALESCE(o.ola_incentive, (0)::numeric) AS ola_incentive,
    COALESCE(o.ola_subscription, (0)::numeric) AS ola_subscription,
    COALESCE(o.ola_km, (0)::numeric) AS ola_km,
    COALESCE(o.ola_tds, (0)::numeric) AS ola_tds,
    COALESCE(u.uber_trips, (0)::bigint) AS uber_trips,
    COALESCE(u.uber_revenue, (0)::numeric) AS uber_revenue,
    COALESCE(u.uber_cash_collection, (0)::numeric) AS uber_cash_collection,
    COALESCE(u.uber_toll, (0)::numeric) AS uber_toll,
    COALESCE(u.uber_incentive, (0)::numeric) AS uber_incentive,
    COALESCE(u.uber_subscription, (0)::numeric) AS uber_subscription,
    COALESCE(u.uber_km, (0)::numeric) AS uber_km,
    COALESCE(r.rapido_trips, (0)::bigint) AS rapido_trips,
    COALESCE(r.rapido_revenue, (0)::numeric) AS rapido_revenue,
    COALESCE(r.rapido_cash_collection, (0)::numeric) AS rapido_cash_collection,
    COALESCE(r.rapido_toll, (0)::numeric) AS rapido_toll,
    COALESCE(r.rapido_incentive, (0)::numeric) AS rapido_incentive,
    COALESCE(r.rapido_subscription, (0)::numeric) AS rapido_subscription,
    COALESCE(r.rapido_km, (0)::numeric) AS rapido_km
   FROM ((ola_kpis o
     FULL JOIN uber_kpis u ON ((((o.vehicle_number)::text = u.vehicle_number) AND (o.week_start = u.week_start))))
     FULL JOIN rapido_kpis r ON ((((COALESCE(o.vehicle_number, (u.vehicle_number)::character varying))::text = (r.vehicle_number)::text) AND (COALESCE(o.week_start, u.week_start) = r.week_start))));
        $view_stmt$;
        RAISE NOTICE 'SUCCESS: Created view public.view_weekly_platform_earnings';
    ELSE
        RAISE NOTICE 'NOTICE: Skipping public.view_weekly_platform_earnings because z_rapido_raw_16 is not present in this environment.';
    END IF;
END $view_blk$;

-- -----------------------------------------------------------------------------
-- View: view_portal_ola_weekly_kpis
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW public.view_portal_ola_weekly_kpis AS
 WITH raw_agg AS (
         SELECT portal_ola_raw.vehicle_number,
            portal_ola_raw.week_start,
            portal_ola_raw.week_end,
            max((portal_ola_raw.driver_name)::text) AS driver_name,
            max((portal_ola_raw.driver_number)::text) AS driver_number,
            count(
                CASE
                    WHEN (((portal_ola_raw.completion_status)::text = ANY ((ARRAY['COMPLETED'::character varying, 'FINISHED'::character varying, 'COMPLETED_RIDE'::character varying])::text[])) OR (portal_ola_raw.bookings_completed_raw > 0)) THEN 1
                    ELSE NULL::integer
                END) AS trips,
            sum(COALESCE(portal_ola_raw.operator_bill_raw, portal_ola_raw.ride_earnings_raw, (0)::numeric)) AS revenue,
            sum(COALESCE(portal_ola_raw.cash_collected_by_driver_raw, (0)::numeric)) AS cash_collection,
            sum(COALESCE(portal_ola_raw.toll_parking_raw, (0)::numeric)) AS toll,
            sum(GREATEST((0)::numeric, (COALESCE(portal_ola_raw.customer_bill_raw, (0)::numeric) - COALESCE(portal_ola_raw.operator_bill_raw, (0)::numeric)))) AS subscription,
            sum(COALESCE(portal_ola_raw.actual_kms_raw, (0)::numeric)) AS km,
            sum(COALESCE(portal_ola_raw.tds_raw, (0)::numeric)) AS tds,
            count(*) AS raw_trips_count
           FROM portal_ola_raw
          WHERE ((portal_ola_raw.week_start IS NOT NULL) AND (portal_ola_raw.week_end IS NOT NULL))
          GROUP BY portal_ola_raw.vehicle_number, portal_ola_raw.week_start, portal_ola_raw.week_end
        ), inc_agg AS (
         SELECT portal_ola_incentive.vehicle_number,
            portal_ola_incentive.week_start,
            portal_ola_incentive.week_end,
            sum(COALESCE(portal_ola_incentive.received_incentive, portal_ola_incentive.slab_amount, portal_ola_incentive.after_tds, (0)::numeric)) AS incentive
           FROM portal_ola_incentive
          WHERE ((portal_ola_incentive.week_start IS NOT NULL) AND (portal_ola_incentive.week_end IS NOT NULL))
          GROUP BY portal_ola_incentive.vehicle_number, portal_ola_incentive.week_start, portal_ola_incentive.week_end
        )
 SELECT r.vehicle_number,
    r.driver_name,
    r.driver_number,
    r.week_start,
    r.week_end,
    COALESCE((EXTRACT(week FROM r.week_start))::integer, 1) AS week_number,
    r.trips,
    r.revenue,
    r.cash_collection,
    r.toll,
    COALESCE(i.incentive, (0)::numeric) AS incentive,
    r.subscription,
    r.km,
    r.tds,
    r.raw_trips_count
   FROM (raw_agg r
     LEFT JOIN inc_agg i ON ((((r.vehicle_number)::text = (i.vehicle_number)::text) AND (r.week_start = i.week_start) AND (r.week_end = i.week_end))));


-- Backward-compatibility views for renamed views:
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.views WHERE table_schema = 'public' AND table_name = 'view_portal_ola_weekly_kpis') THEN
        CREATE OR REPLACE VIEW public.view_july_ola_weekly_kpis AS 
        SELECT * FROM public.view_portal_ola_weekly_kpis;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.views WHERE table_schema = 'public' AND table_name = 'portal_v_kpi_summary') THEN
        CREATE OR REPLACE VIEW public.july_v_kpi_summary AS 
        SELECT * FROM public.portal_v_kpi_summary;
    END IF;
END $$;

-- =============================================================================
-- SECTION 2: UPDATE STORED PROCEDURES & TRIGGER FUNCTIONS
-- =============================================================================

-- -----------------------------------------------------------------------------
-- FUNCTION: fn_sync_core_maintenance_from_portal_in (original: fn_sync_core_maintenance_from_portal_in)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.fn_sync_core_maintenance_from_portal_in()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_next_id BIGINT;
    v_clean_veh VARCHAR(50);
    v_clean_city VARCHAR(100);
    v_start_date DATE;
    v_in_dt TIMESTAMP WITHOUT TIME ZONE;
    v_est_delivery DATE;
    v_appr_date DATE;
    v_est_amt NUMERIC(12, 2);
    v_in_kms INTEGER;
    v_ins_claimed BOOLEAN;
    v_out RECORD;
    v_end_date DATE;
    v_out_dt TIMESTAMP WITHOUT TIME ZONE;
    v_out_kms INTEGER;
    v_inv_date DATE;
    v_inv_amt NUMERIC(12, 2);
    v_ins_disc NUMERIC(12, 2);
    v_payable NUMERIC(12, 2);
    v_status VARCHAR(50);
    v_attrs JSONB := '{}'::jsonb;
BEGIN
    -- Handle Soft Delete
    IF TG_OP = 'DELETE' THEN
        UPDATE public.core_maintenance
        SET is_deleted = TRUE,
            deleted_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'),
            updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
        WHERE portal_maintenance_in_id = OLD.id;
        RETURN OLD;
    END IF;

    -- Clean & Parse Inward Attributes
    v_clean_veh := public.fn_clean_maintenance_vehicle(NEW.vehicle_number);
    v_clean_city := public.fn_clean_maintenance_city(NEW.city_name, v_clean_veh);
    v_in_dt := public.fn_parse_maintenance_timestamp(NEW.vehicle_in_date_time);
    v_start_date := COALESCE(v_in_dt::DATE, NEW.created_at::DATE, (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')::DATE);
    v_est_delivery := public.fn_parse_maintenance_date(NEW.estimated_delivery_date);
    v_appr_date := public.fn_parse_maintenance_date(NEW.approval_date);
    v_est_amt := public.fn_parse_maintenance_numeric(NEW.estimated_amount);
    v_in_kms := public.fn_parse_maintenance_int(NEW.vehicle_k_m_s);
    v_ins_claimed := CASE WHEN LOWER(TRIM(COALESCE(NEW.insurance_claimed, ''))) IN ('yes', 'true', '1') THEN TRUE ELSE FALSE END;

    IF v_clean_veh IN ('TEST', 'TESTVEHICLE', 'ROLLERTEST') OR v_clean_veh ILIKE '%TEST%' THEN
        v_attrs := jsonb_set(v_attrs, '{is_test}', 'true'::jsonb);
    END IF;

    -- Check for paired outward release in portal_maintenance_out
    SELECT * INTO v_out FROM public.portal_maintenance_out WHERE inward_id = NEW.id ORDER BY id DESC LIMIT 1;
    IF FOUND THEN
        v_out_dt := public.fn_parse_maintenance_timestamp(v_out.vehicle_out_date_time);
        v_end_date := COALESCE(public.fn_parse_maintenance_date(v_out.rfd_date), v_out_dt::DATE);
        IF v_end_date IS NOT NULL AND v_end_date < v_start_date THEN
            v_end_date := v_start_date; -- Non-negative duration enforcement
        END IF;
        v_out_kms := public.fn_parse_maintenance_int(v_out.vehicle_out_k_m_s);
        IF v_in_kms IS NOT NULL AND v_out_kms IS NOT NULL AND v_out_kms < v_in_kms THEN
            v_attrs := jsonb_set(v_attrs, '{odometer_warning}', to_jsonb(format('Outward odometer (%s) lower than intake odometer (%s)', v_out_kms, v_in_kms)));
        END IF;
        v_inv_date := public.fn_parse_maintenance_date(v_out.invoice_date);
        v_inv_amt := public.fn_parse_maintenance_numeric(v_out.invoice_amount);
        v_ins_disc := public.fn_parse_maintenance_numeric(v_out.insurance_liability_discounts);
        v_payable := public.fn_parse_maintenance_numeric(v_out.letzryd_payable);
        v_status := COALESCE(v_out.final_status, 'Completed & RFD');
    ELSE
        v_end_date := NULL;
        v_out_dt := NULL;
        v_out_kms := NULL;
        v_inv_date := NULL;
        v_inv_amt := 0.00;
        v_ins_disc := 0.00;
        v_payable := 0.00;
        v_status := CASE WHEN NEW.is_closed = TRUE THEN 'COMPLETED' ELSE 'IN_PROGRESS' END;
    END IF;

    -- Acquire Advisory Lock for Gapless ID Assignment
    PERFORM pg_advisory_xact_lock(888999111);

    -- 1. If record already exists by portal_maintenance_in_id, update it
    IF EXISTS (SELECT 1 FROM public.core_maintenance WHERE portal_maintenance_in_id = NEW.id) THEN
        UPDATE public.core_maintenance SET
            source_type = 'WEB_PORTAL',
            portal_maintenance_out_id = v_out.id,
            vehicle_number = v_clean_veh,
            city = v_clean_city,
            vehicle_location = NEW.vehicle_location,
            start_date = v_start_date,
            end_date = v_end_date,
            in_date_time = v_in_dt,
            out_date_time = v_out_dt,
            estimated_delivery_date = v_est_delivery,
            rfd_date = v_end_date,
            maintenance_status = v_status,
            cohort = 'Off Road',
            repair_type = NEW.repair_type,
            workshop_name = NEW.workshop_name,
            in_kms = v_in_kms,
            out_kms = v_out_kms,
            remarks = COALESCE(NEW.remarks, v_out.remarks),
            estimated_amount = v_est_amt,
            invoice_no = v_out.invoice_no,
            invoice_date = v_inv_date,
            invoice_amount = v_inv_amt,
            insurance_claimed = v_ins_claimed,
            insurance_brokerage = NEW.insurance_brokerage,
            claim_number = NEW.claim_number,
            insurance_liability_discounts = v_ins_disc,
            letzryd_payable = v_payable,
            type_of_payment = v_out.type_of_payment,
            payment_status = v_out.payment_status,
            utr_no = v_out.utr_no,
            approved_by = COALESCE(NEW.approved_by, v_out.approved_by),
            approval_date = COALESCE(v_appr_date, public.fn_parse_maintenance_date(v_out.approval_date)),
            approval_file = COALESCE(NEW.approval_file, v_out.approval_file),
            damage_photos = NEW.vehicle_damage_photos,
            outward_photos = v_out.vehicle_out_photos,
            invoice_file = v_out.invoice_file,
            extra_attributes = COALESCE(extra_attributes, '{}'::jsonb) || v_attrs,
            is_deleted = FALSE,
            deleted_at = NULL,
            updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
        WHERE portal_maintenance_in_id = NEW.id;

    -- 2. PORTAL PRECEDENCE: If an active GOOGLE_SHEET record already exists for this vehicle & date, upgrade it in-place
    ELSIF EXISTS (
        SELECT 1 FROM public.core_maintenance 
        WHERE vehicle_number = v_clean_veh 
          AND source_type = 'GOOGLE_SHEET' 
          AND is_deleted = FALSE 
          AND (start_date = v_start_date OR (end_date IS NOT NULL AND v_start_date BETWEEN start_date AND end_date))
    ) THEN
        UPDATE public.core_maintenance SET
            source_type = 'WEB_PORTAL',
            portal_maintenance_in_id = NEW.id,
            portal_maintenance_out_id = v_out.id,
            city = v_clean_city,
            vehicle_location = NEW.vehicle_location,
            start_date = v_start_date,
            end_date = v_end_date,
            in_date_time = v_in_dt,
            out_date_time = v_out_dt,
            estimated_delivery_date = v_est_delivery,
            rfd_date = v_end_date,
            maintenance_status = v_status,
            cohort = 'Off Road',
            repair_type = NEW.repair_type,
            workshop_name = NEW.workshop_name,
            in_kms = v_in_kms,
            out_kms = v_out_kms,
            remarks = COALESCE(NEW.remarks, v_out.remarks),
            estimated_amount = v_est_amt,
            invoice_no = v_out.invoice_no,
            invoice_date = v_inv_date,
            invoice_amount = v_inv_amt,
            insurance_claimed = v_ins_claimed,
            insurance_brokerage = NEW.insurance_brokerage,
            claim_number = NEW.claim_number,
            insurance_liability_discounts = v_ins_disc,
            letzryd_payable = v_payable,
            type_of_payment = v_out.type_of_payment,
            payment_status = v_out.payment_status,
            utr_no = v_out.utr_no,
            approved_by = COALESCE(NEW.approved_by, v_out.approved_by),
            approval_date = COALESCE(v_appr_date, public.fn_parse_maintenance_date(v_out.approval_date)),
            approval_file = COALESCE(NEW.approval_file, v_out.approval_file),
            damage_photos = NEW.vehicle_damage_photos,
            outward_photos = v_out.vehicle_out_photos,
            invoice_file = v_out.invoice_file,
            extra_attributes = COALESCE(extra_attributes, '{}'::jsonb) || v_attrs,
            is_deleted = FALSE,
            deleted_at = NULL,
            updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
        WHERE vehicle_number = v_clean_veh 
          AND source_type = 'GOOGLE_SHEET' 
          AND is_deleted = FALSE 
          AND (start_date = v_start_date OR (end_date IS NOT NULL AND v_start_date BETWEEN start_date AND end_date));

        -- Soft-delete any redundant subsequent-day sheet records covered by this portal repair window
        UPDATE public.core_maintenance
        SET is_deleted = TRUE,
            deleted_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'),
            updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'),
            extra_attributes = jsonb_set(COALESCE(extra_attributes, '{}'::jsonb), '{superseded_by_portal}', to_jsonb(NEW.id))
        WHERE vehicle_number = v_clean_veh
          AND source_type = 'GOOGLE_SHEET'
          AND is_deleted = FALSE
          AND start_date > v_start_date
          AND (v_end_date IS NULL OR start_date <= v_end_date);

    -- 3. Otherwise, assign next gapless ID and insert
    ELSE
        SELECT COALESCE(MAX(id), 0) + 1 INTO v_next_id FROM public.core_maintenance;

        INSERT INTO public.core_maintenance (
            id, source_type, portal_maintenance_in_id, portal_maintenance_out_id, sheet_maintenance_id,
            vehicle_number, city, vehicle_location, vehicle_model,
            start_date, end_date, in_date_time, out_date_time, estimated_delivery_date, rfd_date,
            maintenance_status, cohort, partner_name, partner_ids, new_partner_name_default, dm_name, type, mapping,
            repair_type, workshop_name, in_kms, out_kms, job_card_number, remarks,
            estimated_amount, invoice_no, invoice_date, invoice_amount,
            insurance_claimed, insurance_brokerage, claim_number, insurance_liability_discounts, letzryd_payable,
            type_of_payment, payment_status, utr_no, approved_by, approval_date,
            approval_file, damage_photos, outward_photos, invoice_file,
            extra_attributes, is_deleted, deleted_at, created_at, updated_at
        ) VALUES (
            v_next_id, 'WEB_PORTAL', NEW.id, v_out.id, NULL,
            v_clean_veh, v_clean_city, NEW.vehicle_location, NULL,
            v_start_date, v_end_date, v_in_dt, v_out_dt, v_est_delivery, v_end_date,
            v_status, 'Off Road', NULL, NULL, NULL, NULL, NULL, NULL,
            NEW.repair_type, NEW.workshop_name, v_in_kms, v_out_kms, NULL, COALESCE(NEW.remarks, v_out.remarks),
            v_est_amt, v_out.invoice_no, v_inv_date, v_inv_amt,
            v_ins_claimed, NEW.insurance_brokerage, NEW.claim_number, v_ins_disc, v_payable,
            v_out.type_of_payment, v_out.payment_status, v_out.utr_no, COALESCE(NEW.approved_by, v_out.approved_by), COALESCE(v_appr_date, public.fn_parse_maintenance_date(v_out.approval_date)),
            COALESCE(NEW.approval_file, v_out.approval_file), NEW.vehicle_damage_photos, v_out.vehicle_out_photos, v_out.invoice_file,
            v_attrs, FALSE, NULL,
            (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'),
            (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
        );
    END IF;

    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'fn_sync_core_maintenance_from_portal_in error shielded: % (SQLSTATE: %). Source table operation unaffected.', SQLERRM, SQLSTATE;
    RETURN COALESCE(NEW, OLD);
END;
$function$
;

-- -----------------------------------------------------------------------------
-- FUNCTION: fn_sync_core_vehicle_from_portal (original: fn_sync_core_vehicle_from_portal)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.fn_sync_core_vehicle_from_portal()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_clean_plate VARCHAR(50);
    v_clean_city VARCHAR(100);
    v_reg_date DATE;
    v_rto_tax DATE;
    v_permit_val DATE;
    v_fit_val DATE;
    v_pol_val DATE;
    v_ins_val DATE;
    v_ins_start DATE;
    v_cng_date DATE;
    v_existing_id BIGINT;
    v_existing_sheet_id BIGINT;
BEGIN
    BEGIN
        -- Handle DELETE (Soft-Delete or Fallback to Sheet for Merged Assets)
        IF TG_OP = 'DELETE' THEN
            UPDATE public.core_vehicle_onboarding
            SET 
                source_system = CASE WHEN sheet_vehicle_id IS NOT NULL THEN 'GOOGLE_SHEET' ELSE source_system END,
                portal_vehicle_id = NULL,
                is_deleted = CASE WHEN sheet_vehicle_id IS NOT NULL THEN FALSE ELSE TRUE END,
                deleted_at = CASE WHEN sheet_vehicle_id IS NOT NULL THEN NULL ELSE (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata') END,
                updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
            WHERE portal_vehicle_id = OLD.id;
        ELSIF TG_OP IN ('INSERT', 'UPDATE') THEN
            -- Clean Key Values
            v_clean_plate := public.fn_clean_plate(NEW.vehicle_number);
            v_clean_city := public.fn_clean_city_name(NEW.city_name);
            
            IF v_clean_plate IS NOT NULL THEN
                -- Parse Dates
                v_reg_date   := public.fn_parse_flexible_date(NEW.registration_date);
                v_rto_tax    := public.fn_parse_flexible_date(NEW.rto_tax_validity);
                v_permit_val := COALESCE(NEW.permit_end_date, public.fn_parse_flexible_date(NEW.permit_validity));
                v_fit_val    := COALESCE(NEW.fitness_end_date, public.fn_parse_flexible_date(NEW.fitness_validity));
                v_pol_val    := public.fn_parse_flexible_date(NEW.pollution_validity);
                v_ins_val    := public.fn_parse_flexible_date(NEW.insurance_validity);
                v_ins_start  := public.fn_parse_flexible_date(NEW.insurance_start_date);
                v_cng_date   := public.fn_parse_flexible_date(NEW.cng_installation_date);

                -- Check if record already exists under this Plate
                SELECT id, sheet_vehicle_id INTO v_existing_id, v_existing_sheet_id
                FROM public.core_vehicle_onboarding
                WHERE registration_no = v_clean_plate;

                IF v_existing_id IS NOT NULL THEN
                    -- UPDATE with Portal Precedence
                    UPDATE public.core_vehicle_onboarding
                    SET 
                        source_system = CASE WHEN v_existing_sheet_id IS NOT NULL THEN 'MERGED_PORTAL_SHEET' ELSE 'PORTAL_FORM' END,
                        source_table = 'portal_vehicle_onboarding',
                        portal_vehicle_id = NEW.id,
                        letzryd_unique_no = COALESCE(NULLIF(NEW.letzryd_unique_no, ''), letzryd_unique_no),
                        chassis_no = COALESCE(NULLIF(NEW.chassis_number, ''), chassis_no),
                        engine_no = COALESCE(NULLIF(NEW.engine_number, ''), engine_no),
                        city = v_clean_city,
                        model = COALESCE(NULLIF(NEW.model, ''), model),
                        fuel_type = COALESCE(NULLIF(NEW.fuel_type, ''), fuel_type, 'CNG'),
                        color = COALESCE(NULLIF(NEW.color, ''), color),
                        dealer_name = COALESCE(NULLIF(NEW.dealer_name, ''), dealer_name),
                        registered_owner_name = COALESCE(NULLIF(NEW.registered_owner_name, ''), registered_owner_name),
                        hp_details = COALESCE(NULLIF(NEW.hp_details, ''), hp_details),
                        mfg_date = COALESCE(NULLIF(NEW.mfg_date, ''), mfg_date),
                        received_allocated = COALESCE(NULLIF(NEW.received_allocated, ''), received_allocated),
                        delivery_month = COALESCE(NULLIF(NEW.delivery_month, ''), delivery_month),
                        registration_date = COALESCE(v_reg_date, registration_date),
                        invoice_date = COALESCE(NEW.invoice_date, invoice_date),
                        invoice_no = COALESCE(NULLIF(NEW.invoice_no, ''), invoice_no),
                        rto_tax_validity = COALESCE(v_rto_tax, rto_tax_validity),
                        permit_validity = COALESCE(v_permit_val, permit_validity),
                        permit_start_date = COALESCE(NEW.permit_start_date, permit_start_date),
                        permit_end_date = COALESCE(NEW.permit_end_date, permit_end_date),
                        permit_type = COALESCE(NULLIF(NEW.permit_type, ''), permit_type),
                        fitness_validity = COALESCE(v_fit_val, fitness_validity),
                        fitness_start_date = COALESCE(NEW.fitness_start_date, fitness_start_date),
                        fitness_end_date = COALESCE(NEW.fitness_end_date, fitness_end_date),
                        pollution_validity = COALESCE(v_pol_val, pollution_validity),
                        auth_start_date = COALESCE(NEW.auth_start_date, auth_start_date),
                        auth_end_date = COALESCE(NEW.auth_end_date, auth_end_date),
                        authorization_certificate = COALESCE(NULLIF(NEW.authorization_certificate, ''), authorization_certificate),
                        insurance_validity = COALESCE(v_ins_val, insurance_validity),
                        insurance_start_date = COALESCE(v_ins_start, insurance_start_date),
                        insurance_broker = COALESCE(NULLIF(NEW.insurance_broker, ''), insurance_broker),
                        insurance_underwriter = COALESCE(NULLIF(NEW.insurance_underwriter, ''), insurance_underwriter),
                        insurance_idv = COALESCE(NULLIF(NEW.insurance_idv, ''), insurance_idv),
                        insurance_mapping = COALESCE(NULLIF(NEW.insurance_mapping, ''), insurance_mapping),
                        cover_engine_protect = COALESCE(NEW.cover_engine_protect, cover_engine_protect),
                        cover_consumables = COALESCE(NEW.cover_consumables, cover_consumables),
                        cover_zero_dep = COALESCE(NEW.cover_zero_dep, cover_zero_dep),
                        cover_rsa = COALESCE(NEW.cover_rsa, cover_rsa),
                        kms_reading = COALESCE(NULLIF(REGEXP_REPLACE(NEW.kms_reading, '[^0-9.]', '', 'g'), '')::NUMERIC, kms_reading),
                        tracking_device_vendor = COALESCE(NULLIF(NEW.tracking_device_vendor, ''), tracking_device_vendor),
                        tracking_device_type = COALESCE(NULLIF(NEW.tracking_device_type, ''), tracking_device_type),
                        fast_tag_number = COALESCE(NULLIF(NEW.fast_tag_number, ''), fast_tag_number),
                        fast_tag_vendor = COALESCE(NULLIF(NEW.fast_tag_vendor, ''), fast_tag_vendor),
                        key_quantity = COALESCE(NEW.key_quantity::TEXT, key_quantity),
                        jack = COALESCE(NULLIF(NEW.jack, ''), jack),
                        jack_rod = COALESCE(NULLIF(NEW.jack_rod, ''), jack_rod),
                        spanner = COALESCE(NULLIF(NEW.spanner, ''), spanner),
                        parking_triangle = COALESCE(NULLIF(NEW.parking_triangle, ''), parking_triangle),
                        fire_extinguishers = COALESCE(NULLIF(NEW.fire_extinguishers, ''), fire_extinguishers),
                        seat_cover = COALESCE(NULLIF(NEW.seat_cover, ''), seat_cover),
                        floor_carpet = COALESCE(NULLIF(NEW.floor_carpet, ''), floor_carpet),
                        cng_installed = COALESCE(NULLIF(NEW.cng_installed, ''), cng_installed),
                        cng_plate = COALESCE(NULLIF(NEW.cng_plate, ''), cng_plate),
                        cng_tank_number = COALESCE(NULLIF(NEW.cng_tank_number, ''), cng_tank_number),
                        cng_installation_date = COALESCE(v_cng_date, cng_installation_date),
                        rc_document = COALESCE(NULLIF(NEW.rc_document, ''), rc_document),
                        insurance_document = COALESCE(NULLIF(NEW.insurance_document, ''), insurance_document),
                        authorization_certificate_doc = COALESCE(NULLIF(NEW.authorization_certificate_doc, ''), authorization_certificate_doc),
                        rto_tax_receipt = COALESCE(NULLIF(NEW.rto_tax_receipt, ''), rto_tax_receipt),
                        image_front = COALESCE(NULLIF(NEW.image_front, ''), image_front),
                        image_lh = COALESCE(NULLIF(NEW.image_lh, ''), image_lh),
                        image_back = COALESCE(NULLIF(NEW.image_back, ''), image_back),
                        image_rh = COALESCE(NULLIF(NEW.image_rh, ''), image_rh),
                        engine_chasis_no_img = COALESCE(NULLIF(NEW.engine_chasis_no_img, ''), engine_chasis_no_img),
                        battery_sl_no_img = COALESCE(NULLIF(NEW.battery_sl_no_img, ''), battery_sl_no_img),
                        engine_compartment_img = COALESCE(NULLIF(NEW.engine_compartment_img, ''), engine_compartment_img),
                        fast_tag_img = COALESCE(NULLIF(NEW.fast_tag_img, ''), fast_tag_img),
                        music_system_img = COALESCE(NULLIF(NEW.music_system_img, ''), music_system_img),
                        rh_fr_tyre_img = COALESCE(NULLIF(NEW.rh_fr_tyre_img, ''), rh_fr_tyre_img),
                        lh_fr_tyre_img = COALESCE(NULLIF(NEW.lh_fr_tyre_img, ''), lh_fr_tyre_img),
                        rh_rear_tyre_img = COALESCE(NULLIF(NEW.rh_rear_tyre_img, ''), rh_rear_tyre_img),
                        lh_rear_tyre_img = COALESCE(NULLIF(NEW.lh_rear_tyre_img, ''), lh_rear_tyre_img),
                        spare_wheel_img = COALESCE(NULLIF(NEW.spare_wheel_img, ''), spare_wheel_img),
                        approval_status = COALESCE(NULLIF(NEW.approval_status, ''), approval_status),
                        current_approver_id = COALESCE(NEW.current_approver_id, current_approver_id),
                        approved_by = COALESCE(NEW.approved_by, approved_by),
                        approval_remarks = COALESCE(NULLIF(NEW.approval_remarks, ''), approval_remarks),
                        chassis_review_flag = (LENGTH(TRIM(COALESCE(NEW.chassis_number, ''))) != 17),
                        is_migrated = COALESCE(NEW.is_migrated, is_migrated),
                        created_by = COALESCE(NEW.created_by, created_by),
                        updated_by = COALESCE(NEW.updated_by, updated_by),
                        is_deleted = CASE WHEN is_deleted THEN is_deleted ELSE FALSE END,
                        deleted_at = CASE WHEN is_deleted THEN deleted_at ELSE NULL END,
                        updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
                    WHERE id = v_existing_id;
                ELSE
                    -- INSERT New Master Row from Portal
                    INSERT INTO public.core_vehicle_onboarding (
                        source_system, source_table, portal_vehicle_id,
                        registration_no, letzryd_unique_no, chassis_no, engine_no,
                        city, model, fuel_type, color, dealer_name, registered_owner_name,
                        hp_details, mfg_date, received_allocated, delivery_month,
                        registration_date, invoice_date, invoice_no,
                        rto_tax_validity, permit_validity, permit_start_date, permit_end_date, permit_type,
                        fitness_validity, fitness_start_date, fitness_end_date,
                        pollution_validity, auth_start_date, auth_end_date, authorization_certificate,
                        insurance_validity, insurance_start_date, insurance_broker, insurance_underwriter,
                        insurance_idv, insurance_mapping, cover_engine_protect, cover_consumables,
                        cover_zero_dep, cover_rsa,
                        kms_reading, tracking_device_vendor, tracking_device_type,
                        fast_tag_number, fast_tag_vendor,
                        key_quantity, jack, jack_rod, spanner, parking_triangle, fire_extinguishers,
                        seat_cover, floor_carpet, cng_installed, cng_plate, cng_tank_number, cng_installation_date,
                        rc_document, insurance_document, authorization_certificate_doc, rto_tax_receipt,
                        image_front, image_lh, image_back, image_rh,
                        engine_chasis_no_img, battery_sl_no_img, engine_compartment_img,
                        fast_tag_img, music_system_img,
                        rh_fr_tyre_img, lh_fr_tyre_img, rh_rear_tyre_img, lh_rear_tyre_img, spare_wheel_img,
                        approval_status, current_approver_id, approved_by, approval_remarks,
                        chassis_review_flag, is_migrated, created_by, updated_by,
                        is_deleted, created_at, updated_at
                    ) VALUES (
                        'PORTAL_FORM', 'portal_vehicle_onboarding', NEW.id,
                        v_clean_plate, LEFT(NEW.letzryd_unique_no, 100), LEFT(NEW.chassis_number, 100), LEFT(NEW.engine_number, 100),
                        v_clean_city, LEFT(NEW.model, 100), LEFT(COALESCE(NEW.fuel_type, 'CNG'), 50), LEFT(NEW.color, 100), LEFT(NEW.dealer_name, 255), LEFT(NEW.registered_owner_name, 255),
                        LEFT(NEW.hp_details, 100), LEFT(NEW.mfg_date, 50), LEFT(NEW.received_allocated, 100), LEFT(NEW.delivery_month, 100),
                        v_reg_date, NEW.invoice_date, LEFT(NEW.invoice_no, 100),
                        v_rto_tax, v_permit_val, NEW.permit_start_date, NEW.permit_end_date, LEFT(NEW.permit_type, 100),
                        v_fit_val, NEW.fitness_start_date, NEW.fitness_end_date,
                        v_pol_val, NEW.auth_start_date, NEW.auth_end_date, LEFT(NEW.authorization_certificate, 255),
                        v_ins_val, v_ins_start, LEFT(NEW.insurance_broker, 255), LEFT(NEW.insurance_underwriter, 255),
                        LEFT(NEW.insurance_idv, 100), LEFT(NEW.insurance_mapping, 255), COALESCE(NEW.cover_engine_protect, FALSE), COALESCE(NEW.cover_consumables, FALSE),
                        COALESCE(NEW.cover_zero_dep, FALSE), COALESCE(NEW.cover_rsa, FALSE),
                        NULLIF(REGEXP_REPLACE(NEW.kms_reading, '[^0-9.]', '', 'g'), '')::NUMERIC, LEFT(NEW.tracking_device_vendor, 100), LEFT(NEW.tracking_device_type, 100),
                        LEFT(NEW.fast_tag_number, 100), LEFT(NEW.fast_tag_vendor, 100),
                        LEFT(NEW.key_quantity::TEXT, 50), LEFT(NEW.jack, 50), LEFT(NEW.jack_rod, 50), LEFT(NEW.spanner, 50), LEFT(NEW.parking_triangle, 50), LEFT(NEW.fire_extinguishers, 50),
                        LEFT(NEW.seat_cover, 50), LEFT(NEW.floor_carpet, 50), LEFT(NEW.cng_installed, 50), LEFT(NEW.cng_plate, 100), LEFT(NEW.cng_tank_number, 100), v_cng_date,
                        NEW.rc_document, NEW.insurance_document, NEW.authorization_certificate_doc, NEW.rto_tax_receipt,
                        NEW.image_front, NEW.image_lh, NEW.image_back, NEW.image_rh,
                        NEW.engine_chasis_no_img, NEW.battery_sl_no_img, engine_compartment_img,
                        NEW.fast_tag_img, NEW.music_system_img,
                        NEW.rh_fr_tyre_img, NEW.lh_fr_tyre_img, NEW.rh_rear_tyre_img, NEW.lh_rear_tyre_img, NEW.spare_wheel_img,
                        LEFT(COALESCE(NEW.approval_status, 'APPROVED'), 50), NEW.current_approver_id, NEW.approved_by, NEW.approval_remarks,
                        (LENGTH(TRIM(COALESCE(NEW.chassis_number, ''))) != 17), COALESCE(NEW.is_migrated, FALSE), NEW.created_by, NEW.updated_by,
                        FALSE, (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'), (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
                    );
                END IF;
            END IF;
        END IF;
    EXCEPTION WHEN OTHERS THEN
        -- Fail-safe decoupling: Guarantees that source table portal_vehicle_onboarding operations NEVER fail
        RAISE WARNING 'core_vehicle_onboarding sync warning from portal: %', SQLERRM;
    END;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$function$
;

-- -----------------------------------------------------------------------------
-- FUNCTION: fn_sync_core_walkin_from_portal_existing (original: fn_sync_core_walkin_from_portal_existing)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.fn_sync_core_walkin_from_portal_existing()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
    DECLARE
        v_next_id BIGINT;
        v_clean_phone VARCHAR(20);
        v_clean_city VARCHAR(100);
        v_f_name TEXT;
        v_l_name TEXT;
        v_full_name TEXT;
        v_reason_cat VARCHAR(100);
        v_time_str VARCHAR(20);
        v_date DATE;
        v_ts TIMESTAMP WITHOUT TIME ZONE;
        v_exec_name VARCHAR(255);
        v_exec_email VARCHAR(255);
    BEGIN
        -- FAIL-SAFE BLOCK: Guarantees that source table portal_existing_walkins is NEVER impacted
        BEGIN
            IF TG_OP = 'DELETE' THEN
                UPDATE public.core_walkin
                SET is_deleted = TRUE,
                    deleted_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'),
                    updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
                WHERE portal_existing_walkin_id = OLD.id;
                RETURN OLD;
            END IF;

            v_clean_phone := RIGHT(REGEXP_REPLACE(COALESCE(NEW.person_number, ''), '\D', '', 'g'), 10);
            
            v_clean_city := CASE 
                WHEN LOWER(TRIM(COALESCE(NEW.city, ''))) IN ('bangalore', 'bengaluru', 'blr') THEN 'Bengaluru'
                WHEN LOWER(TRIM(COALESCE(NEW.city, ''))) IN ('hyderabad', 'hyd') THEN 'Hyderabad'
                WHEN LOWER(TRIM(COALESCE(NEW.city, ''))) IN ('mumbai', 'mum') THEN 'Mumbai'
                ELSE LEFT(INITCAP(TRIM(COALESCE(NEW.city, 'Unknown'))), 100)
            END;

            v_full_name := LEFT(TRIM(REGEXP_REPLACE(COALESCE(NEW.person_name, ''), '\s+', ' ', 'g')), 255);
            IF v_full_name = '' THEN
                v_full_name := LEFT(TRIM(CONCAT(COALESCE(NEW.first_name, ''), ' ', COALESCE(NEW.last_name, ''))), 255);
            END IF;
            IF v_full_name = '' OR v_full_name IS NULL THEN v_full_name := 'UNKNOWN'; END IF;
            
            v_f_name := LEFT(SPLIT_PART(v_full_name, ' ', 1), 100);
            v_l_name := NULLIF(LEFT(SUBSTRING(v_full_name FROM LENGTH(v_f_name) + 2), 100), '');

            v_reason_cat := CASE 
                WHEN NEW.visiting_reason ILIKE '%new joining%' OR NEW.visiting_reason ILIKE '%onboarding%' OR NEW.visiting_reason ILIKE '%re-joining%' OR NEW.visiting_reason ILIKE '%adding new vehicle%' THEN 'ONBOARDING'
                WHEN NEW.visiting_reason ILIKE '%enquiry%' OR NEW.visiting_reason ILIKE '%inquiry%' THEN 'ENQUIRY'
                WHEN NEW.visiting_reason ILIKE '%hisaab%' OR NEW.visiting_reason ILIKE '%payout%' OR NEW.visiting_reason ILIKE '%earnings%' THEN 'PAYOUT_HISAAB'
                WHEN NEW.visiting_reason ILIKE '%maintenance%' OR NEW.visiting_reason ILIKE '%tyre%' OR NEW.visiting_reason ILIKE '%swap%' OR NEW.visiting_reason ILIKE '%drop off%' THEN 'VEHICLE_MAINTENANCE'
                WHEN NEW.visiting_reason ILIKE '%meet%' OR NEW.visiting_reason ILIKE '%manager%' OR NEW.visiting_reason ILIKE '%dm%' THEN 'MEETING_COMPLAINT'
                ELSE 'OTHER'
            END;

            v_date := COALESCE(NEW.event_date, (NEW.created_at AT TIME ZONE 'Asia/Kolkata')::date, (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')::date);
            v_time_str := COALESCE(NEW.enquiry_time, TO_CHAR(NEW.created_at AT TIME ZONE 'Asia/Kolkata', 'HH24:MI'), TO_CHAR(CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata', 'HH24:MI'));

            BEGIN
                v_ts := (v_date::text || ' ' || v_time_str)::timestamp;
            EXCEPTION WHEN OTHERS THEN
                v_ts := COALESCE(NEW.created_at AT TIME ZONE 'Asia/Kolkata', (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'));
            END;

            SELECT 
                COALESCE(NULLIF(TRIM(CONCAT(e.first_name, ' ', e.last_name)), ''), pu.username, 'Executive'),
                COALESCE(pu.email, e.company_email, '')
            INTO v_exec_name, v_exec_email
            FROM public.portal_portal_users pu
            LEFT JOIN public.portal_employees e ON e.employee_id = pu.employee_id
            WHERE pu.portal_user_id = COALESCE(NEW.created_by, NEW.executive_id)
            LIMIT 1;

            IF TG_OP = 'INSERT' THEN
                PERFORM pg_advisory_xact_lock(777888999);
                SELECT COALESCE(MAX(id), 0) + 1 INTO v_next_id FROM public.core_walkin;

                INSERT INTO public.core_walkin (
                    id,
                    source_system, source_table, sheet_walkin_id, portal_new_walkin_id, portal_existing_walkin_id,
                    walkin_type, walkin_date, walkin_time, walkin_timestamp, city, operating_place,
                    full_name, first_name, last_name, phone_number, partner_role,
                    dl_number, aadhaar_number, dl_image_url, aadhaar_image_url,
                    visiting_reason, visiting_reason_category, joined_status, is_joined, joined_date, submission_status,
                    lead_channel, lead_channel_details, referred_by_name, referred_by_phone,
                    attending_executive, attending_executive_id, submitter_email, remarks, visit_notes,
                    sheet_row_number, is_deleted, deleted_at, created_at, updated_at
                ) VALUES (
                    v_next_id,
                    'PORTAL_EXISTING', 'portal_existing_walkins', NULL, NULL, NEW.id,
                    'EXISTING_PARTNER', v_date, v_time_str, v_ts, v_clean_city, NULL,
                    v_full_name, v_f_name, v_l_name, v_clean_phone, LEFT(COALESCE(NEW.partner_type, 'Driver'), 100),
                    NULL, NULL, NULL, NULL,
                    NEW.visiting_reason, v_reason_cat, 'Partner Visit', FALSE, NULL, LEFT(COALESCE(NEW.submission_status, 'Submitted'), 50),
                    NULL, NULL, NULL, NULL,
                    LEFT(COALESCE(v_exec_name, 'Executive'), 150), COALESCE(NEW.created_by, NEW.executive_id), LEFT(v_exec_email, 255), NULL, NEW.visit_notes,
                    NULL, FALSE, NULL, v_ts, COALESCE(NEW.updated_at, v_ts)
                );
                PERFORM setval('public.core_walkin_id_seq', v_next_id, true);

            ELSIF TG_OP = 'UPDATE' THEN
                UPDATE public.core_walkin SET
                    walkin_date = v_date,
                    walkin_time = v_time_str,
                    city = v_clean_city,
                    full_name = v_full_name,
                    first_name = v_f_name,
                    last_name = v_l_name,
                    phone_number = v_clean_phone,
                    partner_role = LEFT(COALESCE(NEW.partner_type, 'Driver'), 100),
                    visiting_reason = NEW.visiting_reason,
                    visiting_reason_category = v_reason_cat,
                    submission_status = LEFT(COALESCE(NEW.submission_status, 'Submitted'), 50),
                    attending_executive = LEFT(COALESCE(v_exec_name, attending_executive), 150),
                    attending_executive_id = COALESCE(NEW.created_by, NEW.executive_id),
                    submitter_email = LEFT(COALESCE(v_exec_email, submitter_email), 255),
                    visit_notes = NEW.visit_notes,
                    is_deleted = FALSE,
                    deleted_at = NULL,
                    updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
                WHERE portal_existing_walkin_id = NEW.id;

                IF NOT FOUND THEN
                    PERFORM pg_advisory_xact_lock(777888999);
                    SELECT COALESCE(MAX(id), 0) + 1 INTO v_next_id FROM public.core_walkin;
                    INSERT INTO public.core_walkin (
                        id,
                        source_system, source_table, sheet_walkin_id, portal_new_walkin_id, portal_existing_walkin_id,
                        walkin_type, walkin_date, walkin_time, walkin_timestamp, city, operating_place,
                        full_name, first_name, last_name, phone_number, partner_role,
                        dl_number, aadhaar_number, dl_image_url, aadhaar_image_url,
                        visiting_reason, visiting_reason_category, joined_status, is_joined, joined_date, submission_status,
                        lead_channel, lead_channel_details, referred_by_name, referred_by_phone,
                        attending_executive, attending_executive_id, submitter_email, remarks, visit_notes,
                        sheet_row_number, is_deleted, deleted_at, created_at, updated_at
                    ) VALUES (
                        v_next_id,
                        'PORTAL_EXISTING', 'portal_existing_walkins', NULL, NULL, NEW.id,
                        'EXISTING_PARTNER', v_date, v_time_str, v_ts, v_clean_city, NULL,
                        v_full_name, v_f_name, v_l_name, v_clean_phone, LEFT(COALESCE(NEW.partner_type, 'Driver'), 100),
                        NULL, NULL, NULL, NULL,
                        NEW.visiting_reason, v_reason_cat, 'Partner Visit', FALSE, NULL, LEFT(COALESCE(NEW.submission_status, 'Submitted'), 50),
                        NULL, NULL, NULL, NULL,
                        LEFT(COALESCE(v_exec_name, 'Executive'), 150), COALESCE(NEW.created_by, NEW.executive_id), LEFT(v_exec_email, 255), NULL, NEW.visit_notes,
                        NULL, FALSE, NULL, v_ts, COALESCE(NEW.updated_at, v_ts)
                    );
                    PERFORM setval('public.core_walkin_id_seq', v_next_id, true);
                END IF;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            -- Ensures source table operation NEVER fails even if core_walkin encounters an exception
            RAISE WARNING 'core_walkin sync warning for portal_existing: %', SQLERRM;
        END;
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        END IF;
        RETURN NEW;
    END;
    $function$
;

-- -----------------------------------------------------------------------------
-- FUNCTION: fn_sync_core_walkin_from_portal_new (original: fn_sync_core_walkin_from_portal_new)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.fn_sync_core_walkin_from_portal_new()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
    DECLARE
        v_next_id BIGINT;
        v_clean_phone VARCHAR(20);
        v_clean_city VARCHAR(100);
        v_f_name TEXT;
        v_l_name TEXT;
        v_full_name TEXT;
        v_reason_cat VARCHAR(100);
        v_is_joined BOOLEAN;
        v_time_str VARCHAR(20);
        v_date DATE;
        v_ts TIMESTAMP WITHOUT TIME ZONE;
        v_exec_name VARCHAR(255);
        v_exec_email VARCHAR(255);
    BEGIN
        -- FAIL-SAFE BLOCK: Guarantees that source table portal_new_walkins is NEVER impacted
        BEGIN
            IF TG_OP = 'DELETE' THEN
                UPDATE public.core_walkin
                SET is_deleted = TRUE,
                    deleted_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'),
                    updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
                WHERE portal_new_walkin_id = OLD.id;
                RETURN OLD;
            END IF;

            v_clean_phone := RIGHT(REGEXP_REPLACE(COALESCE(NEW.person_number, ''), '\D', '', 'g'), 10);
            
            v_clean_city := CASE 
                WHEN LOWER(TRIM(COALESCE(NEW.city, ''))) IN ('bangalore', 'bengaluru', 'blr') THEN 'Bengaluru'
                WHEN LOWER(TRIM(COALESCE(NEW.city, ''))) IN ('hyderabad', 'hyd') THEN 'Hyderabad'
                WHEN LOWER(TRIM(COALESCE(NEW.city, ''))) IN ('mumbai', 'mum') THEN 'Mumbai'
                ELSE LEFT(INITCAP(TRIM(COALESCE(NEW.city, 'Unknown'))), 100)
            END;

            v_full_name := LEFT(TRIM(REGEXP_REPLACE(COALESCE(NEW.person_name, ''), '\s+', ' ', 'g')), 255);
            IF v_full_name = '' THEN
                v_full_name := LEFT(TRIM(CONCAT(COALESCE(NEW.first_name, ''), ' ', COALESCE(NEW.last_name, ''))), 255);
            END IF;
            IF v_full_name = '' OR v_full_name IS NULL THEN v_full_name := 'UNKNOWN'; END IF;
            
            v_f_name := LEFT(SPLIT_PART(v_full_name, ' ', 1), 100);
            v_l_name := NULLIF(LEFT(SUBSTRING(v_full_name FROM LENGTH(v_f_name) + 2), 100), '');

            v_reason_cat := CASE 
                WHEN NEW.visiting_reason ILIKE '%new joining%' OR NEW.visiting_reason ILIKE '%onboarding%' OR NEW.visiting_reason ILIKE '%re-joining%' OR NEW.visiting_reason ILIKE '%adding new vehicle%' THEN 'ONBOARDING'
                WHEN NEW.visiting_reason ILIKE '%enquiry%' OR NEW.visiting_reason ILIKE '%inquiry%' THEN 'ENQUIRY'
                WHEN NEW.visiting_reason ILIKE '%hisaab%' OR NEW.visiting_reason ILIKE '%payout%' OR NEW.visiting_reason ILIKE '%earnings%' THEN 'PAYOUT_HISAAB'
                WHEN NEW.visiting_reason ILIKE '%maintenance%' OR NEW.visiting_reason ILIKE '%tyre%' OR NEW.visiting_reason ILIKE '%swap%' OR NEW.visiting_reason ILIKE '%drop off%' THEN 'VEHICLE_MAINTENANCE'
                WHEN NEW.visiting_reason ILIKE '%meet%' OR NEW.visiting_reason ILIKE '%manager%' OR NEW.visiting_reason ILIKE '%dm%' THEN 'MEETING_COMPLAINT'
                ELSE 'OTHER'
            END;

            v_is_joined := COALESCE(
                (NEW.joined_status ILIKE '%onboard%' OR NEW.joined_status ILIKE '%joined%' OR NEW.joined_status ILIKE '%active%')
                AND NEW.joined_status NOT ILIKE '%not%' AND NEW.joined_status NOT ILIKE '%reject%',
                FALSE
            );

            v_date := COALESCE(NEW.event_date, (NEW.created_at AT TIME ZONE 'Asia/Kolkata')::date, (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')::date);
            v_time_str := COALESCE(NEW.enquiry_time, TO_CHAR(NEW.created_at AT TIME ZONE 'Asia/Kolkata', 'HH24:MI'), TO_CHAR(CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata', 'HH24:MI'));

            BEGIN
                v_ts := (v_date::text || ' ' || v_time_str)::timestamp;
            EXCEPTION WHEN OTHERS THEN
                v_ts := COALESCE(NEW.created_at AT TIME ZONE 'Asia/Kolkata', (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'));
            END;

            SELECT 
                COALESCE(NULLIF(TRIM(CONCAT(e.first_name, ' ', e.last_name)), ''), pu.username, 'Executive'),
                COALESCE(pu.email, e.company_email, '')
            INTO v_exec_name, v_exec_email
            FROM public.portal_portal_users pu
            LEFT JOIN public.portal_employees e ON e.employee_id = pu.employee_id
            WHERE pu.portal_user_id = COALESCE(NEW.created_by, NEW.executive_id)
            LIMIT 1;

            IF TG_OP = 'INSERT' THEN
                PERFORM pg_advisory_xact_lock(777888999);
                SELECT COALESCE(MAX(id), 0) + 1 INTO v_next_id FROM public.core_walkin;

                INSERT INTO public.core_walkin (
                    id,
                    source_system, source_table, sheet_walkin_id, portal_new_walkin_id, portal_existing_walkin_id,
                    walkin_type, walkin_date, walkin_time, walkin_timestamp, city, operating_place,
                    full_name, first_name, last_name, phone_number, partner_role,
                    dl_number, aadhaar_number, dl_image_url, aadhaar_image_url,
                    visiting_reason, visiting_reason_category, joined_status, is_joined, joined_date, submission_status,
                    lead_channel, lead_channel_details, referred_by_name, referred_by_phone,
                    attending_executive, attending_executive_id, submitter_email, remarks, visit_notes,
                    sheet_row_number, is_deleted, deleted_at, created_at, updated_at
                ) VALUES (
                    v_next_id,
                    'PORTAL_NEW', 'portal_new_walkins', NULL, NEW.id, NULL,
                    'NEW_CANDIDATE', v_date, v_time_str, v_ts, v_clean_city, LEFT(NEW.operating_place, 150),
                    v_full_name, v_f_name, v_l_name, v_clean_phone, LEFT(COALESCE(NEW.interested_position, 'Driver'), 100),
                    LEFT(NEW.dl_number, 50), LEFT(NEW.aadhaar_number, 50), NEW.dl_image, NEW.aadhaar_image,
                    NEW.visiting_reason, v_reason_cat, NEW.joined_status, v_is_joined, NULL, LEFT(COALESCE(NEW.submission_status, 'Submitted'), 50),
                    LEFT(NEW.lead_channel, 100), LEFT(NEW.lead_channel_details, 255), LEFT(NEW.referred_by_name, 255), LEFT(NEW.referred_by_phone, 50),
                    LEFT(COALESCE(v_exec_name, 'Executive'), 150), COALESCE(NEW.created_by, NEW.executive_id), LEFT(v_exec_email, 255), NEW.remarks, NULL,
                    NULL, FALSE, NULL, v_ts, COALESCE(NEW.updated_at, v_ts)
                );
                PERFORM setval('public.core_walkin_id_seq', v_next_id, true);

            ELSIF TG_OP = 'UPDATE' THEN
                UPDATE public.core_walkin SET
                    walkin_date = v_date,
                    walkin_time = v_time_str,
                    city = v_clean_city,
                    operating_place = LEFT(NEW.operating_place, 150),
                    full_name = v_full_name,
                    first_name = v_f_name,
                    last_name = v_l_name,
                    phone_number = v_clean_phone,
                    partner_role = LEFT(COALESCE(NEW.interested_position, 'Driver'), 100),
                    dl_number = LEFT(NEW.dl_number, 50),
                    aadhaar_number = LEFT(NEW.aadhaar_number, 50),
                    dl_image_url = NEW.dl_image,
                    aadhaar_image_url = NEW.aadhaar_image,
                    visiting_reason = NEW.visiting_reason,
                    visiting_reason_category = v_reason_cat,
                    joined_status = NEW.joined_status,
                    is_joined = v_is_joined,
                    submission_status = LEFT(COALESCE(NEW.submission_status, 'Submitted'), 50),
                    lead_channel = LEFT(NEW.lead_channel, 100),
                    lead_channel_details = LEFT(NEW.lead_channel_details, 255),
                    referred_by_name = LEFT(NEW.referred_by_name, 255),
                    referred_by_phone = LEFT(NEW.referred_by_phone, 50),
                    attending_executive = LEFT(COALESCE(v_exec_name, attending_executive), 150),
                    attending_executive_id = COALESCE(NEW.created_by, NEW.executive_id),
                    submitter_email = LEFT(COALESCE(v_exec_email, submitter_email), 255),
                    remarks = NEW.remarks,
                    is_deleted = FALSE,
                    deleted_at = NULL,
                    updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
                WHERE portal_new_walkin_id = NEW.id;

                IF NOT FOUND THEN
                    PERFORM pg_advisory_xact_lock(777888999);
                    SELECT COALESCE(MAX(id), 0) + 1 INTO v_next_id FROM public.core_walkin;
                    INSERT INTO public.core_walkin (
                        id,
                        source_system, source_table, sheet_walkin_id, portal_new_walkin_id, portal_existing_walkin_id,
                        walkin_type, walkin_date, walkin_time, walkin_timestamp, city, operating_place,
                        full_name, first_name, last_name, phone_number, partner_role,
                        dl_number, aadhaar_number, dl_image_url, aadhaar_image_url,
                        visiting_reason, visiting_reason_category, joined_status, is_joined, joined_date, submission_status,
                        lead_channel, lead_channel_details, referred_by_name, referred_by_phone,
                        attending_executive, attending_executive_id, submitter_email, remarks, visit_notes,
                        sheet_row_number, is_deleted, deleted_at, created_at, updated_at
                    ) VALUES (
                        v_next_id,
                        'PORTAL_NEW', 'portal_new_walkins', NULL, NEW.id, NULL,
                        'NEW_CANDIDATE', v_date, v_time_str, v_ts, v_clean_city, LEFT(NEW.operating_place, 150),
                        v_full_name, v_f_name, v_l_name, v_clean_phone, LEFT(COALESCE(NEW.interested_position, 'Driver'), 100),
                        LEFT(NEW.dl_number, 50), LEFT(NEW.aadhaar_number, 50), NEW.dl_image, NEW.aadhaar_image,
                        NEW.visiting_reason, v_reason_cat, NEW.joined_status, v_is_joined, NULL, LEFT(COALESCE(NEW.submission_status, 'Submitted'), 50),
                        LEFT(NEW.lead_channel, 100), LEFT(NEW.lead_channel_details, 255), LEFT(NEW.referred_by_name, 255), LEFT(NEW.referred_by_phone, 50),
                        LEFT(COALESCE(v_exec_name, 'Executive'), 150), COALESCE(NEW.created_by, NEW.executive_id), LEFT(v_exec_email, 255), NEW.remarks, NULL,
                        NULL, FALSE, NULL, v_ts, COALESCE(NEW.updated_at, v_ts)
                    );
                    PERFORM setval('public.core_walkin_id_seq', v_next_id, true);
                END IF;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            -- Ensures source table operation NEVER fails even if core_walkin encounters an exception
            RAISE WARNING 'core_walkin sync warning for portal_new: %', SQLERRM;
        END;
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        END IF;
        RETURN NEW;
    END;
    $function$
;

-- -----------------------------------------------------------------------------
-- FUNCTION: fn_sync_hisaab_to_app_tables (original: fn_sync_hisaab_to_app_tables)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.fn_sync_hisaab_to_app_tables()
 RETURNS TABLE(drivers_synced integer, operators_synced integer, hisaabs_synced integer)
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_drivers_count INTEGER := 0;
    v_operators_count INTEGER := 0;
    v_hisaabs_count INTEGER := 0;
BEGIN
    -- -------------------------------------------------------------------------
    -- PHASE A: Sync Drivers from portal_driver_users (READ-ONLY) -> app_drivers
    -- -------------------------------------------------------------------------
    WITH inserted_drivers AS (
        INSERT INTO app_drivers (
            driver_id,
            operator_id,
            full_name,
            phone,
            driver_code,
            vehicle_reg_number,
            deposit_total_req,
            deposit_paid,
            deposit_pending,
            cumulative_owed,
            is_active,
            last_synced_at
        )
        SELECT 
            jdu.id                              AS driver_id,
            1                                   AS operator_id,
            COALESCE(jdu.name, 'Driver Partner') AS full_name,
            jdu.phone                           AS phone,
            COALESCE(jdu.driver_id, 'LR-DRV-' || jdu.id) AS driver_code,
            COALESCE(jdu.vehicle_number, 'UNASSIGNED')  AS vehicle_reg_number,
            COALESCE(jdu.deposit_total_required, 6000.00) AS deposit_total_req,
            COALESCE(jdu.deposit_paid_so_far, 5000.00)    AS deposit_paid,
            COALESCE(jdu.deposit_pending, 1000.00)        AS deposit_pending,
            COALESCE(jdu.cumulative_owed, 0.00)           AS cumulative_owed,
            COALESCE(jdu.is_active, TRUE)                 AS is_active,
            NOW()                               AS last_synced_at
        FROM portal_driver_users jdu
        WHERE jdu.phone IS NOT NULL AND jdu.phone != ''
        ON CONFLICT (phone) DO UPDATE SET
            full_name          = EXCLUDED.full_name,
            driver_code        = EXCLUDED.driver_code,
            vehicle_reg_number = CASE 
                                   WHEN EXCLUDED.vehicle_reg_number != 'UNASSIGNED' 
                                   THEN EXCLUDED.vehicle_reg_number 
                                   ELSE app_drivers.vehicle_reg_number 
                                 END,
            deposit_total_req  = COALESCE(app_drivers.deposit_total_req, EXCLUDED.deposit_total_req),
            deposit_paid        = COALESCE(app_drivers.deposit_paid, EXCLUDED.deposit_paid),
            deposit_pending     = COALESCE(app_drivers.deposit_pending, EXCLUDED.deposit_pending),
            cumulative_owed    = EXCLUDED.cumulative_owed,
            last_synced_at     = NOW()
        RETURNING 1
    )
    SELECT COUNT(*) INTO v_drivers_count FROM inserted_drivers;

    -- -------------------------------------------------------------------------
    -- PHASE B: Sync Operators from portal_operator_users (READ-ONLY) -> app_operators
    -- -------------------------------------------------------------------------
    WITH inserted_operators AS (
        INSERT INTO app_operators (
            operator_id,
            operator_code,
            phone,
            company_name,
            operator_type,
            deposit_total_req,
            deposit_paid,
            deposit_pending,
            is_active,
            last_synced_at
        )
        SELECT 
            jou.id                                  AS operator_id,
            COALESCE(jou.operator_code, 'OPR-' || jou.id) AS operator_code,
            jou.phone                               AS phone,
            COALESCE(jou.operator_name, 'Fleet Operator') AS company_name,
            COALESCE(jou.operator_type, 'Fleet Owner')    AS operator_type,
            COALESCE(jou.deposit_total_required, 25000.00) AS deposit_total_req,
            COALESCE(jou.deposit_paid_so_far, 20000.00)    AS deposit_paid,
            COALESCE(jou.deposit_pending, 5000.00)        AS deposit_pending,
            TRUE                                    AS is_active,
            NOW()                                   AS last_synced_at
        FROM portal_operator_users jou
        WHERE jou.phone IS NOT NULL AND jou.phone != ''
        ON CONFLICT (phone) DO UPDATE SET
            company_name       = EXCLUDED.company_name,
            operator_code      = EXCLUDED.operator_code,
            deposit_total_req  = COALESCE(app_operators.deposit_total_req, EXCLUDED.deposit_total_req),
            deposit_paid        = COALESCE(app_operators.deposit_paid, EXCLUDED.deposit_paid),
            deposit_pending     = COALESCE(app_operators.deposit_pending, EXCLUDED.deposit_pending),
            last_synced_at     = NOW()
        RETURNING 1
    )
    SELECT COUNT(*) INTO v_operators_count FROM inserted_operators;

    -- -------------------------------------------------------------------------
    -- PHASE C: Push Weekly Hisaab Summaries from portal_ola_weekly_summary -> app_hisaabs
    -- -------------------------------------------------------------------------
    WITH inserted_hisaabs AS (
        INSERT INTO app_hisaabs (
            allocation_id,
            hisaab_id,
            app_driver_id,
            app_operator_id,
            vehicle_id,
            hisaab_number,
            week_number,
            period_start,
            period_end,
            days_count,
            ola_trips,
            ola_revenue,
            ola_cash,
            ola_toll,
            ola_incentive,
            ola_subscription,
            ola_km,
            total_gross_earnings,
            status,
            last_synced_at,
            updated_at
        )
        SELECT 
            1                                                       AS allocation_id,
            MIN(jows.id)                                            AS hisaab_id,
            COALESCE(MIN(ad.app_driver_id), 1)                      AS app_driver_id,
            1                                                       AS app_operator_id,
            1                                                       AS vehicle_id,
            'HIS-2026-' || LPAD(EXTRACT(WEEK FROM MIN(jows.week_start))::TEXT, 3, '0') || '-' || jows.vehicle_number AS hisaab_number,
            EXTRACT(WEEK FROM MIN(jows.week_start))::SMALLINT       AS week_number,
            MIN(jows.week_start)                                    AS period_start,
            MAX(jows.week_end)                                      AS period_end,
            7                                                       AS days_count,
            SUM(COALESCE(jows.trips, 0))                            AS ola_trips,
            SUM(COALESCE(jows.revenue, 0.00))                       AS ola_revenue,
            SUM(COALESCE(jows.cash_collection, 0.00))               AS ola_cash,
            SUM(COALESCE(jows.toll, 0.00))                          AS ola_toll,
            SUM(COALESCE(jows.incentive, 0.00))                     AS ola_incentive,
            SUM(COALESCE(jows.subscription, 0.00))                  AS ola_subscription,
            SUM(COALESCE(jows.km, 0.00))                            AS ola_km,
            SUM(COALESCE(jows.revenue, 0.00))                       AS total_gross_earnings,
            'in_progress'                                           AS status,
            NOW()                                                   AS last_synced_at,
            NOW()                                                   AS updated_at
        FROM portal_ola_weekly_summary jows
        LEFT JOIN app_drivers ad ON LOWER(ad.vehicle_reg_number) = LOWER(jows.vehicle_number)
        GROUP BY jows.vehicle_number, EXTRACT(WEEK FROM jows.week_start)
        ON CONFLICT (hisaab_number) DO UPDATE SET
            ola_trips            = EXCLUDED.ola_trips,
            ola_revenue          = EXCLUDED.ola_revenue,
            ola_cash             = EXCLUDED.ola_cash,
            ola_toll             = EXCLUDED.ola_toll,
            ola_incentive        = EXCLUDED.ola_incentive,
            ola_subscription     = EXCLUDED.ola_subscription,
            ola_km               = EXCLUDED.ola_km,
            total_gross_earnings = EXCLUDED.total_gross_earnings,
            last_synced_at       = NOW(),
            updated_at           = NOW()
        RETURNING 1
    )
    SELECT COUNT(*) INTO v_hisaabs_count FROM inserted_hisaabs;

    -- Return sync statistics summary
    RETURN QUERY SELECT v_drivers_count, v_operators_count, v_hisaabs_count;
END;
$function$
;

-- -----------------------------------------------------------------------------
-- FUNCTION: fn_sync_portal_accidents_registry (original: fn_sync_july_accidents_registry)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.fn_sync_portal_accidents_registry()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_clean_veh VARCHAR(20);
    v_clean_city VARCHAR(10);
    v_accident_date DATE;
    v_photos TEXT;
    v_estimate NUMERIC(12,2);
    v_existing_id BIGINT;
    v_existing_source VARCHAR(50);
    v_existing_ref VARCHAR(100);
    v_next_id BIGINT;
BEGIN
    BEGIN
    IF TG_OP = 'DELETE' THEN
        UPDATE public.core_accidents
        SET is_deleted = TRUE, 
            deleted_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'), 
            updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
        WHERE source_reference_id = 'ACC-PORTAL-' || OLD.id::TEXT AND data_source = 'PORTAL_FORM';
        RETURN OLD;
    END IF;

    IF NEW.vehicle_number IS NOT NULL AND NEW.vehicle_number != '' THEN
        v_clean_veh := UPPER(REGEXP_REPLACE(NEW.vehicle_number, '[^A-Za-z0-9]', '', 'g'));
        v_clean_city := UPPER(TRIM(COALESCE(LEFT(NEW.city_name, 3), 'BLR')));
        
        -- Flexible Accident Date parsing
        v_accident_date := COALESCE(
            CASE 
                WHEN NEW.date_of_accident ~ '^\d{4}-\d{2}-\d{2}' THEN NEW.date_of_accident::DATE
                WHEN NEW.date_of_accident ~ '^\d{2}/\d{2}/\d{4}' THEN TO_DATE(NEW.date_of_accident, 'DD/MM/YYYY')
                ELSE NULL
            END,
            CURRENT_DATE
        );

        -- Combine all 4 inspection photo angles without dropping any
        v_photos := public.fn_combine_portal_photos(
            NEW.front_vehicle_photo, NEW.back_vehicle_photo, NEW.right_vehicle_photo, NEW.left_vehicle_photo
        );

        v_estimate := COALESCE(NULLIF(REGEXP_REPLACE(COALESCE(NEW.repair_cost, ''), '[^0-9.]', '', 'g'), '')::NUMERIC, 0.00);

        -- Transactional advisory lock for gapless zero-burn concurrency
        PERFORM pg_advisory_xact_lock(777222333);

        -- Cross-source deduplication: check matching vehicle + accident date or exact source reference
        SELECT id, data_source, source_reference_id
        INTO v_existing_id, v_existing_source, v_existing_ref
        FROM public.core_accidents
        WHERE (vehicle_number = v_clean_veh AND accident_date = v_accident_date)
           OR source_reference_id = 'ACC-PORTAL-' || NEW.id::TEXT
        ORDER BY CASE WHEN source_reference_id = 'ACC-PORTAL-' || NEW.id::TEXT THEN 1 ELSE 2 END
        LIMIT 1;

        IF v_existing_id IS NOT NULL THEN
            -- UPDATE and merge portal fields onto existing accident record
            UPDATE public.core_accidents
            SET
                city_code = COALESCE(core_accidents.city_code, v_clean_city),
                driver_name = COALESCE(core_accidents.driver_name, NEW.driver_name),
                driver_partner_id = COALESCE(core_accidents.driver_partner_id, NEW.driver_id),
                police_acknowledgement = CASE WHEN LOWER(COALESCE(NEW.fir_filed, '')) IN ('yes', 'true', '1') THEN TRUE ELSE core_accidents.police_acknowledgement END,
                estimate_amount = CASE WHEN core_accidents.estimate_amount > 0 THEN core_accidents.estimate_amount ELSE v_estimate END,
                accident_photos_url = CASE 
                    WHEN core_accidents.accident_photos_url IS NOT NULL AND v_photos IS NOT NULL 
                    THEN core_accidents.accident_photos_url || ',' || v_photos
                    ELSE COALESCE(core_accidents.accident_photos_url, v_photos)
                END,
                invoice_letter_url = COALESCE(core_accidents.invoice_letter_url, NEW.fir_document_copy),
                workshop_name = COALESCE(core_accidents.workshop_name, NEW.vendor_name),
                workshop_status = COALESCE(core_accidents.workshop_status, NEW.approval_status, NEW.vehicle_status),
                incident_remarks = COALESCE(core_accidents.incident_remarks, NEW.comments, NEW.accident_reason),
                data_source = CASE WHEN v_existing_source = 'GOOGLE_SHEET' THEN 'MERGED' ELSE 'PORTAL_FORM' END,
                source_reference_id = CASE 
                    WHEN v_existing_ref IS NOT NULL AND v_existing_ref NOT LIKE '%ACC-PORTAL-' || NEW.id::TEXT || '%' 
                    THEN v_existing_ref || ',ACC-PORTAL-' || NEW.id::TEXT 
                    ELSE COALESCE(v_existing_ref, 'ACC-PORTAL-' || NEW.id::TEXT) 
                END,
                is_deleted = FALSE,
                deleted_at = NULL,
                updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
            WHERE id = v_existing_id;
        ELSE
            -- INSERT new row with gapless ID
            SELECT COALESCE(MAX(id), 0) + 1 INTO v_next_id FROM public.core_accidents;

            INSERT INTO public.core_accidents (
                id,
                accident_id,
                vehicle_number,
                city_code,
                accident_date,
                driver_name,
                driver_partner_id,
                police_acknowledgement,
                estimate_amount,
                liability_amount,
                letzryd_payable_amount,
                total_invoice_amount,
                letzryd_share_amount,
                accident_photos_url,
                invoice_letter_url,
                workshop_name,
                workshop_status,
                mode_of_repair,
                type_of_payment,
                vehicle_rfd_date,
                incident_remarks,
                data_source,
                source_reference_id,
                is_deleted,
                created_at,
                updated_at
            ) VALUES (
                v_next_id,
                'ACC-PORTAL-' || NEW.id::TEXT,
                v_clean_veh,
                v_clean_city,
                v_accident_date,
                NEW.driver_name,
                NEW.driver_id,
                CASE WHEN LOWER(COALESCE(NEW.fir_filed, '')) IN ('yes', 'true', '1') THEN TRUE ELSE FALSE END,
                v_estimate,
                NULL,
                0.00,
                NULL,
                NULL,
                v_photos,
                NEW.fir_document_copy,
                NEW.vendor_name,
                COALESCE(NEW.approval_status, NEW.vehicle_status, 'Portal Logged'),
                'Accident',
                COALESCE(NEW.insurance_status, 'Insurance'),
                NULL,
                COALESCE(NEW.comments, NEW.accident_reason),
                'PORTAL_FORM',
                'ACC-PORTAL-' || NEW.id::TEXT,
                FALSE,
                (COALESCE(NEW.created_at, CURRENT_TIMESTAMP) AT TIME ZONE 'Asia/Kolkata'),
                (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
            );
        END IF;
    END IF;

    EXCEPTION WHEN OTHERS THEN
        RAISE WARNING 'fn_sync_portal_accidents_registry error shielded for id %: %', COALESCE(NEW.id, 0), SQLERRM;
    END;
        RETURN NEW;
END;
$function$
;

-- -----------------------------------------------------------------------------
-- FUNCTION: fn_sync_portal_form_onboarding (original: fn_sync_july_form_onboarding)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.fn_sync_portal_form_onboarding()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_clean_phone VARCHAR(20);
    v_existing_id BIGINT;
    v_existing_origin VARCHAR(50);
    v_next_id BIGINT;
    v_partner_id VARCHAR(50);
    v_parsed_dob DATE;
    v_parsed_dl_exp DATE;
    v_parsed_deposit NUMERIC(12, 2);
    v_clean_ref_phone VARCHAR(20);
BEGIN
    BEGIN
        IF TG_OP = 'DELETE' THEN
            UPDATE public.core_partner_onboarding
            SET is_deleted = CASE WHEN source_origin = 'PORTAL_FORM' THEN TRUE ELSE is_deleted END,
                source_origin = CASE WHEN source_origin = 'MERGED' THEN 'GOOGLE_SHEET' ELSE source_origin END,
                source_portal_form_id = CASE WHEN source_origin = 'MERGED' THEN NULL ELSE source_portal_form_id END,
                deleted_at = CASE WHEN source_origin = 'PORTAL_FORM' THEN (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata') ELSE deleted_at END,
                updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
            WHERE source_portal_form_id = OLD.id;
            RETURN OLD;
        END IF;

        IF NEW.phone_number IS NOT NULL THEN
            v_clean_phone := RIGHT(REGEXP_REPLACE(NEW.phone_number, '[^0-9]', '', 'g'), 10);
            IF LENGTH(v_clean_phone) = 10 THEN
                PERFORM pg_advisory_xact_lock(777111222);

                -- Determine canonical partner ID with IP for Operators
                IF NEW.driver_id IS NOT NULL AND NEW.driver_id ~ '^LETZ[A-Z]{3}IP[0-9]{10}$' THEN
                    v_partner_id := NEW.driver_id;
                ELSE
                    v_partner_id := public.fn_canonical_partner_id(NEW.city, v_clean_phone, NEW.candidate_role);
                END IF;

                v_parsed_dob := public.fn_safe_cast_date(NEW.dob);
                v_parsed_dl_exp := public.fn_safe_cast_date(NEW.dl_expiry_date);
                
                BEGIN
                    v_parsed_deposit := NULLIF(REGEXP_REPLACE(COALESCE(NEW.security_deposit, ''), '[^0-9.]', '', 'g'), '')::NUMERIC(12, 2);
                EXCEPTION WHEN OTHERS THEN
                    v_parsed_deposit := 0.00;
                END;

                v_clean_ref_phone := RIGHT(REGEXP_REPLACE(COALESCE(NEW.ref1_phone, ''), '[^0-9]', '', 'g'), 10);

                SELECT id, source_origin INTO v_existing_id, v_existing_origin
                FROM public.core_partner_onboarding
                WHERE phone_number = v_clean_phone;

                IF v_existing_id IS NOT NULL THEN
                    UPDATE public.core_partner_onboarding
                    SET
                        partner_id = v_partner_id,
                        driver_name = COALESCE(UPPER(TRIM(NEW.driver_name)), core_partner_onboarding.driver_name),
                        whatsapp_number = COALESCE(RIGHT(REGEXP_REPLACE(COALESCE(NEW.whatsapp_number, NEW.phone_number), '[^0-9]', '', 'g'), 10), core_partner_onboarding.whatsapp_number),
                        dob = COALESCE(v_parsed_dob, core_partner_onboarding.dob),
                        father_name = COALESCE(NEW.father_name, core_partner_onboarding.father_name),
                        city = COALESCE(NEW.city, core_partner_onboarding.city),
                        lead_source = COALESCE(NEW.lead_source, core_partner_onboarding.lead_source),
                        driver_plan = COALESCE(NEW.rental_model, core_partner_onboarding.driver_plan),
                        present_address = COALESCE(NEW.present_address, core_partner_onboarding.present_address),
                        permanent_address = COALESCE(NEW.permanent_address, core_partner_onboarding.permanent_address),
                        emergency_name = COALESCE(NEW.emergency_name, core_partner_onboarding.emergency_name),
                        emergency_phone = COALESCE(NEW.emergency_phone, core_partner_onboarding.emergency_phone),
                        emergency_relationship = COALESCE(NEW.emergency_relationship, core_partner_onboarding.emergency_relationship),
                        reference_name = COALESCE(NEW.ref1_name, core_partner_onboarding.reference_name),
                        reference_phone = COALESCE(NULLIF(v_clean_ref_phone, ''), core_partner_onboarding.reference_phone),
                        dl_number = COALESCE(NEW.dl_number, core_partner_onboarding.dl_number),
                        dl_expiry_date = COALESCE(v_parsed_dl_exp, core_partner_onboarding.dl_expiry_date),
                        pan_number = COALESCE(NEW.pan_number, core_partner_onboarding.pan_number),
                        aadhaar_number = COALESCE(REGEXP_REPLACE(NEW.aadhaar_number, '\s+', '', 'g'), core_partner_onboarding.aadhaar_number),
                        pan_aadhaar_linked = COALESCE(NEW.pan_aadhaar_linked, core_partner_onboarding.pan_aadhaar_linked),
                        bank_name = COALESCE(NEW.bank_name, core_partner_onboarding.bank_name),
                        account_name = COALESCE(NEW.account_name, core_partner_onboarding.account_name),
                        account_number = COALESCE(NEW.account_number, core_partner_onboarding.account_number),
                        ifsc_code = COALESCE(NEW.ifsc_code, core_partner_onboarding.ifsc_code),
                        upi_id = COALESCE(NEW.upi_id, core_partner_onboarding.upi_id),
                        security_deposit = CASE WHEN COALESCE(v_parsed_deposit, 0.00) > 0 THEN v_parsed_deposit ELSE core_partner_onboarding.security_deposit END,
                        selfie_photo = COALESCE(NEW.selfie_photo, core_partner_onboarding.selfie_photo),
                        dl_front = COALESCE(NEW.dl_front, core_partner_onboarding.dl_front),
                        dl_back = COALESCE(NEW.dl_back, core_partner_onboarding.dl_back),
                        aadhaar_card_front = COALESCE(NEW.aadhaar_card_front, NEW.aadhaar_card_photo, core_partner_onboarding.aadhaar_card_front),
                        aadhaar_card_back = COALESCE(NEW.aadhaar_card_back, core_partner_onboarding.aadhaar_card_back),
                        pan_card_photo = COALESCE(NEW.pan_card_photo, core_partner_onboarding.pan_card_photo),
                        local_address_proof = COALESCE(NEW.local_address_proof, core_partner_onboarding.local_address_proof),
                        cancelled_cheque_photo = COALESCE(NEW.cancelled_cheque_photo, core_partner_onboarding.cancelled_cheque_photo),
                        approval_status = COALESCE(NEW.approval_status, core_partner_onboarding.approval_status),
                        is_documents_verified = COALESCE(NEW.documents_verified, core_partner_onboarding.is_documents_verified),
                        is_spring_verified = COALESCE(NEW.is_spring_verified, core_partner_onboarding.is_spring_verified),
                        source_portal_form_id = NEW.id,
                        source_origin = CASE WHEN v_existing_origin IN ('GOOGLE_SHEET', 'MERGED') THEN 'MERGED' ELSE 'PORTAL_FORM' END,
                        is_deleted = FALSE,
                        deleted_at = NULL,
                        updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
                    WHERE id = v_existing_id;
                ELSE
                    SELECT COALESCE(MAX(id), 0) + 1 INTO v_next_id FROM public.core_partner_onboarding;

                    INSERT INTO public.core_partner_onboarding (
                        id, partner_id, driver_name, phone_number, whatsapp_number,
                        dob, father_name, city, onboarding_type, present_address, permanent_address, emergency_name, emergency_phone,
                        emergency_relationship, reference_name, reference_phone, dl_number, dl_expiry_date, lead_source, driver_plan,
                        pan_number, aadhaar_number, pan_aadhaar_linked, bank_name, account_name, account_number, ifsc_code,
                        upi_id, security_deposit, selfie_photo, dl_front, dl_back, aadhaar_card_front,
                        aadhaar_card_back, pan_card_photo, local_address_proof, cancelled_cheque_photo, approval_status,
                        is_documents_verified, is_spring_verified, source_origin, source_portal_form_id,
                        onboarding_timestamp, is_deleted, created_at, updated_at
                    ) VALUES (
                        v_next_id,
                        v_partner_id,
                        UPPER(TRIM(NEW.driver_name)),
                        v_clean_phone,
                        RIGHT(REGEXP_REPLACE(COALESCE(NEW.whatsapp_number, NEW.phone_number), '[^0-9]', '', 'g'), 10),
                        v_parsed_dob,
                        NEW.father_name,
                        COALESCE(NEW.city, 'Bengaluru'),
                        COALESCE(NEW.candidate_role, 'Individual'),
                        NEW.present_address,
                        NEW.permanent_address,
                        NEW.emergency_name,
                        NEW.emergency_phone,
                        NEW.emergency_relationship,
                        NEW.ref1_name,
                        NULLIF(v_clean_ref_phone, ''),
                        NEW.dl_number,
                        v_parsed_dl_exp,
                        NEW.lead_source,
                        NEW.rental_model,
                        NEW.pan_number,
                        REGEXP_REPLACE(NEW.aadhaar_number, '\s+', '', 'g'),
                        NEW.pan_aadhaar_linked,
                        NEW.bank_name,
                        NEW.account_name,
                        NEW.account_number,
                        NEW.ifsc_code,
                        NEW.upi_id,
                        COALESCE(v_parsed_deposit, 0.00),
                        NEW.selfie_photo,
                        NEW.dl_front,
                        NEW.dl_back,
                        COALESCE(NEW.aadhaar_card_front, NEW.aadhaar_card_photo),
                        NEW.aadhaar_card_back,
                        NEW.pan_card_photo,
                        NEW.local_address_proof,
                        NEW.cancelled_cheque_photo,
                        COALESCE(NEW.approval_status, 'Draft'),
                        COALESCE(NEW.documents_verified, FALSE),
                        COALESCE(NEW.is_spring_verified, FALSE),
                        'PORTAL_FORM',
                        NEW.id,
                        (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'),
                        FALSE,
                        (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'),
                        (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
                    );
                END IF;
                -- Keep sequence in sync with max id
                PERFORM setval('public.core_partner_onboarding_id_seq', (SELECT MAX(id) FROM public.core_partner_onboarding));
            END IF;
        END IF;
    EXCEPTION WHEN OTHERS THEN
        RAISE WARNING 'fn_sync_portal_form_onboarding error shielded for id %: %', COALESCE(NEW.id, 0), SQLERRM;
    END;
    RETURN NEW;
END;
$function$
;

-- -----------------------------------------------------------------------------
-- FUNCTION: fn_sync_portal_vehicle_dropoffs (original: fn_sync_july_vehicle_dropoffs)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.fn_sync_portal_vehicle_dropoffs()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_clean_veh VARCHAR(20);
    v_clean_city VARCHAR(50);
    v_clean_driver_id VARCHAR(50);
    v_driver_type VARCHAR(30);
    v_return_date DATE;
    v_pending_dues NUMERIC(12,2);
    v_damage_pen NUMERIC(12,2);
    v_total_liab NUMERIC(12,2);
    v_ref_id VARCHAR(50);
    v_existing_id BIGINT;
    v_existing_source VARCHAR(50);
    v_existing_ref VARCHAR(100);
    v_existing_sheet_id BIGINT;
    v_existing_driver_id VARCHAR(50);
    v_existing_return_type VARCHAR(50);
    v_existing_remarks TEXT;
    v_final_driver_id VARCHAR(50);
    v_combined_remarks TEXT;
    v_next_id BIGINT;
BEGIN
    IF TG_OP = 'DELETE' THEN
        UPDATE public.core_dropoffs
        SET is_deleted = TRUE, 
            deleted_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'), 
            updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
        WHERE portal_dropoff_id = OLD.id;
        RETURN OLD;
    END IF;

    IF NEW.vehicle_number IS NOT NULL AND NEW.vehicle_number != '' THEN
        v_clean_veh := UPPER(REGEXP_REPLACE(NEW.vehicle_number, '[^A-Za-z0-9]', '', 'g'));
        
        -- Regex Gatekeeper: Ignore dummy/test plates
        IF v_clean_veh !~ '^[A-Z]{2}[0-9]{1,2}[A-Z]{0,3}[0-9]{4}$' THEN
            RETURN NEW;
        END IF;

        v_clean_city := public.fn_normalize_dropoff_city(NEW.city_name, v_clean_veh);
        v_clean_driver_id := COALESCE(NULLIF(TRIM(NEW.driver_id), ''), 'UNKNOWN_DRIVER');
        v_driver_type := public.fn_resolve_driver_type(COALESCE(NEW.driver_type, 'Individual'), v_clean_driver_id);
        v_ref_id := NEW.id::TEXT;
        
        v_return_date := COALESCE(
            CASE 
                WHEN NEW.return_date::TEXT ~ '^\d{4}-\d{2}-\d{2}' THEN NEW.return_date::DATE
                WHEN NEW.return_date::TEXT ~ '^\d{2}/\d{2}/\d{4}' THEN TO_DATE(NEW.return_date::TEXT, 'DD/MM/YYYY')
                ELSE NULL
            END,
            CURRENT_DATE
        );

        v_pending_dues := COALESCE(NEW.pending_dues, 0.00);
        v_damage_pen := COALESCE(NEW.damage_penalty, 0.00);

        -- Transactional advisory lock
        PERFORM pg_advisory_xact_lock(777444555);

        -- Seek existing record
        SELECT id, data_source, source_reference_id, sheet_dropoff_id, driver_id, return_type, remarks
        INTO v_existing_id, v_existing_source, v_existing_ref, v_existing_sheet_id, v_existing_driver_id, v_existing_return_type, v_existing_remarks
        FROM public.core_dropoffs
        WHERE portal_dropoff_id = NEW.id
           OR (
               vehicle_number = v_clean_veh 
               AND return_date = v_return_date
               AND (
                   driver_id = v_clean_driver_id
                   OR driver_id = 'UNKNOWN_DRIVER'
                   OR v_clean_driver_id = 'UNKNOWN_DRIVER'
                   OR (driver_id LIKE '%IP%' AND v_clean_driver_id LIKE '%' || SUBSTRING(driver_id FROM 8) || '%')
                   OR (v_clean_driver_id LIKE '%IP%' AND driver_id LIKE '%' || SUBSTRING(v_clean_driver_id FROM 8) || '%')
               )
           )
        ORDER BY id DESC
        LIMIT 1;

        IF v_existing_id IS NOT NULL THEN
            -- Operator IP Priority Rule
            IF v_clean_driver_id LIKE '%IP%' THEN
                v_final_driver_id := v_clean_driver_id;
            ELSIF v_existing_driver_id LIKE '%IP%' THEN
                v_final_driver_id := v_existing_driver_id;
            ELSE
                v_final_driver_id := COALESCE(NULLIF(v_clean_driver_id, 'UNKNOWN_DRIVER'), v_existing_driver_id);
            END IF;

            -- Concatenate Remarks
            IF NULLIF(TRIM(COALESCE(NEW.remarks, '')), '') IS NOT NULL THEN
                IF v_existing_remarks IS NOT NULL AND v_existing_remarks NOT LIKE '%' || NEW.remarks || '%' THEN
                    v_combined_remarks := v_existing_remarks || ' | Portal: ' || NEW.remarks;
                ELSE
                    v_combined_remarks := COALESCE(v_existing_remarks, 'Portal: ' || NEW.remarks);
                END IF;
            ELSE
                v_combined_remarks := v_existing_remarks;
            END IF;

            v_total_liab := public.fn_calculate_dropoff_liability(
                (SELECT negative_balance FROM public.core_dropoffs WHERE id = v_existing_id),
                v_pending_dues,
                v_damage_pen
            );

            UPDATE public.core_dropoffs
            SET
                portal_dropoff_id = NEW.id,
                city = COALESCE(NULLIF(v_clean_city, ''), core_dropoffs.city),
                driver_name = COALESCE(NULLIF(NEW.driver_name, ''), core_dropoffs.driver_name),
                driver_id = v_final_driver_id,
                driver_type = COALESCE(NULLIF(v_driver_type, ''), core_dropoffs.driver_type),
                return_type = COALESCE(v_existing_return_type, NULLIF(NEW.return_type, ''), core_dropoffs.return_type),
                pending_dues = v_pending_dues,
                damage_penalty = v_damage_pen,
                total_liability = v_total_liab,
                remarks = v_combined_remarks,
                data_source = CASE WHEN v_existing_source = 'GOOGLE_SHEET' THEN 'MERGED' ELSE 'PORTAL_FORM' END,
                source_reference_id = CASE 
                    WHEN v_existing_sheet_id IS NOT NULL 
                    THEN v_existing_sheet_id::TEXT || ',' || v_ref_id
                    ELSE COALESCE(v_existing_ref, v_ref_id)
                END,
                is_deleted = FALSE,
                deleted_at = NULL,
                updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
            WHERE id = v_existing_id;
        ELSE
            SELECT COALESCE(MAX(id), 0) + 1 INTO v_next_id FROM public.core_dropoffs;
            v_total_liab := public.fn_calculate_dropoff_liability(0.00, v_pending_dues, v_damage_pen);

            INSERT INTO public.core_dropoffs (
                id,
                dropoff_id,
                sheet_dropoff_id,
                portal_dropoff_id,
                return_date,
                return_type,
                driver_id,
                driver_name,
                driver_type,
                vehicle_number,
                city,
                negative_balance,
                pending_dues,
                damage_penalty,
                total_liability,
                remarks,
                data_source,
                source_reference_id,
                is_deleted,
                created_at,
                updated_at
            ) VALUES (
                v_next_id,
                v_next_id::TEXT,
                NULL,
                NEW.id,
                v_return_date,
                COALESCE(NULLIF(NEW.return_type, ''), 'Attrition'),
                v_clean_driver_id,
                COALESCE(NULLIF(NEW.driver_name, ''), 'Unknown Driver'),
                v_driver_type,
                v_clean_veh,
                v_clean_city,
                0.00,
                v_pending_dues,
                v_damage_pen,
                v_total_liab,
                CASE WHEN NEW.remarks IS NOT NULL THEN 'Portal: ' || NEW.remarks ELSE NULL END,
                'PORTAL_FORM',
                v_ref_id,
                FALSE,
                (COALESCE(NEW.created_at, CURRENT_TIMESTAMP) AT TIME ZONE 'Asia/Kolkata'),
                (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
            );
        END IF;
    END IF;

    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'Shielding active: fn_sync_portal_vehicle_dropoffs failed to sync to core_dropoffs: %, SQLSTATE: %', SQLERRM, SQLSTATE;
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$function$
;

-- -----------------------------------------------------------------------------
-- FUNCTION: refresh_all_hisaab_statements (original: refresh_all_hisaab_statements)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.refresh_all_hisaab_statements()
 RETURNS void
 LANGUAGE plpgsql
AS $function$
BEGIN
    PERFORM refresh_portal_ola_weekly_summary();

    WITH aggregated_earnings AS (
        SELECT 
            'HIS-' || COALESCE(EXTRACT(YEAR FROM p.week_start)::text, '2026') || '-WK' || LPAD(COALESCE(EXTRACT(WEEK FROM p.week_start)::INT, 1)::text, 2, '0') || '-' || REPLACE(COALESCE(p.vehicle_number, 'UNKNOWN'), ' ', '') AS hisaab_number,
            p.vehicle_number,
            COALESCE(EXTRACT(WEEK FROM MIN(p.week_start))::INT, 1) AS week_number,
            MIN(p.week_start) AS week_start,
            MAX(p.week_end) AS week_end,
            SUM(p.ola_trips) AS ola_trips,
            SUM(p.ola_revenue) AS ola_revenue,
            SUM(p.ola_cash_collection) AS ola_cash_collection,
            SUM(p.ola_toll) AS ola_toll,
            SUM(p.ola_incentive) AS ola_incentive,
            SUM(p.ola_subscription) AS ola_subscription,
            SUM(p.ola_km) AS ola_km,
            SUM(p.ola_tds) AS ola_tds,
            SUM(p.uber_revenue) AS uber_revenue,
            SUM(p.uber_cash_collection) AS uber_cash_collection,
            SUM(p.rapido_revenue) AS rapido_revenue,
            SUM(p.rapido_cash_collection) AS rapido_cash_collection,
            SUM(p.ola_revenue + p.ola_toll + p.ola_incentive + p.uber_revenue + p.rapido_revenue) AS total_gross_earnings,
            SUM(p.ola_cash_collection + p.uber_cash_collection + p.rapido_cash_collection) AS total_cash_collected
        FROM view_weekly_platform_earnings p
        GROUP BY 1, 2
    )
    INSERT INTO portal_hisaab_weekly_statement (
        hisaab_number, vehicle_number, driver_name, week_number, week_start, week_end,
        ola_trips, ola_revenue, ola_cash_collection, ola_toll, ola_incentive, ola_subscription, ola_km,
        uber_revenue, uber_cash_collection, rapido_revenue, rapido_cash_collection,
        total_gross_earnings, total_cash_collected, net_weekly_rent, tds, challan, adjustment,
        current_week_os, to_collect, to_pay, letzryd_earning, updated_at
    )
    SELECT 
        a.hisaab_number,
        a.vehicle_number,
        COALESCE(d.name, alloc.driver_name, 'Driver') AS driver_name,
        a.week_number,
        a.week_start,
        a.week_end,
        a.ola_trips, a.ola_revenue, a.ola_cash_collection, a.ola_toll, a.ola_incentive, a.ola_subscription, a.ola_km,
        a.uber_revenue, a.uber_cash_collection, a.rapido_revenue, a.rapido_cash_collection,
        a.total_gross_earnings,
        a.total_cash_collected,
        7000.00 AS net_weekly_rent,
        a.ola_tds AS tds,
        COALESCE(c.total_challan, 0) AS challan,
        COALESCE(adj.total_adj, 0) AS adjustment,
        ((7000.00 + COALESCE(c.total_challan, 0) + COALESCE(adj.total_adj, 0) + a.total_cash_collected + a.ola_tds) - a.total_gross_earnings) AS current_week_os,
        GREATEST(0, ((7000.00 + COALESCE(c.total_challan, 0) + COALESCE(adj.total_adj, 0) + a.total_cash_collected + a.ola_tds) - a.total_gross_earnings)) AS to_collect,
        GREATEST(0, (a.total_gross_earnings - (7000.00 + COALESCE(c.total_challan, 0) + COALESCE(adj.total_adj, 0) + a.total_cash_collected + a.ola_tds))) AS to_pay,
        7000.00 AS letzryd_earning,
        NOW()
    FROM aggregated_earnings a
    LEFT JOIN portal_driver_users d ON d.vehicle_number = a.vehicle_number
    LEFT JOIN (
        SELECT DISTINCT ON (vehicle_number) vehicle_number, driver_name
        FROM copy_vehicle_allocation
        ORDER BY vehicle_number, id DESC
    ) alloc ON alloc.vehicle_number = a.vehicle_number
    LEFT JOIN (
        SELECT vehicle_number, SUM(challan_amount) AS total_challan
        FROM copy_traffic_challans
        GROUP BY vehicle_number
    ) c ON c.vehicle_number = a.vehicle_number
    LEFT JOIN (
        SELECT vehicle_number, SUM(CAST(enter_amount AS NUMERIC)) AS total_adj
        FROM copy_partner_adjustment
        WHERE status = 'Approved'
        GROUP BY vehicle_number
    ) adj ON adj.vehicle_number = a.vehicle_number
    ON CONFLICT (hisaab_number)
    DO UPDATE SET
        driver_name          = COALESCE(EXCLUDED.driver_name, portal_hisaab_weekly_statement.driver_name),
        vehicle_number       = EXCLUDED.vehicle_number,
        week_start           = EXCLUDED.week_start,
        week_end             = EXCLUDED.week_end,
        ola_trips            = EXCLUDED.ola_trips,
        ola_revenue          = EXCLUDED.ola_revenue,
        ola_cash_collection  = EXCLUDED.ola_cash_collection,
        ola_toll             = EXCLUDED.ola_toll,
        ola_incentive        = EXCLUDED.ola_incentive,
        ola_subscription     = EXCLUDED.ola_subscription,
        ola_km               = EXCLUDED.ola_km,
        uber_revenue         = EXCLUDED.uber_revenue,
        uber_cash_collection = EXCLUDED.uber_cash_collection,
        rapido_revenue       = EXCLUDED.rapido_revenue,
        rapido_cash_collection = EXCLUDED.rapido_cash_collection,
        total_gross_earnings = EXCLUDED.total_gross_earnings,
        total_cash_collected = EXCLUDED.total_cash_collected,
        challan              = EXCLUDED.challan,
        adjustment           = EXCLUDED.adjustment,
        current_week_os      = EXCLUDED.current_week_os,
        to_collect           = EXCLUDED.to_collect,
        to_pay               = EXCLUDED.to_pay,
        updated_at           = NOW();
END;
$function$
;

-- -----------------------------------------------------------------------------
-- FUNCTION: refresh_core_accidents (original: refresh_core_accidents)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.refresh_core_accidents()
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_inserted_count INTEGER := 0;
    r RECORD;
    v_clean_veh VARCHAR(20);
    v_clean_city VARCHAR(10);
    v_existing_id BIGINT;
    v_existing_source VARCHAR(50);
    v_existing_ref VARCHAR(100);
    v_next_id BIGINT;
    v_partner_id VARCHAR(50);
    v_photos TEXT;
    v_estimate NUMERIC(12,2);
    v_accident_date DATE;
BEGIN
    -- Acquire advisory lock
    PERFORM pg_advisory_xact_lock(777222333);

    -- Step 5.1: Ingest/Upsert from sheet_accidents
    FOR r IN (SELECT * FROM public.sheet_accidents ORDER BY submission_timestamp ASC, id ASC) LOOP
        v_clean_veh := UPPER(REGEXP_REPLACE(COALESCE(r.vehicle_number, ''), '[^A-Za-z0-9]', '', 'g'));
        v_clean_city := UPPER(TRIM(COALESCE(r.city_code, 'BLR')));
        
        IF v_clean_veh != '' THEN
            v_partner_id := r.driver_partner_id;
            IF v_partner_id IS NULL OR TRIM(v_partner_id) = '' THEN
                SELECT partner_id INTO v_partner_id
                FROM public.core_partner_onboarding
                WHERE phone_number = RIGHT(REGEXP_REPLACE(COALESCE(r.driver_partner_id, ''), '[^0-9]', '', 'g'), 10)
                LIMIT 1;
            END IF;

            SELECT id, data_source, source_reference_id
            INTO v_existing_id, v_existing_source, v_existing_ref
            FROM public.core_accidents
            WHERE (vehicle_number = v_clean_veh AND accident_date = r.accident_date)
               OR source_reference_id = 'ACC-SHT-' || r.id::TEXT
            LIMIT 1;

            IF v_existing_id IS NOT NULL THEN
                UPDATE public.core_accidents
                SET
                    driver_name = COALESCE(r.driver_name, core_accidents.driver_name),
                    driver_partner_id = COALESCE(v_partner_id, core_accidents.driver_partner_id),
                    police_acknowledgement = COALESCE(r.police_acknowledgement, core_accidents.police_acknowledgement),
                    estimate_amount = COALESCE(r.estimate_amount, core_accidents.estimate_amount),
                    liability_amount = COALESCE(r.liability_amount, core_accidents.liability_amount),
                    letzryd_payable_amount = COALESCE(r.letzryd_payable_amount, core_accidents.letzryd_payable_amount),
                    total_invoice_amount = COALESCE(r.total_invoice, core_accidents.total_invoice_amount),
                    letzryd_share_amount = COALESCE(r.letzryd_share, core_accidents.letzryd_share_amount),
                    accident_photos_url = COALESCE(r.accident_photos_link, core_accidents.accident_photos_url),
                    invoice_letter_url = COALESCE(r.invoice_letter_link, core_accidents.invoice_letter_url),
                    workshop_name = COALESCE(r.workshop_name, core_accidents.workshop_name),
                    workshop_status = COALESCE(r.workshop_status, core_accidents.workshop_status),
                    mode_of_repair = COALESCE(r.mode_of_repair, core_accidents.mode_of_repair),
                    type_of_payment = COALESCE(r.type_of_payment, core_accidents.type_of_payment),
                    vehicle_rfd_date = COALESCE(r.vehicle_rfd_date, core_accidents.vehicle_rfd_date),
                    incident_remarks = COALESCE(r.incident_remarks, core_accidents.incident_remarks),
                    data_source = CASE WHEN v_existing_source = 'PORTAL_FORM' THEN 'MERGED' ELSE 'GOOGLE_SHEET' END,
                    source_reference_id = CASE 
                        WHEN v_existing_ref IS NOT NULL AND v_existing_ref NOT LIKE '%ACC-SHT-' || r.id::TEXT || '%' 
                        THEN v_existing_ref || ',ACC-SHT-' || r.id::TEXT 
                        ELSE COALESCE(v_existing_ref, 'ACC-SHT-' || r.id::TEXT) 
                    END,
                    is_deleted = FALSE,
                    deleted_at = NULL,
                    updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
                WHERE id = v_existing_id;
            ELSE
                SELECT COALESCE(MAX(id), 0) + 1 INTO v_next_id FROM public.core_accidents;

                INSERT INTO public.core_accidents (
                    id,
                    accident_id,
                    vehicle_number,
                    city_code,
                    accident_date,
                    driver_name,
                    driver_partner_id,
                    police_acknowledgement,
                    estimate_amount,
                    liability_amount,
                    letzryd_payable_amount,
                    total_invoice_amount,
                    letzryd_share_amount,
                    accident_photos_url,
                    invoice_letter_url,
                    workshop_name,
                    workshop_status,
                    mode_of_repair,
                    type_of_payment,
                    vehicle_rfd_date,
                    incident_remarks,
                    data_source,
                    source_reference_id,
                    is_deleted,
                    created_at,
                    updated_at
                ) VALUES (
                    v_next_id,
                    'ACC-SHT-' || r.id::TEXT,
                    v_clean_veh,
                    v_clean_city,
                    r.accident_date,
                    r.driver_name,
                    v_partner_id,
                    r.police_acknowledgement,
                    r.estimate_amount,
                    r.liability_amount,
                    r.letzryd_payable_amount,
                    r.total_invoice,
                    r.letzryd_share,
                    r.accident_photos_link,
                    r.invoice_letter_link,
                    r.workshop_name,
                    COALESCE(r.workshop_status, 'Reported'),
                    r.mode_of_repair,
                    r.type_of_payment,
                    r.vehicle_rfd_date,
                    r.incident_remarks,
                    'GOOGLE_SHEET',
                    'ACC-SHT-' || r.id::TEXT,
                    FALSE,
                    (COALESCE(r.submission_timestamp, CURRENT_TIMESTAMP) AT TIME ZONE 'Asia/Kolkata'),
                    (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
                );
                v_inserted_count := v_inserted_count + 1;
            END IF;
        END IF;
    END LOOP;

    -- Step 5.2: Ingest/Upsert from portal_accidents_registry
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'portal_accidents_registry') THEN
        FOR r IN (SELECT * FROM public.portal_accidents_registry WHERE vehicle_number IS NOT NULL AND vehicle_number != '' ORDER BY created_at ASC, id ASC) LOOP
            v_clean_veh := UPPER(REGEXP_REPLACE(r.vehicle_number, '[^A-Za-z0-9]', '', 'g'));
            v_clean_city := UPPER(TRIM(COALESCE(LEFT(r.city_name, 3), 'BLR')));
            
            v_accident_date := COALESCE(
                CASE 
                    WHEN r.date_of_accident ~ '^\d{4}-\d{2}-\d{2}' THEN r.date_of_accident::DATE
                    WHEN r.date_of_accident ~ '^\d{2}/\d{2}/\d{4}' THEN TO_DATE(r.date_of_accident, 'DD/MM/YYYY')
                    ELSE NULL
                END,
                CURRENT_DATE
            );

            v_photos := public.fn_combine_portal_photos(
                r.front_vehicle_photo, r.back_vehicle_photo, r.right_vehicle_photo, r.left_vehicle_photo
            );

            v_estimate := COALESCE(NULLIF(REGEXP_REPLACE(COALESCE(r.repair_cost, ''), '[^0-9.]', '', 'g'), '')::NUMERIC, 0.00);

            SELECT id, data_source, source_reference_id
            INTO v_existing_id, v_existing_source, v_existing_ref
            FROM public.core_accidents
            WHERE (vehicle_number = v_clean_veh AND accident_date = v_accident_date)
               OR source_reference_id = 'ACC-PORTAL-' || r.id::TEXT
            LIMIT 1;

            IF v_existing_id IS NOT NULL THEN
                UPDATE public.core_accidents
                SET
                    driver_name = COALESCE(core_accidents.driver_name, r.driver_name),
                    driver_partner_id = COALESCE(core_accidents.driver_partner_id, r.driver_id),
                    police_acknowledgement = CASE WHEN LOWER(COALESCE(r.fir_filed, '')) IN ('yes', 'true', '1') THEN TRUE ELSE core_accidents.police_acknowledgement END,
                    estimate_amount = CASE WHEN core_accidents.estimate_amount > 0 THEN core_accidents.estimate_amount ELSE v_estimate END,
                    accident_photos_url = CASE 
                        WHEN core_accidents.accident_photos_url IS NOT NULL AND v_photos IS NOT NULL 
                        THEN core_accidents.accident_photos_url || ',' || v_photos
                        ELSE COALESCE(core_accidents.accident_photos_url, v_photos)
                    END,
                    invoice_letter_url = COALESCE(core_accidents.invoice_letter_url, r.fir_document_copy),
                    workshop_name = COALESCE(core_accidents.workshop_name, r.vendor_name),
                    workshop_status = COALESCE(core_accidents.workshop_status, r.approval_status, r.vehicle_status),
                    incident_remarks = COALESCE(core_accidents.incident_remarks, r.comments, r.accident_reason),
                    data_source = CASE WHEN v_existing_source = 'GOOGLE_SHEET' THEN 'MERGED' ELSE 'PORTAL_FORM' END,
                    source_reference_id = CASE 
                        WHEN v_existing_ref IS NOT NULL AND v_existing_ref NOT LIKE '%ACC-PORTAL-' || r.id::TEXT || '%' 
                        THEN v_existing_ref || ',ACC-PORTAL-' || r.id::TEXT 
                        ELSE COALESCE(v_existing_ref, 'ACC-PORTAL-' || r.id::TEXT) 
                    END,
                    is_deleted = FALSE,
                    deleted_at = NULL,
                    updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
                WHERE id = v_existing_id;
            ELSE
                SELECT COALESCE(MAX(id), 0) + 1 INTO v_next_id FROM public.core_accidents;

                INSERT INTO public.core_accidents (
                    id,
                    accident_id,
                    vehicle_number,
                    city_code,
                    accident_date,
                    driver_name,
                    driver_partner_id,
                    police_acknowledgement,
                    estimate_amount,
                    liability_amount,
                    letzryd_payable_amount,
                    total_invoice_amount,
                    letzryd_share_amount,
                    accident_photos_url,
                    invoice_letter_url,
                    workshop_name,
                    workshop_status,
                    mode_of_repair,
                    type_of_payment,
                    vehicle_rfd_date,
                    incident_remarks,
                    data_source,
                    source_reference_id,
                    is_deleted,
                    created_at,
                    updated_at
                ) VALUES (
                    v_next_id,
                    'ACC-PORTAL-' || r.id::TEXT,
                    v_clean_veh,
                    v_clean_city,
                    v_accident_date,
                    r.driver_name,
                    r.driver_id,
                    CASE WHEN LOWER(COALESCE(r.fir_filed, '')) IN ('yes', 'true', '1') THEN TRUE ELSE FALSE END,
                    v_estimate,
                    NULL,
                    0.00,
                    NULL,
                    NULL,
                    v_photos,
                    r.fir_document_copy,
                    r.vendor_name,
                    COALESCE(r.approval_status, r.vehicle_status, 'Portal Logged'),
                    'Accident',
                    COALESCE(r.insurance_status, 'Insurance'),
                    NULL,
                    COALESCE(r.comments, r.accident_reason),
                    'PORTAL_FORM',
                    'ACC-PORTAL-' || r.id::TEXT,
                    FALSE,
                    (COALESCE(r.created_at, CURRENT_TIMESTAMP) AT TIME ZONE 'Asia/Kolkata'),
                    (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
                );
                v_inserted_count := v_inserted_count + 1;
            END IF;
        END LOOP;
    END IF;

    RETURN v_inserted_count;
END;
$function$
;

-- -----------------------------------------------------------------------------
-- FUNCTION: refresh_core_adjustments (original: refresh_core_adjustments)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.refresh_core_adjustments()
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_total_synced INTEGER := 0;
    r RECORD;
    v_clean_phone TEXT;
    v_clean_veh TEXT;
    v_clean_city TEXT;
    v_partner_id TEXT;
    v_adj_date DATE;
    v_amount NUMERIC(12,2);
    v_status TEXT;
    v_existing_id BIGINT;
    v_next_id BIGINT;
BEGIN
    PERFORM pg_advisory_xact_lock(777333444);

    SELECT COALESCE(MAX(id), 0) INTO v_next_id FROM public.core_adjustments;

    -- 1. Sync all rows from sheet_adjustments (1-to-1 canonical)
    FOR r IN (SELECT * FROM public.sheet_adjustments ORDER BY id ASC) LOOP
        v_clean_phone := RIGHT(REGEXP_REPLACE(COALESCE(r.partner_phone, ''), '[^0-9]', '', 'g'), 10);
        v_clean_veh := UPPER(REGEXP_REPLACE(COALESCE(r.vehicle_number, ''), '[^A-Za-z0-9]', '', 'g'));
        v_clean_city := COALESCE(r.city_name, 'Bengaluru');
        v_partner_id := COALESCE(r.partner_code, public.fn_adj_canonical_partner_id(v_clean_city, v_clean_phone));
        v_adj_date := COALESCE(r.adjustment_date, r.submission_timestamp::DATE, CURRENT_DATE);
        v_status := public.fn_standardize_approval_status(COALESCE(r.final_status, r.first_level_status), 'Pending');

        SELECT id INTO v_existing_id
        FROM public.core_adjustments
        WHERE adjustment_id = 'ADJ-SHT-' || r.id::TEXT;

        IF v_existing_id IS NOT NULL THEN
            UPDATE public.core_adjustments
            SET
                partner_id = v_partner_id,
                partner_name = r.partner_name,
                partner_phone = v_clean_phone,
                partner_type = COALESCE(r.partner_type, 'Individual'),
                vehicle_number = r.vehicle_number,
                city_name = r.city_name,
                adjustment_type = r.adjustment_type,
                adjustment_nature = 'Monetary',
                adjustment_level = CASE WHEN LOWER(r.partner_type) = 'operator' THEN 'Operator' ELSE 'Driver' END,
                adjustment_date = v_adj_date,
                amount = r.amount,
                remittance_towards = r.remittance_towards,
                adjustment_related_to = r.adjustment_related_to,
                hisaab_number = r.hisaab_week_str,
                hisaab_week_number = r.hisaab_week_number,
                remarks = r.remarks,
                approval_status = v_status,
                first_level_approver = r.first_level_approver,
                final_level_approver = r.final_level_approver,
                photo_url = r.photo_url,
                data_source = 'GOOGLE_SHEET',
                source_reference_id = 'ADJ-SHT-' || r.id::TEXT,
                is_deleted = FALSE,
                deleted_at = NULL,
                updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
            WHERE id = v_existing_id;
        ELSE
            v_next_id := v_next_id + 1;

            INSERT INTO public.core_adjustments (
                id, adjustment_id, partner_id, partner_name, partner_phone, partner_type,
                vehicle_number, city_name, adjustment_type, adjustment_nature, adjustment_level,
                adjustment_date, amount, remittance_towards, adjustment_related_to,
                hisaab_number, hisaab_week_number, remarks, approval_status,
                first_level_approver, final_level_approver, photo_url,
                data_source, source_reference_id, is_deleted, created_at, updated_at
            ) VALUES (
                v_next_id,
                'ADJ-SHT-' || r.id::TEXT,
                v_partner_id,
                r.partner_name,
                v_clean_phone,
                COALESCE(r.partner_type, 'Individual'),
                r.vehicle_number,
                r.city_name,
                r.adjustment_type,
                'Monetary',
                CASE WHEN LOWER(r.partner_type) = 'operator' THEN 'Operator' ELSE 'Driver' END,
                v_adj_date,
                r.amount,
                r.remittance_towards,
                r.adjustment_related_to,
                r.hisaab_week_str,
                r.hisaab_week_number,
                r.remarks,
                v_status,
                r.first_level_approver,
                r.final_level_approver,
                r.photo_url,
                'GOOGLE_SHEET',
                'ADJ-SHT-' || r.id::TEXT,
                FALSE,
                (COALESCE(r.submission_timestamp, CURRENT_TIMESTAMP) AT TIME ZONE 'Asia/Kolkata'),
                (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
            );
        END IF;
        v_total_synced := v_total_synced + 1;
    END LOOP;

    -- 2. Sync all rows from portal_partner_adjustment
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'portal_partner_adjustment') THEN
        FOR r IN (SELECT * FROM public.portal_partner_adjustment ORDER BY id ASC) LOOP
            v_clean_phone := RIGHT(REGEXP_REPLACE(COALESCE(r.partner_number, ''), '[^0-9]', '', 'g'), 10);
            v_clean_veh := UPPER(REGEXP_REPLACE(COALESCE(r.vehicle_number, ''), '[^A-Za-z0-9]', '', 'g'));
            v_clean_city := COALESCE(r.city_name, 'Bengaluru');
            v_partner_id := COALESCE(r.driver_id, r.partner_code, public.fn_adj_canonical_partner_id(v_clean_city, v_clean_phone));
            
            v_adj_date := COALESCE(
                CASE 
                    WHEN r.adjustment_date ~ '^\d{4}-\d{2}-\d{2}' THEN r.adjustment_date::DATE
                    WHEN r.adjustment_date ~ '^\d{2}/\d{2}/\d{4}' THEN TO_DATE(r.adjustment_date, 'DD/MM/YYYY')
                    ELSE NULL
                END,
                r.created_at::DATE,
                CURRENT_DATE
            );

            v_amount := COALESCE(NULLIF(REGEXP_REPLACE(COALESCE(r.enter_amount, ''), '[^0-9.]', '', 'g'), '')::NUMERIC, 0.00);
            v_status := public.fn_standardize_approval_status(COALESCE(r.approval_status, r.status), 'Pending');

            SELECT id INTO v_existing_id
            FROM public.core_adjustments
            WHERE adjustment_id = 'ADJ-PORTAL-' || r.id::TEXT;

            IF v_existing_id IS NOT NULL THEN
                UPDATE public.core_adjustments
                SET
                    partner_id = v_partner_id,
                    partner_name = r.partner_name,
                    partner_phone = v_clean_phone,
                    partner_type = COALESCE(r.partner_type, 'Individual'),
                    vehicle_number = r.vehicle_number,
                    city_name = COALESCE(r.city_name, 'Bengaluru'),
                    adjustment_type = COALESCE(r.adjustment_type, 'Credit'),
                    adjustment_nature = COALESCE(r.adjustment_nature, 'Monetary'),
                    adjustment_level = COALESCE(r.adjustment_level, 'Driver'),
                    adjustment_date = v_adj_date,
                    amount = v_amount,
                    remittance_towards = r.remittance_towards,
                    adjustment_related_to = r.adjustment_related_to,
                    hisaab_number = r.hisaab_number,
                    contested_line_items = CASE WHEN r.contested_line_items IS NOT NULL AND r.contested_line_items != '' AND r.contested_line_items != 'nan' THEN r.contested_line_items::JSONB ELSE core_adjustments.contested_line_items END,
                    severity_level = r.severity_level,
                    cost_level = r.cost_level,
                    remarks = r.remarks,
                    approval_status = v_status,
                    first_level_approver = r.first_level_approval_by,
                    final_level_approver = r.final_level_approval_by,
                    current_approver_id = r.current_approver_id::TEXT,
                    approved_by = r.approved_by::TEXT,
                    photo_url = r.photo,
                    data_source = 'PORTAL_FORM',
                    source_reference_id = 'ADJ-PORTAL-' || r.id::TEXT,
                    is_deleted = FALSE,
                    deleted_at = NULL,
                    updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
                WHERE id = v_existing_id;
            ELSE
                v_next_id := v_next_id + 1;

                INSERT INTO public.core_adjustments (
                    id, adjustment_id, partner_id, partner_name, partner_phone, partner_type,
                    vehicle_number, city_name, adjustment_type, adjustment_nature, adjustment_level,
                    adjustment_date, amount, remittance_towards, adjustment_related_to,
                    hisaab_number, contested_line_items, severity_level, cost_level,
                    remarks, approval_status, first_level_approver, final_level_approver,
                    current_approver_id, approved_by, photo_url,
                    data_source, source_reference_id, is_deleted, created_at, updated_at
                ) VALUES (
                    v_next_id,
                    'ADJ-PORTAL-' || r.id::TEXT,
                    v_partner_id,
                    r.partner_name,
                    v_clean_phone,
                    COALESCE(r.partner_type, 'Individual'),
                    r.vehicle_number,
                    COALESCE(r.city_name, 'Bengaluru'),
                    COALESCE(r.adjustment_type, 'Credit'),
                    COALESCE(r.adjustment_nature, 'Monetary'),
                    COALESCE(r.adjustment_level, 'Driver'),
                    v_adj_date,
                    v_amount,
                    r.remittance_towards,
                    r.adjustment_related_to,
                    r.hisaab_number,
                    CASE WHEN r.contested_line_items IS NOT NULL AND r.contested_line_items != '' AND r.contested_line_items != 'nan' THEN r.contested_line_items::JSONB ELSE NULL END,
                    r.severity_level,
                    r.cost_level,
                    r.remarks,
                    v_status,
                    r.first_level_approval_by,
                    r.final_level_approval_by,
                    r.current_approver_id::TEXT,
                    r.approved_by::TEXT,
                    r.photo,
                    'PORTAL_FORM',
                    'ADJ-PORTAL-' || r.id::TEXT,
                    FALSE,
                    (COALESCE(r.created_at, CURRENT_TIMESTAMP) AT TIME ZONE 'Asia/Kolkata'),
                    (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
                );
            END IF;
            v_total_synced := v_total_synced + 1;
        END LOOP;
    END IF;

    -- 3. Reconcile soft-deleted records (mark as deleted if deleted from upstream source)
    UPDATE public.core_adjustments
    SET is_deleted = TRUE,
        deleted_at = COALESCE(deleted_at, CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'),
        updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
    WHERE data_source = 'GOOGLE_SHEET'
      AND is_deleted = FALSE
      AND NOT EXISTS (
          SELECT 1 FROM public.sheet_adjustments s 
          WHERE 'ADJ-SHT-' || s.id::TEXT = core_adjustments.adjustment_id
      );

    UPDATE public.core_adjustments
    SET is_deleted = TRUE,
        deleted_at = COALESCE(deleted_at, CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'),
        updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
    WHERE data_source = 'PORTAL_FORM'
      AND is_deleted = FALSE
      AND NOT EXISTS (
          SELECT 1 FROM public.portal_partner_adjustment p 
          WHERE 'ADJ-PORTAL-' || p.id::TEXT = core_adjustments.adjustment_id
      );

    PERFORM setval('public.core_adjustments_id_seq', COALESCE(v_next_id, 1), true);
    RETURN v_total_synced;
END;
$function$
;

-- -----------------------------------------------------------------------------
-- FUNCTION: refresh_core_dropoffs (original: refresh_core_dropoffs)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.refresh_core_dropoffs()
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
    r RECORD;
    p RECORD;
    v_clean_veh VARCHAR(20);
    v_clean_city VARCHAR(50);
    v_clean_driver_id VARCHAR(50);
    v_driver_type VARCHAR(30);
    v_neg_bal NUMERIC(12,2);
    v_total_liab NUMERIC(12,2);
    v_ref_id VARCHAR(50);
    v_next_id BIGINT;
    v_existing_id BIGINT;
    v_existing_source VARCHAR(50);
    v_existing_ref VARCHAR(100);
    v_existing_sheet_id BIGINT;
    v_existing_driver_id VARCHAR(50);
    v_existing_return_type VARCHAR(50);
    v_existing_remarks TEXT;
    v_final_driver_id VARCHAR(50);
    v_combined_remarks TEXT;
    v_inserted_count INTEGER := 0;
BEGIN
    PERFORM pg_advisory_xact_lock(777444555);

    -- Step A: Sync all Google Sheet records
    FOR r IN 
        SELECT * FROM public.sheet_dropoffs 
        ORDER BY dropoff_id ASC
    LOOP
        v_clean_veh := UPPER(REGEXP_REPLACE(COALESCE(r.vehicle_number, ''), '[^A-Za-z0-9]', '', 'g'));
        
        -- Skip invalid plates
        IF v_clean_veh !~ '^[A-Z]{2}[0-9]{1,2}[A-Z]{0,3}[0-9]{4}$' THEN
            CONTINUE;
        END IF;

        v_clean_city := public.fn_normalize_dropoff_city(r.city, v_clean_veh);
        v_clean_driver_id := COALESCE(NULLIF(TRIM(r.driver_id), ''), 'UNKNOWN_DRIVER');
        v_driver_type := public.fn_resolve_driver_type(r.driver_type, v_clean_driver_id);
        v_ref_id := r.dropoff_id::TEXT;

        IF r.negative_balance IS NOT NULL THEN
            v_neg_bal := -1.0 * ABS(r.negative_balance);
        ELSE
            v_neg_bal := 0.00;
        END IF;

        -- Seek existing record
        SELECT id, data_source, source_reference_id, driver_id
        INTO v_existing_id, v_existing_source, v_existing_ref, v_existing_driver_id
        FROM public.core_dropoffs
        WHERE sheet_dropoff_id = r.dropoff_id
           OR (
               vehicle_number = v_clean_veh 
               AND return_date = r.return_date
               AND (
                   driver_id = v_clean_driver_id
                   OR driver_id = 'UNKNOWN_DRIVER'
                   OR v_clean_driver_id = 'UNKNOWN_DRIVER'
                   OR (driver_id LIKE '%IP%' AND v_clean_driver_id LIKE '%' || SUBSTRING(driver_id FROM 8) || '%')
                   OR (v_clean_driver_id LIKE '%IP%' AND driver_id LIKE '%' || SUBSTRING(v_clean_driver_id FROM 8) || '%')
               )
           )
        ORDER BY id DESC
        LIMIT 1;

        IF v_existing_id IS NOT NULL THEN
            IF v_existing_driver_id LIKE '%IP%' AND v_clean_driver_id NOT LIKE '%IP%' THEN
                v_final_driver_id := v_existing_driver_id;
            ELSE
                v_final_driver_id := v_clean_driver_id;
            END IF;

            v_total_liab := public.fn_calculate_dropoff_liability(
                v_neg_bal,
                (SELECT pending_dues FROM public.core_dropoffs WHERE id = v_existing_id),
                (SELECT damage_penalty FROM public.core_dropoffs WHERE id = v_existing_id)
            );

            UPDATE public.core_dropoffs
            SET
                sheet_dropoff_id = r.dropoff_id,
                vehicle_number = v_clean_veh,
                city = v_clean_city,
                return_date = r.return_date,
                return_type = COALESCE(NULLIF(r.return_type, ''), core_dropoffs.return_type),
                driver_id = v_final_driver_id,
                driver_name = COALESCE(NULLIF(r.driver_name, ''), core_dropoffs.driver_name),
                driver_type = v_driver_type,
                negative_balance = v_neg_bal,
                total_liability = v_total_liab,
                data_source = CASE WHEN v_existing_source = 'PORTAL_FORM' THEN 'MERGED' ELSE core_dropoffs.data_source END,
                source_reference_id = COALESCE(v_ref_id, core_dropoffs.source_reference_id),
                is_deleted = FALSE,
                deleted_at = NULL,
                updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
            WHERE id = v_existing_id;
        ELSE
            SELECT COALESCE(MAX(id), 0) + 1 INTO v_next_id FROM public.core_dropoffs;
            v_total_liab := public.fn_calculate_dropoff_liability(v_neg_bal, 0.00, 0.00);

            INSERT INTO public.core_dropoffs (
                id,
                dropoff_id,
                sheet_dropoff_id,
                portal_dropoff_id,
                return_date,
                return_type,
                driver_id,
                driver_name,
                driver_type,
                vehicle_number,
                city,
                negative_balance,
                pending_dues,
                damage_penalty,
                total_liability,
                remarks,
                data_source,
                source_reference_id,
                is_deleted,
                created_at,
                updated_at
            ) VALUES (
                v_next_id,
                v_next_id::TEXT,
                r.dropoff_id,
                NULL,
                r.return_date,
                COALESCE(NULLIF(r.return_type, ''), 'Attrition'),
                v_clean_driver_id,
                COALESCE(NULLIF(r.driver_name, ''), 'Unknown Driver'),
                v_driver_type,
                v_clean_veh,
                v_clean_city,
                v_neg_bal,
                0.00,
                0.00,
                v_total_liab,
                NULL,
                'GOOGLE_SHEET',
                v_ref_id,
                FALSE,
                (COALESCE(r.created_at, CURRENT_TIMESTAMP) AT TIME ZONE 'Asia/Kolkata'),
                (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
            );
            v_inserted_count := v_inserted_count + 1;
        END IF;
    END LOOP;

    -- Step B: Merge Web Portal records
    FOR p IN 
        SELECT * FROM public.portal_vehicle_dropoffs 
        ORDER BY id ASC
    LOOP
        v_clean_veh := UPPER(REGEXP_REPLACE(COALESCE(p.vehicle_number, ''), '[^A-Za-z0-9]', '', 'g'));
        
        -- Skip invalid plates
        IF v_clean_veh !~ '^[A-Z]{2}[0-9]{1,2}[A-Z]{0,3}[0-9]{4}$' THEN
            CONTINUE;
        END IF;

        v_clean_city := public.fn_normalize_dropoff_city(p.city_name, v_clean_veh);
        v_clean_driver_id := COALESCE(NULLIF(TRIM(p.driver_id), ''), 'UNKNOWN_DRIVER');
        v_driver_type := public.fn_resolve_driver_type(COALESCE(p.driver_type, 'Individual'), v_clean_driver_id);

        -- Seek existing record
        SELECT id, data_source, source_reference_id, sheet_dropoff_id, driver_id, return_type, remarks
        INTO v_existing_id, v_existing_source, v_existing_ref, v_existing_sheet_id, v_existing_driver_id, v_existing_return_type, v_existing_remarks
        FROM public.core_dropoffs
        WHERE portal_dropoff_id = p.id
           OR (
               vehicle_number = v_clean_veh 
               AND return_date = p.return_date
               AND (
                   driver_id = v_clean_driver_id
                   OR driver_id = 'UNKNOWN_DRIVER'
                   OR v_clean_driver_id = 'UNKNOWN_DRIVER'
                   OR (driver_id LIKE '%IP%' AND v_clean_driver_id LIKE '%' || SUBSTRING(driver_id FROM 8) || '%')
                   OR (v_clean_driver_id LIKE '%IP%' AND driver_id LIKE '%' || SUBSTRING(v_clean_driver_id FROM 8) || '%')
               )
           )
        ORDER BY id DESC
        LIMIT 1;

        IF v_existing_id IS NOT NULL THEN
            IF v_clean_driver_id LIKE '%IP%' THEN
                v_final_driver_id := v_clean_driver_id;
            ELSIF v_existing_driver_id LIKE '%IP%' THEN
                v_final_driver_id := v_existing_driver_id;
            ELSE
                v_final_driver_id := COALESCE(NULLIF(v_clean_driver_id, 'UNKNOWN_DRIVER'), v_existing_driver_id);
            END IF;

            IF NULLIF(TRIM(COALESCE(p.remarks, '')), '') IS NOT NULL THEN
                IF v_existing_remarks IS NOT NULL AND v_existing_remarks NOT LIKE '%' || p.remarks || '%' THEN
                    v_combined_remarks := v_existing_remarks || ' | Portal: ' || p.remarks;
                ELSE
                    v_combined_remarks := COALESCE(v_existing_remarks, 'Portal: ' || p.remarks);
                END IF;
            ELSE
                v_combined_remarks := v_existing_remarks;
            END IF;

            v_total_liab := public.fn_calculate_dropoff_liability(
                (SELECT negative_balance FROM public.core_dropoffs WHERE id = v_existing_id),
                COALESCE(p.pending_dues, 0.00),
                COALESCE(p.damage_penalty, 0.00)
            );

            v_ref_id := p.id::TEXT;

            UPDATE public.core_dropoffs
            SET
                portal_dropoff_id = p.id,
                city = COALESCE(NULLIF(v_clean_city, ''), core_dropoffs.city),
                driver_name = COALESCE(NULLIF(p.driver_name, ''), core_dropoffs.driver_name),
                driver_id = v_final_driver_id,
                driver_type = COALESCE(NULLIF(v_driver_type, ''), core_dropoffs.driver_type),
                pending_dues = COALESCE(p.pending_dues, 0.00),
                damage_penalty = COALESCE(p.damage_penalty, 0.00),
                total_liability = v_total_liab,
                remarks = v_combined_remarks,
                data_source = CASE WHEN v_existing_source = 'GOOGLE_SHEET' THEN 'MERGED' ELSE 'PORTAL_FORM' END,
                source_reference_id = CASE 
                    WHEN v_existing_sheet_id IS NOT NULL 
                    THEN v_existing_sheet_id::TEXT || ',' || v_ref_id
                    ELSE COALESCE(v_existing_ref, v_ref_id)
                END,
                is_deleted = FALSE,
                deleted_at = NULL,
                updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
            WHERE id = v_existing_id;
        ELSE
            SELECT COALESCE(MAX(id), 0) + 1 INTO v_next_id FROM public.core_dropoffs;
            v_total_liab := public.fn_calculate_dropoff_liability(0.00, COALESCE(p.pending_dues, 0.00), COALESCE(p.damage_penalty, 0.00));

            INSERT INTO public.core_dropoffs (
                id,
                dropoff_id,
                sheet_dropoff_id,
                portal_dropoff_id,
                return_date,
                return_type,
                driver_id,
                driver_name,
                driver_type,
                vehicle_number,
                city,
                negative_balance,
                pending_dues,
                damage_penalty,
                total_liability,
                remarks,
                data_source,
                source_reference_id,
                is_deleted,
                created_at,
                updated_at
            ) VALUES (
                v_next_id,
                v_next_id::TEXT,
                NULL,
                p.id,
                p.return_date,
                COALESCE(NULLIF(p.return_type, ''), 'Attrition'),
                v_clean_driver_id,
                COALESCE(NULLIF(p.driver_name, ''), 'Unknown Driver'),
                v_driver_type,
                v_clean_veh,
                v_clean_city,
                0.00,
                COALESCE(p.pending_dues, 0.00),
                COALESCE(p.damage_penalty, 0.00),
                v_total_liab,
                CASE WHEN p.remarks IS NOT NULL THEN 'Portal: ' || p.remarks ELSE NULL END,
                'PORTAL_FORM',
                p.id::TEXT,
                FALSE,
                (COALESCE(p.created_at, CURRENT_TIMESTAMP) AT TIME ZONE 'Asia/Kolkata'),
                (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
            );
            v_inserted_count := v_inserted_count + 1;
        END IF;
    END LOOP;

    -- Step C (Phase 3): Redundant Duplicate Purging & Deduplication
    -- C1: Soft-delete corrupted 'New Allocation' records
    UPDATE public.core_dropoffs
    SET is_deleted = TRUE,
        deleted_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'),
        updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
    WHERE driver_name ILIKE '%New Allocation%'
      AND is_deleted = FALSE;

    -- C2: Soft-delete duplicate sheet_dropoff_id pairs (keep latest ID)
    WITH dup_sheet AS (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY sheet_dropoff_id
                   ORDER BY id DESC
               ) as rn
        FROM public.core_dropoffs
        WHERE is_deleted = FALSE AND sheet_dropoff_id IS NOT NULL
    )
    UPDATE public.core_dropoffs c
    SET is_deleted = TRUE,
        deleted_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'),
        updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
    FROM dup_sheet d
    WHERE c.id = d.id AND d.rn > 1;

    -- C3: Soft-delete same-driver duplicate event rows (prefer MERGED > PORTAL > SHEET, then latest ID)
    WITH dup_event AS (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY vehicle_number, return_date, driver_id
                   ORDER BY CASE WHEN data_source = 'MERGED' THEN 1 
                                 WHEN data_source = 'PORTAL_FORM' THEN 2 
                                 ELSE 3 END,
                            id DESC
               ) as rn
        FROM public.core_dropoffs
        WHERE is_deleted = FALSE
    )
    UPDATE public.core_dropoffs c
    SET is_deleted = TRUE,
        deleted_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'),
        updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
    FROM dup_event d
    WHERE c.id = d.id AND d.rn > 1;

    RETURN v_inserted_count;
END;
$function$
;

-- -----------------------------------------------------------------------------
-- PROCEDURE: refresh_core_maintenance (original: refresh_core_maintenance)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE public.refresh_core_maintenance()
 LANGUAGE plpgsql
AS $procedure$
DECLARE
    v_in_row RECORD;
    v_out_row RECORD;
    v_sheet_row RECORD;
    v_clean_veh VARCHAR(20);
    v_clean_city VARCHAR(20);
    v_start_date DATE;
    v_end_date DATE;
    v_status VARCHAR(30);
    v_workshop VARCHAR(150);
    v_reason TEXT;
    v_job_card VARCHAR(100);
    v_est_cost NUMERIC(12, 2);
    v_act_cost NUMERIC(12, 2);
    v_portal_count INTEGER := 0;
    v_sheet_count INTEGER := 0;
BEGIN
    -- Transactional Advisory Lock to guarantee single-runner execution
    PERFORM pg_advisory_xact_lock(777666555);

    RAISE NOTICE 'Starting full reconciliation for public.core_maintenance...';

    -- =========================================================================
    -- STEP 1: Ingest & Pair Web Portal Inward and Outward Records
    -- =========================================================================
    FOR v_in_row IN (
        SELECT mi.*
        FROM public.portal_maintenance_in mi
        ORDER BY mi.id ASC
    ) LOOP
        v_clean_veh := public.fn_clean_maintenance_vehicle(v_in_row.vehicle_number);
        v_clean_city := public.fn_clean_maintenance_city(v_in_row.city_name, v_clean_veh);
        v_start_date := COALESCE(
            public.fn_parse_maintenance_date(v_in_row.vehicle_in_date_time),
            v_in_row.created_at::DATE,
            CURRENT_DATE
        );
        v_workshop := LEFT(TRIM(COALESCE(v_in_row.workshop_name, 'Unspecified Workshop')), 150);
        v_reason := TRIM(
            COALESCE(v_in_row.repair_type, '') ||
            CASE 
                WHEN v_in_row.remarks IS NOT NULL AND TRIM(v_in_row.remarks) <> '' AND TRIM(v_in_row.remarks) <> TRIM(COALESCE(v_in_row.repair_type, ''))
                THEN ' - ' || TRIM(v_in_row.remarks)
                ELSE ''
            END
        );
        v_est_cost := public.fn_parse_maintenance_amount(v_in_row.estimated_amount);

        -- Find matching outward record
        SELECT * INTO v_out_row
        FROM public.portal_maintenance_out mo
        WHERE mo.inward_id = v_in_row.id
        ORDER BY mo.id DESC
        LIMIT 1;

        IF v_out_row.id IS NOT NULL THEN
            v_end_date := COALESCE(
                public.fn_parse_maintenance_date(v_out_row.vehicle_out_date_time),
                public.fn_parse_maintenance_date(v_out_row.rfd_date),
                v_out_row.created_at::DATE,
                v_start_date
            );
            IF v_end_date < v_start_date THEN
                v_end_date := v_start_date;
            END IF;
            v_status := 'COMPLETED';
            v_job_card := LEFT(TRIM(COALESCE(v_out_row.invoice_no, v_in_row.claim_number)), 100);
            v_act_cost := public.fn_parse_maintenance_amount(
                COALESCE(v_out_row.letzryd_payable, v_out_row.invoice_amount, '0')
            );
        ELSE
            v_end_date := NULL;
            v_act_cost := 0.00;
            v_job_card := LEFT(TRIM(v_in_row.claim_number), 100);
            IF v_in_row.is_closed = TRUE THEN
                v_status := 'COMPLETED';
                v_end_date := COALESCE(v_in_row.closed_at::DATE, v_start_date);
            ELSE
                v_status := 'IN_PROGRESS';
            END IF;
        END IF;

        -- Upsert into public.core_maintenance on portal_maintenance_in_id
        INSERT INTO public.core_maintenance (
            vehicle_number,
            city,
            start_date,
            end_date,
            status,
            workshop_name,
            job_card_number,
            maintenance_reason,
            estimated_cost,
            actual_cost,
            data_source,
            portal_maintenance_in_id,
            portal_maintenance_out_id,
            sheet_maintenance_id,
            is_deleted,
            deleted_at,
            created_at,
            updated_at
        ) VALUES (
            v_clean_veh,
            v_clean_city,
            v_start_date,
            v_end_date,
            v_status,
            v_workshop,
            v_job_card,
            NULLIF(v_reason, ''),
            v_est_cost,
            v_act_cost,
            'PORTAL_MAINTENANCE',
            v_in_row.id,
            v_out_row.id,
            NULL,
            FALSE,
            NULL,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (portal_maintenance_in_id) WHERE portal_maintenance_in_id IS NOT NULL
        DO UPDATE SET
            vehicle_number            = EXCLUDED.vehicle_number,
            city                      = EXCLUDED.city,
            start_date                = EXCLUDED.start_date,
            end_date                  = EXCLUDED.end_date,
            status                    = EXCLUDED.status,
            workshop_name             = EXCLUDED.workshop_name,
            job_card_number           = COALESCE(EXCLUDED.job_card_number, core_maintenance.job_card_number),
            maintenance_reason        = COALESCE(EXCLUDED.maintenance_reason, core_maintenance.maintenance_reason),
            estimated_cost            = EXCLUDED.estimated_cost,
            actual_cost               = CASE WHEN EXCLUDED.actual_cost > 0 THEN EXCLUDED.actual_cost ELSE core_maintenance.actual_cost END,
            portal_maintenance_out_id = COALESCE(EXCLUDED.portal_maintenance_out_id, core_maintenance.portal_maintenance_out_id),
            is_deleted                = FALSE,
            deleted_at                = NULL,
            updated_at                = CURRENT_TIMESTAMP;

        v_portal_count := v_portal_count + 1;
    END LOOP;

    -- Handle any orphaned outward records not linked to an inward record
    FOR v_out_row IN (
        SELECT mo.*
        FROM public.portal_maintenance_out mo
        LEFT JOIN public.core_maintenance cm ON cm.portal_maintenance_out_id = mo.id
        WHERE cm.id IS NULL
        ORDER BY mo.id ASC
    ) LOOP
        v_clean_veh := public.fn_clean_maintenance_vehicle(v_out_row.vehicle_number);
        v_clean_city := public.fn_clean_maintenance_city('', v_clean_veh);
        v_end_date := COALESCE(
            public.fn_parse_maintenance_date(v_out_row.vehicle_out_date_time),
            public.fn_parse_maintenance_date(v_out_row.rfd_date),
            v_out_row.created_at::DATE,
            CURRENT_DATE
        );
        v_act_cost := public.fn_parse_maintenance_amount(
            COALESCE(v_out_row.letzryd_payable, v_out_row.invoice_amount, '0')
        );

        INSERT INTO public.core_maintenance (
            vehicle_number,
            city,
            start_date,
            end_date,
            status,
            workshop_name,
            job_card_number,
            maintenance_reason,
            estimated_cost,
            actual_cost,
            data_source,
            portal_maintenance_in_id,
            portal_maintenance_out_id,
            sheet_maintenance_id,
            is_deleted,
            deleted_at,
            created_at,
            updated_at
        ) VALUES (
            v_clean_veh,
            v_clean_city,
            v_end_date,
            v_end_date,
            'COMPLETED',
            'Direct Outward Maintenance',
            LEFT(TRIM(v_out_row.invoice_no), 100),
            COALESCE(v_out_row.remarks, 'Standalone Portal Outward Release'),
            0.00,
            v_act_cost,
            'PORTAL_MAINTENANCE',
            NULL,
            v_out_row.id,
            NULL,
            FALSE,
            NULL,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        );
        v_portal_count := v_portal_count + 1;
    END LOOP;


    -- =========================================================================
    -- STEP 2: Ingest Google Sheets Maintenance Records (sheet_maintenance)
    -- =========================================================================
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'sheet_maintenance'
    ) THEN
        FOR v_sheet_row IN (
            SELECT sm.*
            FROM public.sheet_maintenance sm
            ORDER BY sm.id ASC
        ) LOOP
            v_clean_veh := public.fn_clean_maintenance_vehicle(v_sheet_row.vehicle_number);
            v_clean_city := public.fn_clean_maintenance_city(v_sheet_row.city, v_clean_veh);
            v_start_date := v_sheet_row.start_date;
            v_end_date := v_sheet_row.end_date;

            IF v_end_date IS NOT NULL AND v_end_date < v_start_date THEN
                v_end_date := v_start_date;
            END IF;

            IF v_end_date IS NOT NULL OR UPPER(COALESCE(v_sheet_row.status, '')) IN ('COMPLETED', 'RFD', 'CLOSED', 'DELIVERED') THEN
                v_status := 'COMPLETED';
            ELSE
                v_status := 'IN_PROGRESS';
            END IF;

            v_est_cost := COALESCE(v_sheet_row.estimated_cost, 0.00);
            v_act_cost := COALESCE(v_sheet_row.actual_cost, 0.00);

            INSERT INTO public.core_maintenance (
                vehicle_number,
                city,
                start_date,
                end_date,
                status,
                workshop_name,
                job_card_number,
                maintenance_reason,
                estimated_cost,
                actual_cost,
                data_source,
                portal_maintenance_in_id,
                portal_maintenance_out_id,
                sheet_maintenance_id,
                is_deleted,
                deleted_at,
                created_at,
                updated_at
            ) VALUES (
                v_clean_veh,
                v_clean_city,
                v_start_date,
                v_end_date,
                v_status,
                LEFT(TRIM(v_sheet_row.workshop_name), 150),
                LEFT(TRIM(v_sheet_row.job_card_number), 100),
                v_sheet_row.maintenance_reason,
                v_est_cost,
                v_act_cost,
                'SHEET_STATUS_EXTRACT',
                NULL,
                NULL,
                v_sheet_row.id,
                COALESCE(v_sheet_row.is_deleted, FALSE),
                v_sheet_row.deleted_at,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT (sheet_maintenance_id) WHERE sheet_maintenance_id IS NOT NULL
            DO UPDATE SET
                vehicle_number     = EXCLUDED.vehicle_number,
                city               = EXCLUDED.city,
                start_date         = EXCLUDED.start_date,
                end_date           = EXCLUDED.end_date,
                status             = EXCLUDED.status,
                workshop_name      = LEFT(TRIM(COALESCE(EXCLUDED.workshop_name, core_maintenance.workshop_name)), 150),
                job_card_number    = LEFT(TRIM(COALESCE(EXCLUDED.job_card_number, core_maintenance.job_card_number)), 100),
                maintenance_reason = COALESCE(EXCLUDED.maintenance_reason, core_maintenance.maintenance_reason),
                estimated_cost     = EXCLUDED.estimated_cost,
                actual_cost        = EXCLUDED.actual_cost,
                is_deleted         = EXCLUDED.is_deleted,
                deleted_at         = EXCLUDED.deleted_at,
                updated_at         = CURRENT_TIMESTAMP;

            v_sheet_count := v_sheet_count + 1;
        END LOOP;
    END IF;

    -- =========================================================================
    -- STEP 3: Sanitize Interval Durations & Consistency
    -- =========================================================================
    UPDATE public.core_maintenance
    SET end_date = start_date,
        updated_at = CURRENT_TIMESTAMP
    WHERE end_date IS NOT NULL AND end_date < start_date;

    UPDATE public.core_maintenance
    SET status = 'COMPLETED',
        updated_at = CURRENT_TIMESTAMP
    WHERE end_date IS NOT NULL AND status <> 'COMPLETED';

    UPDATE public.core_maintenance
    SET status = 'IN_PROGRESS',
        updated_at = CURRENT_TIMESTAMP
    WHERE end_date IS NULL AND status = 'COMPLETED';

    RAISE NOTICE 'Reconciliation complete. Processed % portal records and % sheet records.',
        v_portal_count, v_sheet_count;
END;
$procedure$
;

-- -----------------------------------------------------------------------------
-- PROCEDURE: refresh_core_partner_onboarding (original: refresh_core_partner_onboarding)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE public.refresh_core_partner_onboarding()
 LANGUAGE plpgsql
AS $procedure$
DECLARE
    r RECORD;
    v_clean_phone VARCHAR(20);
    v_partner_id VARCHAR(50);
    v_existing_id BIGINT;
    v_existing_origin VARCHAR(50);
    v_next_id BIGINT;
    v_parsed_dob DATE;
    v_parsed_dl_exp DATE;
    v_parsed_deposit NUMERIC(12, 2);
    v_clean_ref_phone VARCHAR(20);
    v_is_operator BOOLEAN;
BEGIN
    PERFORM pg_advisory_xact_lock(777111222);

    -- 5.1 Reconcile Google Sheet Records
    FOR r IN (
        SELECT DISTINCT ON (RIGHT(REGEXP_REPLACE(driver_phone, '[^0-9]', '', 'g'), 10))
            s.*,
            RIGHT(REGEXP_REPLACE(driver_phone, '[^0-9]', '', 'g'), 10) AS clean_phone
        FROM public.sheet_driver_onboarding s
        WHERE s.driver_phone IS NOT NULL AND LENGTH(REGEXP_REPLACE(s.driver_phone, '[^0-9]', '', 'g')) >= 10
        ORDER BY RIGHT(REGEXP_REPLACE(driver_phone, '[^0-9]', '', 'g'), 10), s.submission_timestamp DESC NULLS LAST, s.id DESC
    ) LOOP
        v_clean_phone := r.clean_phone;
        IF r.partner_id IS NOT NULL AND r.partner_id ~ '^LETZ[A-Z]{3}IP[0-9]{10}$' THEN
            v_partner_id := r.partner_id;
        ELSE
            v_partner_id := public.fn_canonical_partner_id(r.city, v_clean_phone, r.onboarding_type);
        END IF;

        SELECT id, source_origin INTO v_existing_id, v_existing_origin
        FROM public.core_partner_onboarding
        WHERE phone_number = v_clean_phone;

        IF v_existing_id IS NOT NULL THEN
            UPDATE public.core_partner_onboarding
            SET
                partner_id = v_partner_id,
                driver_name = COALESCE(UPPER(TRIM(r.driver_name)), core_partner_onboarding.driver_name),
                whatsapp_number = COALESCE(RIGHT(REGEXP_REPLACE(r.whatsapp_phone, '[^0-9]', '', 'g'), 10), v_clean_phone, core_partner_onboarding.whatsapp_number),
                dob = COALESCE(r.dob, core_partner_onboarding.dob),
                city = COALESCE(r.city, core_partner_onboarding.city),
                onboarding_type = COALESCE(r.onboarding_type, core_partner_onboarding.onboarding_type),
                lead_source = COALESCE(r.lead_source, core_partner_onboarding.lead_source),
                driver_plan = COALESCE(r.driver_plan, core_partner_onboarding.driver_plan),
                father_name = COALESCE(r.father_name, core_partner_onboarding.father_name),
                present_address = COALESCE(r.present_address, r.aadhaar_address, core_partner_onboarding.present_address),
                permanent_address = COALESCE(r.aadhaar_address, core_partner_onboarding.permanent_address),
                emergency_name = COALESCE(r.emergency_name, core_partner_onboarding.emergency_name),
                emergency_phone = COALESCE(r.emergency_phone, core_partner_onboarding.emergency_phone),
                reference_name = COALESCE(r.reference_name, core_partner_onboarding.reference_name),
                reference_phone = COALESCE(r.reference_phone, core_partner_onboarding.reference_phone),
                dl_number = COALESCE(r.dl_number, core_partner_onboarding.dl_number),
                dl_expiry_date = COALESCE(r.dl_expiry, core_partner_onboarding.dl_expiry_date),
                pan_number = COALESCE(r.pan_number, core_partner_onboarding.pan_number),
                aadhaar_number = COALESCE(r.aadhaar_number, core_partner_onboarding.aadhaar_number),
                pan_aadhaar_linked = COALESCE(r.pan_aadhaar_linked, core_partner_onboarding.pan_aadhaar_linked),
                account_name = COALESCE(r.account_name, core_partner_onboarding.account_name),
                account_number = COALESCE(r.account_number, core_partner_onboarding.account_number),
                ifsc_code = COALESCE(r.ifsc_code, core_partner_onboarding.ifsc_code),
                upi_id = COALESCE(r.upi_id, core_partner_onboarding.upi_id),
                selfie_photo = COALESCE(r.selfie_photo, core_partner_onboarding.selfie_photo),
                dl_front = COALESCE(r.dl_front, core_partner_onboarding.dl_front),
                dl_back = COALESCE(r.dl_back, core_partner_onboarding.dl_back),
                aadhaar_card_front = COALESCE(r.aadhaar_front, core_partner_onboarding.aadhaar_card_front),
                aadhaar_card_back = COALESCE(r.aadhaar_back, core_partner_onboarding.aadhaar_card_back),
                pan_card_photo = COALESCE(r.pan_card, core_partner_onboarding.pan_card_photo),
                local_address_proof = COALESCE(r.local_address_proof, core_partner_onboarding.local_address_proof),
                cancelled_cheque_photo = COALESCE(r.bank_details_doc, core_partner_onboarding.cancelled_cheque_photo),
                security_deposit = CASE WHEN COALESCE(r.deposit_amount, 0.00) > 0 THEN r.deposit_amount ELSE core_partner_onboarding.security_deposit END,
                source_sheet_row_id = r.id,
                source_origin = CASE WHEN v_existing_origin = 'PORTAL_FORM' THEN 'MERGED' ELSE 'GOOGLE_SHEET' END,
                is_deleted = FALSE,
                deleted_at = NULL,
                updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
            WHERE id = v_existing_id;
        ELSE
            SELECT COALESCE(MAX(id), 0) + 1 INTO v_next_id FROM public.core_partner_onboarding;

            INSERT INTO public.core_partner_onboarding (
                id, partner_id, driver_name, phone_number, whatsapp_number, dob,
                city, onboarding_type, lead_source, driver_plan, father_name,
                present_address, permanent_address, emergency_name, emergency_phone,
                reference_name, reference_phone, dl_number, dl_expiry_date,
                pan_number, aadhaar_number, pan_aadhaar_linked, account_name,
                account_number, ifsc_code, upi_id, security_deposit,
                selfie_photo, dl_front, dl_back, aadhaar_card_front, aadhaar_card_back,
                pan_card_photo, local_address_proof, cancelled_cheque_photo, approval_status,
                source_origin, source_sheet_row_id, onboarding_timestamp, is_deleted, created_at, updated_at
            ) VALUES (
                v_next_id,
                v_partner_id,
                UPPER(TRIM(r.driver_name)),
                v_clean_phone,
                COALESCE(RIGHT(REGEXP_REPLACE(r.whatsapp_phone, '[^0-9]', '', 'g'), 10), v_clean_phone),
                r.dob,
                COALESCE(r.city, 'Bengaluru'),
                COALESCE(r.onboarding_type, 'Individual'),
                r.lead_source,
                r.driver_plan,
                r.father_name,
                COALESCE(r.present_address, r.aadhaar_address),
                r.aadhaar_address,
                r.emergency_name,
                r.emergency_phone,
                r.reference_name,
                r.reference_phone,
                r.dl_number,
                r.dl_expiry,
                r.pan_number,
                r.aadhaar_number,
                r.pan_aadhaar_linked,
                r.account_name,
                r.account_number,
                r.ifsc_code,
                r.upi_id,
                COALESCE(r.deposit_amount, 0.00),
                r.selfie_photo,
                r.dl_front,
                r.dl_back,
                r.aadhaar_front,
                r.aadhaar_back,
                r.pan_card,
                r.local_address_proof,
                r.bank_details_doc,
                'Approved',
                'GOOGLE_SHEET',
                r.id,
                r.submission_timestamp,
                FALSE,
                (COALESCE(r.created_at, CURRENT_TIMESTAMP) AT TIME ZONE 'Asia/Kolkata'),
                (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
            );
        END IF;
    END LOOP;

    -- 5.2 Reconcile Portal Form Submissions
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'portal_form_onboarding') THEN
        FOR r IN (
            SELECT DISTINCT ON (RIGHT(REGEXP_REPLACE(phone_number, '[^0-9]', '', 'g'), 10))
                p.*,
                RIGHT(REGEXP_REPLACE(phone_number, '[^0-9]', '', 'g'), 10) AS clean_phone
            FROM public.portal_form_onboarding p
            WHERE p.phone_number IS NOT NULL AND LENGTH(REGEXP_REPLACE(p.phone_number, '[^0-9]', '', 'g')) >= 10
            ORDER BY RIGHT(REGEXP_REPLACE(phone_number, '[^0-9]', '', 'g'), 10), p.created_at DESC NULLS LAST, p.id DESC
        ) LOOP
            v_clean_phone := r.clean_phone;
            v_parsed_dob := public.fn_safe_cast_date(r.dob);
            v_parsed_dl_exp := public.fn_safe_cast_date(r.dl_expiry_date);
            
            BEGIN
                v_parsed_deposit := NULLIF(REGEXP_REPLACE(COALESCE(r.security_deposit, ''), '[^0-9.]', '', 'g'), '')::NUMERIC(12, 2);
            EXCEPTION WHEN OTHERS THEN
                v_parsed_deposit := 0.00;
            END;

            v_clean_ref_phone := RIGHT(REGEXP_REPLACE(COALESCE(r.ref1_phone, ''), '[^0-9]', '', 'g'), 10);

            SELECT id, source_origin INTO v_existing_id, v_existing_origin
            FROM public.core_partner_onboarding
            WHERE phone_number = v_clean_phone;

            IF v_existing_id IS NOT NULL THEN
                -- Check if partner is an Operator from either source
                SELECT (core_partner_onboarding.onboarding_type = 'Operator' OR UPPER(TRIM(COALESCE(r.candidate_role, ''))) = 'OPERATOR')
                INTO v_is_operator
                FROM public.core_partner_onboarding
                WHERE id = v_existing_id;

                IF r.driver_id IS NOT NULL AND r.driver_id ~ '^LETZ[A-Z]{3}IP[0-9]{10}$' THEN
                    v_partner_id := r.driver_id;
                ELSE
                    v_partner_id := public.fn_canonical_partner_id(r.city, v_clean_phone, CASE WHEN v_is_operator THEN 'Operator' ELSE r.candidate_role END);
                END IF;

                UPDATE public.core_partner_onboarding
                SET
                    partner_id = v_partner_id,
                    driver_name = COALESCE(UPPER(TRIM(r.driver_name)), core_partner_onboarding.driver_name),
                    whatsapp_number = COALESCE(RIGHT(REGEXP_REPLACE(COALESCE(r.whatsapp_number, r.phone_number), '[^0-9]', '', 'g'), 10), core_partner_onboarding.whatsapp_number),
                    dob = COALESCE(v_parsed_dob, core_partner_onboarding.dob),
                    father_name = COALESCE(r.father_name, core_partner_onboarding.father_name),
                    city = COALESCE(r.city, core_partner_onboarding.city),
                    onboarding_type = CASE WHEN v_is_operator THEN 'Operator' ELSE core_partner_onboarding.onboarding_type END,
                    lead_source = COALESCE(r.lead_source, core_partner_onboarding.lead_source),
                    driver_plan = COALESCE(r.rental_model, core_partner_onboarding.driver_plan),
                    present_address = COALESCE(r.present_address, core_partner_onboarding.present_address),
                    permanent_address = COALESCE(r.permanent_address, core_partner_onboarding.permanent_address),
                    emergency_name = COALESCE(r.emergency_name, core_partner_onboarding.emergency_name),
                    emergency_phone = COALESCE(r.emergency_phone, core_partner_onboarding.emergency_phone),
                    emergency_relationship = COALESCE(r.emergency_relationship, core_partner_onboarding.emergency_relationship),
                    reference_name = COALESCE(r.ref1_name, core_partner_onboarding.reference_name),
                    reference_phone = COALESCE(NULLIF(v_clean_ref_phone, ''), core_partner_onboarding.reference_phone),
                    dl_number = COALESCE(r.dl_number, core_partner_onboarding.dl_number),
                    dl_expiry_date = COALESCE(v_parsed_dl_exp, core_partner_onboarding.dl_expiry_date),
                    pan_number = COALESCE(r.pan_number, core_partner_onboarding.pan_number),
                    aadhaar_number = COALESCE(r.aadhaar_number, core_partner_onboarding.aadhaar_number),
                    pan_aadhaar_linked = COALESCE(r.pan_aadhaar_linked, core_partner_onboarding.pan_aadhaar_linked),
                    bank_name = COALESCE(r.bank_name, core_partner_onboarding.bank_name),
                    account_name = COALESCE(r.account_name, core_partner_onboarding.account_name),
                    account_number = COALESCE(r.account_number, core_partner_onboarding.account_number),
                    ifsc_code = COALESCE(r.ifsc_code, core_partner_onboarding.ifsc_code),
                    upi_id = COALESCE(r.upi_id, core_partner_onboarding.upi_id),
                    security_deposit = CASE WHEN COALESCE(v_parsed_deposit, 0.00) > 0 THEN v_parsed_deposit ELSE core_partner_onboarding.security_deposit END,
                    selfie_photo = COALESCE(r.selfie_photo, core_partner_onboarding.selfie_photo),
                    dl_front = COALESCE(r.dl_front, core_partner_onboarding.dl_front),
                    dl_back = COALESCE(r.dl_back, core_partner_onboarding.dl_back),
                    aadhaar_card_front = COALESCE(r.aadhaar_card_front, r.aadhaar_card_photo, core_partner_onboarding.aadhaar_card_front),
                    aadhaar_card_back = COALESCE(r.aadhaar_card_back, core_partner_onboarding.aadhaar_card_back),
                    pan_card_photo = COALESCE(r.pan_card_photo, core_partner_onboarding.pan_card_photo),
                    local_address_proof = COALESCE(r.local_address_proof, core_partner_onboarding.local_address_proof),
                    cancelled_cheque_photo = COALESCE(r.cancelled_cheque_photo, core_partner_onboarding.cancelled_cheque_photo),
                    approval_status = COALESCE(r.approval_status, core_partner_onboarding.approval_status),
                    is_documents_verified = COALESCE(r.documents_verified, core_partner_onboarding.is_documents_verified),
                    is_spring_verified = COALESCE(r.is_spring_verified, core_partner_onboarding.is_spring_verified),
                    source_portal_form_id = r.id,
                    source_origin = CASE WHEN v_existing_origin = 'GOOGLE_SHEET' THEN 'MERGED' ELSE 'PORTAL_FORM' END,
                    is_deleted = FALSE,
                    deleted_at = NULL,
                    updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
                WHERE id = v_existing_id;
            ELSE
                SELECT COALESCE(MAX(id), 0) + 1 INTO v_next_id FROM public.core_partner_onboarding;

                IF r.driver_id IS NOT NULL AND r.driver_id ~ '^LETZ[A-Z]{3}IP[0-9]{10}$' THEN
                    v_partner_id := r.driver_id;
                ELSE
                    v_partner_id := public.fn_canonical_partner_id(r.city, v_clean_phone, r.candidate_role);
                END IF;

                INSERT INTO public.core_partner_onboarding (
                    id, partner_id, driver_name, phone_number, whatsapp_number,
                    dob, father_name, city, onboarding_type, present_address, permanent_address, emergency_name, emergency_phone,
                    emergency_relationship, reference_name, reference_phone, dl_number, dl_expiry_date, lead_source, driver_plan,
                    pan_number, aadhaar_number, pan_aadhaar_linked, bank_name, account_name, account_number, ifsc_code,
                    upi_id, security_deposit, selfie_photo, dl_front, dl_back, aadhaar_card_front,
                    aadhaar_card_back, pan_card_photo, local_address_proof, cancelled_cheque_photo, approval_status,
                    is_documents_verified, is_spring_verified, source_origin, source_portal_form_id,
                    onboarding_timestamp, is_deleted, created_at, updated_at
                ) VALUES (
                    v_next_id,
                    v_partner_id,
                    UPPER(TRIM(r.driver_name)),
                    v_clean_phone,
                    RIGHT(REGEXP_REPLACE(COALESCE(r.whatsapp_number, r.phone_number), '[^0-9]', '', 'g'), 10),
                    v_parsed_dob,
                    r.father_name,
                    COALESCE(r.city, 'Bengaluru'),
                    COALESCE(r.candidate_role, 'Individual'),
                    r.present_address,
                    r.permanent_address,
                    r.emergency_name,
                    r.emergency_phone,
                    r.emergency_relationship,
                    r.ref1_name,
                    NULLIF(v_clean_ref_phone, ''),
                    r.dl_number,
                    v_parsed_dl_exp,
                    r.lead_source,
                    r.rental_model,
                    r.pan_number,
                    r.aadhaar_number,
                    r.pan_aadhaar_linked,
                    r.bank_name,
                    r.account_name,
                    r.account_number,
                    r.ifsc_code,
                    r.upi_id,
                    COALESCE(v_parsed_deposit, 0.00),
                    r.selfie_photo,
                    r.dl_front,
                    r.dl_back,
                    COALESCE(r.aadhaar_card_front, r.aadhaar_card_photo),
                    r.aadhaar_card_back,
                    r.pan_card_photo,
                    r.local_address_proof,
                    r.cancelled_cheque_photo,
                    COALESCE(r.approval_status, 'Draft'),
                    COALESCE(r.documents_verified, FALSE),
                    COALESCE(r.is_spring_verified, FALSE),
                    'PORTAL_FORM',
                    r.id,
                    (COALESCE(r.created_at, CURRENT_TIMESTAMP) AT TIME ZONE 'Asia/Kolkata'),
                    FALSE,
                    (COALESCE(r.created_at, CURRENT_TIMESTAMP) AT TIME ZONE 'Asia/Kolkata'),
                    (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
                );
            END IF;
        END LOOP;
    END IF;

    PERFORM setval('public.core_partner_onboarding_id_seq', (SELECT MAX(id) FROM public.core_partner_onboarding));
END;
$procedure$
;

-- -----------------------------------------------------------------------------
-- FUNCTION: refresh_portal_ola_weekly_summary (original: refresh_july_ola_weekly_summary)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.refresh_portal_ola_weekly_summary(p_week_start date DEFAULT NULL::date, p_week_end date DEFAULT NULL::date)
 RETURNS void
 LANGUAGE plpgsql
AS $function$
BEGIN
    INSERT INTO portal_ola_weekly_summary (
        vehicle_number, driver_name, driver_number, week_start, week_end, week_number,
        trips, revenue, cash_collection, toll, incentive, subscription, km, tds, raw_trips_count, updated_at
    )
    SELECT 
        vehicle_number, driver_name, driver_number, week_start, week_end, week_number,
        trips, revenue, cash_collection, toll, incentive, subscription, km, tds, raw_trips_count, NOW()
    FROM view_portal_ola_weekly_kpis
    WHERE (p_week_start IS NULL OR week_start >= p_week_start)
      AND (p_week_end IS NULL OR week_end <= p_week_end)
    ON CONFLICT (vehicle_number, week_start, week_end)
    DO UPDATE SET
        driver_name     = EXCLUDED.driver_name,
        driver_number   = EXCLUDED.driver_number,
        trips           = EXCLUDED.trips,
        revenue         = EXCLUDED.revenue,
        cash_collection = EXCLUDED.cash_collection,
        toll            = EXCLUDED.toll,
        incentive       = EXCLUDED.incentive,
        subscription    = EXCLUDED.subscription,
        km              = EXCLUDED.km,
        tds             = EXCLUDED.tds,
        raw_trips_count = EXCLUDED.raw_trips_count,
        updated_at      = NOW();
END;
$function$
;

-- -----------------------------------------------------------------------------
-- PROCEDURE: sp_backfill_core_vehicle_allocation (original: sp_backfill_core_vehicle_allocation)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE public.sp_backfill_core_vehicle_allocation()
 LANGUAGE plpgsql
AS $procedure$
DECLARE
    v_sheet_count INTEGER := 0;
    v_portal_merged INTEGER := 0;
    v_portal_new INTEGER := 0;
    v_max_id BIGINT := 0;
BEGIN
    PERFORM pg_advisory_xact_lock(888999111);

    TRUNCATE TABLE public.core_vehicle_allocation RESTART IDENTITY;

    -- Step 1: Ingest all valid records from sheet_vehicle_allocations (1..N sequence)
    INSERT INTO public.core_vehicle_allocation (
        id, source_origin, sheet_record_id, portal_record_id,
        allocation_date, vehicle_number, partner_id, driver_phone, driver_name,
        city, allocation_type, sub_type, car_model, hub_name,
        driver_plan, type_of_plan, rental_plan, partner_type,
        odometer_reading, ola_negative_balance, ola_negative_balance_proof,
        fastag_balance_amount, fastag_balance_proof, damage_penalty, deposit_refund_status, pending_dues, gps_active, duplicate_key_status,
        driver_agreement_doc, photo_front_side, photo_back_side, photo_lh_side, photo_rh_side, vehicle_driver_photo, battery_photo, odometer_photo, police_verification_doc, insp_stepney_photo, customer_address,
        security_cheque_1, security_cheque_2, security_cheque_3, security_cheque_4, security_cheques,
        jack, jack_rod_tommy, spanner_pana, stepney_tyre, parking_triangle, fire_extinguishers, floor_carpet, seat_cover, music_system, insp_remarks,
        old_vehicle_number, dropoff_odometer, dropoff_remarks, dropoff_photo, dropoff_location, manual_dropoff_location, jama_form_filled, pdi_completed,
        ret_jack, ret_jack_rod, ret_spanner, ret_parking_triangle, ret_fire_extinguishers, ret_seat_cover, ret_floor_carpet, ret_music_system, ret_insp_remarks,
        status, created_by, updated_by, current_approver_id, approval_status, approved_by, approval_remarks,
        reason_to_visit, vehicle_manager_poc, submitter_email, sheet_row_number,
        submission_timestamp, event_date_time, is_deleted, deleted_at, created_at, updated_at
    )
    SELECT
        ROW_NUMBER() OVER (ORDER BY s.allocation_date ASC, s.submission_timestamp ASC NULLS LAST, s.id ASC) AS id,
        'GOOGLE_SHEET' AS source_origin,
        s.id AS sheet_record_id,
        NULL::INTEGER AS portal_record_id,
        s.allocation_date,
        REGEXP_REPLACE(UPPER(COALESCE(s.vehicle_number, '')), '[^A-Z0-9]', '', 'g') AS vehicle_number,
        REGEXP_REPLACE(REGEXP_REPLACE(UPPER(TRIM(COALESCE(s.operator_driver_id, ''))), '^LETZOWN(BLR|HYD|MUM|PUN)', 'LETZ\1IP'), '^(LETZ(?:BLR|HYD|MUM|PUN))OP', '\1IP') AS partner_id,
        RIGHT(REGEXP_REPLACE(COALESCE(s.driver_phone, ''), '\D', '', 'g'), 10) AS driver_phone,
        LEFT(TRIM(REGEXP_REPLACE(COALESCE(s.driver_name, 'UNKNOWN'), '\s+', ' ', 'g')), 255) AS driver_name,
        CASE 
            WHEN LOWER(TRIM(COALESCE(s.city, ''))) IN ('bangalore', 'bengaluru', 'blr') THEN 'Bengaluru'
            WHEN LOWER(TRIM(COALESCE(s.city, ''))) IN ('hyderabad', 'hyd') THEN 'Hyderabad'
            WHEN LOWER(TRIM(COALESCE(s.city, ''))) IN ('mumbai', 'mum') THEN 'Mumbai'
            WHEN LOWER(TRIM(COALESCE(s.city, ''))) IN ('pune', 'pun') THEN 'Pune'
            ELSE LEFT(INITCAP(TRIM(COALESCE(s.city, 'Unknown'))), 100)
        END AS city,
        CASE
            WHEN LOWER(TRIM(COALESCE(s.allocation_type, ''))) IN ('fresh allocation', 'allocation', 'new allocation') THEN 'New Allocation'
            WHEN LOWER(TRIM(COALESCE(s.allocation_type, ''))) IN ('swap', 'car swap') THEN 'Car Swap'
            WHEN LOWER(TRIM(COALESCE(s.allocation_type, ''))) = 'reallocation' THEN 'Reallocation'
            WHEN LOWER(TRIM(COALESCE(s.allocation_type, ''))) = 'drop-off' THEN 'Drop-Off'
            ELSE INITCAP(TRIM(COALESCE(s.allocation_type, 'New Allocation')))
        END AS allocation_type,
        NULL AS sub_type,
        LEFT(s.car_model, 100) AS car_model,
        NULL AS hub_name,
        LEFT(s.driver_plan, 100) AS driver_plan,
        LEFT(s.type_of_plan, 100) AS type_of_plan,
        LEFT(s.rental_plan, 100) AS rental_plan,
        LEFT(s.partner_type, 50) AS partner_type,
        s.odometer_reading,
        s.ola_negative_amount AS ola_negative_balance,
        s.ola_negative_amount_ss AS ola_negative_balance_proof,
        NULL::NUMERIC AS fastag_balance_amount,
        NULL::TEXT AS fastag_balance_proof,
        NULL::NUMERIC AS damage_penalty,
        NULL::VARCHAR AS deposit_refund_status,
        NULL::NUMERIC AS pending_dues,
        NULL::VARCHAR AS gps_active,
        NULL::VARCHAR AS duplicate_key_status,
        s.upload_agreement AS driver_agreement_doc,
        s.front_car_photo AS photo_front_side,
        s.back_car_photo AS photo_back_side,
        s.lh_car_photo AS photo_lh_side,
        s.rh_car_photo AS photo_rh_side,
        s.driver_with_car_photo AS vehicle_driver_photo,
        s.battery_photo,
        NULL::TEXT AS odometer_photo,
        NULL::TEXT AS police_verification_doc,
        NULL::TEXT AS insp_stepney_photo,
        NULL::TEXT AS customer_address,
        NULL::TEXT AS security_cheque_1,
        NULL::TEXT AS security_cheque_2,
        NULL::TEXT AS security_cheque_3,
        NULL::TEXT AS security_cheque_4,
        NULL::TEXT AS security_cheques,
        s.jack,
        s.jack_rod_tommy,
        s.spanner_pana,
        s.stepney_tyre,
        s.parking_triangle,
        s.fire_extinguishers,
        s.floor_carpet,
        s.seat_cover,
        s.music_system,
        NULL::TEXT AS insp_remarks,
        NULL::VARCHAR AS old_vehicle_number,
        NULL::NUMERIC AS dropoff_odometer,
        NULL::TEXT AS dropoff_remarks,
        NULL::TEXT AS dropoff_photo,
        NULL::VARCHAR AS dropoff_location,
        NULL::TEXT AS manual_dropoff_location,
        NULL::BOOLEAN AS jama_form_filled,
        NULL::BOOLEAN AS pdi_completed,
        NULL::VARCHAR AS ret_jack,
        NULL::VARCHAR AS ret_jack_rod,
        NULL::VARCHAR AS ret_spanner,
        NULL::VARCHAR AS ret_parking_triangle,
        NULL::VARCHAR AS ret_fire_extinguishers,
        NULL::VARCHAR AS ret_seat_cover,
        NULL::VARCHAR AS ret_floor_carpet,
        NULL::VARCHAR AS ret_music_system,
        NULL::TEXT AS ret_insp_remarks,
        'Submitted' AS status,
        NULL::INTEGER AS created_by,
        NULL::INTEGER AS updated_by,
        NULL::INTEGER AS current_approver_id,
        NULL::VARCHAR AS approval_status,
        NULL::INTEGER AS approved_by,
        NULL::TEXT AS approval_remarks,
        LEFT(s.reason_to_visit, 255) AS reason_to_visit,
        LEFT(s.vehicle_manager_poc, 100) AS vehicle_manager_poc,
        LEFT(s.submitter_email, 255) AS submitter_email,
        s.sheet_row_number,
        s.submission_timestamp AT TIME ZONE 'Asia/Kolkata' AS submission_timestamp,
        NULL::TIMESTAMP WITHOUT TIME ZONE AS event_date_time,
        FALSE AS is_deleted,
        NULL::TIMESTAMP WITHOUT TIME ZONE AS deleted_at,
        COALESCE(s.created_at AT TIME ZONE 'Asia/Kolkata', CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata') AS created_at,
        COALESCE(s.updated_at AT TIME ZONE 'Asia/Kolkata', CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata') AS updated_at
    FROM public.sheet_vehicle_allocations s
    WHERE s.allocation_date IS NOT NULL
      AND LENGTH(REGEXP_REPLACE(UPPER(COALESCE(s.vehicle_number, '')), '[^A-Z0-9]', '', 'g')) BETWEEN 8 AND 12
      AND REGEXP_REPLACE(REGEXP_REPLACE(UPPER(TRIM(COALESCE(s.operator_driver_id, ''))), '^LETZOWN(BLR|HYD|MUM|PUN)', 'LETZ\1IP'), '^(LETZ(?:BLR|HYD|MUM|PUN))OP', '\1IP') ~ '^LETZ(BLR|HYD|MUM|PUN)(IP)?[0-9]{10}$'
      AND REGEXP_REPLACE(LOWER(TRIM(COALESCE(s.allocation_type, ''))), '[\s\-_]', '', 'g') != 'dropoff';

    GET DIAGNOSTICS v_sheet_count = ROW_COUNT;

    -- Step 2: Overlay valid records from portal_allocation_form matching core events (MERGE)
    WITH portal_ranked AS (
        SELECT p.*,
               REGEXP_REPLACE(UPPER(COALESCE(p.vehicle_number, '')), '[^A-Z0-9]', '', 'g') AS clean_vnum,
               CASE 
                   WHEN UPPER(TRIM(COALESCE(p.driver_id, ''))) ~* '^LR-[0-9]+' AND LENGTH(RIGHT(REGEXP_REPLACE(COALESCE(p.driver_phone, ''), '\D', '', 'g'), 10)) = 10 THEN
                       'LETZ' || CASE 
                           WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('bangalore', 'bengaluru', 'blr') THEN 'BLRIP'
                           WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('hyderabad', 'hyd') THEN 'HYDIP'
                           WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('mumbai', 'mum') THEN 'MUMIP'
                           WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('pune', 'pun') THEN 'PUNIP'
                           ELSE 'BLRIP'
                       END || RIGHT(REGEXP_REPLACE(COALESCE(p.driver_phone, ''), '\D', '', 'g'), 10)
                   ELSE 
                       REGEXP_REPLACE(REGEXP_REPLACE(UPPER(TRIM(COALESCE(p.driver_id, ''))), '^LETZOWN(BLR|HYD|MUM|PUN)', 'LETZ\1IP'), '^(LETZ(?:BLR|HYD|MUM|PUN))OP', '\1IP')
               END AS norm_id,
               ROW_NUMBER() OVER (
                   PARTITION BY p.allocation_date, 
                                REGEXP_REPLACE(UPPER(COALESCE(p.vehicle_number, '')), '[^A-Z0-9]', '', 'g'),
                                CASE 
                                   WHEN UPPER(TRIM(COALESCE(p.driver_id, ''))) ~* '^LR-[0-9]+' AND LENGTH(RIGHT(REGEXP_REPLACE(COALESCE(p.driver_phone, ''), '\D', '', 'g'), 10)) = 10 THEN
                                       'LETZ' || CASE 
                                           WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('bangalore', 'bengaluru', 'blr') THEN 'BLRIP'
                                           WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('hyderabad', 'hyd') THEN 'HYDIP'
                                           WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('mumbai', 'mum') THEN 'MUMIP'
                                           WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('pune', 'pun') THEN 'PUNIP'
                                           ELSE 'BLRIP'
                                       END || RIGHT(REGEXP_REPLACE(COALESCE(p.driver_phone, ''), '\D', '', 'g'), 10)
                                   ELSE 
                                       REGEXP_REPLACE(REGEXP_REPLACE(UPPER(TRIM(COALESCE(p.driver_id, ''))), '^LETZOWN(BLR|HYD|MUM|PUN)', 'LETZ\1IP'), '^(LETZ(?:BLR|HYD|MUM|PUN))OP', '\1IP')
                                END
                   ORDER BY p.created_at DESC NULLS LAST, p.id DESC
               ) as rn
        FROM public.portal_allocation_form p
        WHERE p.allocation_date IS NOT NULL
          AND LENGTH(REGEXP_REPLACE(UPPER(COALESCE(p.vehicle_number, '')), '[^A-Z0-9]', '', 'g')) BETWEEN 8 AND 12
          AND CASE 
                WHEN UPPER(TRIM(COALESCE(p.driver_id, ''))) ~* '^LR-[0-9]+' AND LENGTH(RIGHT(REGEXP_REPLACE(COALESCE(p.driver_phone, ''), '\D', '', 'g'), 10)) = 10 THEN
                    'LETZ' || CASE 
                        WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('bangalore', 'bengaluru', 'blr') THEN 'BLRIP'
                        WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('hyderabad', 'hyd') THEN 'HYDIP'
                        WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('mumbai', 'mum') THEN 'MUMIP'
                        WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('pune', 'pun') THEN 'PUNIP'
                        ELSE 'BLRIP'
                    END || RIGHT(REGEXP_REPLACE(COALESCE(p.driver_phone, ''), '\D', '', 'g'), 10)
                ELSE 
                    REGEXP_REPLACE(REGEXP_REPLACE(UPPER(TRIM(COALESCE(p.driver_id, ''))), '^LETZOWN(BLR|HYD|MUM|PUN)', 'LETZ\1IP'), '^(LETZ(?:BLR|HYD|MUM|PUN))OP', '\1IP')
              END ~ '^LETZ(BLR|HYD|MUM|PUN)(IP)?[0-9]{10}$'
          AND REGEXP_REPLACE(LOWER(TRIM(COALESCE(p.allocation_type, ''))), '[\s\-_]', '', 'g') != 'dropoff'
    ),
    portal_clean AS (
        SELECT * FROM portal_ranked WHERE rn = 1
    )
    UPDATE public.core_vehicle_allocation c
    SET source_origin = 'MERGED',
        portal_record_id = p.id,
        sub_type = LEFT(p.sub_type, 100),
        hub_name = LEFT(p.hub_name, 100),
        gps_active = LEFT(p.gps_active, 10),
        ola_negative_balance = COALESCE(p.ola_negative_balance, c.ola_negative_balance),
        ola_negative_balance_proof = COALESCE(p.ola_negative_balance_proof, c.ola_negative_balance_proof),
        fastag_balance_amount = p.fastag_balance_amount,
        fastag_balance_proof = p.fastag_balance_proof,
        damage_penalty = p.damage_penalty,
        deposit_refund_status = LEFT(p.deposit_refund_status, 50),
        pending_dues = p.pending_dues,
        duplicate_key_status = LEFT(p.duplicate_key_status, 10),
        driver_agreement_doc = COALESCE(p.driver_agreement_doc, c.driver_agreement_doc),
        photo_front_side = COALESCE(p.photo_front_side, c.photo_front_side),
        photo_back_side = COALESCE(p.photo_back_side, c.photo_back_side),
        photo_lh_side = COALESCE(p.photo_lh_side, c.photo_lh_side),
        photo_rh_side = COALESCE(p.photo_rh_side, c.photo_rh_side),
        vehicle_driver_photo = COALESCE(p.vehicle_driver_photo, c.vehicle_driver_photo),
        battery_photo = COALESCE(p.battery_photo, c.battery_photo),
        odometer_photo = p.odometer_photo,
        insp_stepney_photo = p.insp_stepney_photo,
        police_verification_doc = p.police_verification_doc,
        customer_address = p.customer_address,
        security_cheque_1 = p.security_cheque_1,
        security_cheque_2 = p.security_cheque_2,
        security_cheque_3 = p.security_cheque_3,
        security_cheque_4 = p.security_cheque_4,
        security_cheques = p.security_cheques,
        jack = COALESCE(p.insp_jack, c.jack),
        jack_rod_tommy = COALESCE(p.insp_jack_rod, c.jack_rod_tommy),
        spanner_pana = COALESCE(p.insp_spanner, c.spanner_pana),
        stepney_tyre = COALESCE(p.insp_stepney, c.stepney_tyre),
        parking_triangle = COALESCE(p.insp_parking_triangle, c.parking_triangle),
        fire_extinguishers = COALESCE(p.insp_fire_extinguishers, c.fire_extinguishers),
        floor_carpet = COALESCE(p.insp_floor_carpet, c.floor_carpet),
        seat_cover = COALESCE(p.insp_seat_cover, c.seat_cover),
        music_system = COALESCE(p.insp_music_system, c.music_system),
        insp_remarks = p.insp_remarks,
        old_vehicle_number = LEFT(p.old_vehicle_number, 50),
        dropoff_odometer = p.dropoff_odometer,
        dropoff_remarks = p.dropoff_remarks,
        dropoff_photo = p.dropoff_photo,
        dropoff_location = LEFT(p.dropoff_location, 50),
        manual_dropoff_location = p.manual_dropoff_location,
        jama_form_filled = p.jama_form_filled,
        pdi_completed = p.pdi_completed,
        ret_jack = LEFT(p.ret_jack, 30),
        ret_jack_rod = LEFT(p.ret_jack_rod, 30),
        ret_spanner = LEFT(p.ret_spanner, 30),
        ret_parking_triangle = LEFT(p.ret_parking_triangle, 30),
        ret_fire_extinguishers = LEFT(p.ret_fire_extinguishers, 30),
        ret_seat_cover = LEFT(p.ret_seat_cover, 30),
        ret_floor_carpet = LEFT(p.ret_floor_carpet, 30),
        ret_music_system = LEFT(p.ret_music_system, 30),
        ret_insp_remarks = p.ret_insp_remarks,
        status = COALESCE(LEFT(p.status, 50), c.status),
        created_by = COALESCE(p.created_by, c.created_by),
        updated_by = COALESCE(p.updated_by, c.updated_by),
        current_approver_id = p.current_approver_id,
        approval_status = LEFT(p.approval_status, 50),
        approved_by = p.approved_by,
        approval_remarks = p.approval_remarks,
        odometer_reading = CASE 
            WHEN p.odometer_reading ~ '^[0-9]+(\.[0-9]+)?$' AND p.odometer_reading::numeric BETWEEN 0 AND 2000000 
            THEN ROUND(p.odometer_reading::numeric)::integer 
            ELSE c.odometer_reading 
        END,
        event_date_time = COALESCE(p.event_date_time AT TIME ZONE 'Asia/Kolkata', c.event_date_time)
    FROM portal_clean p
    WHERE c.allocation_date = p.allocation_date
      AND c.vehicle_number = p.clean_vnum
      AND (c.partner_id = p.norm_id OR c.driver_phone = RIGHT(REGEXP_REPLACE(COALESCE(p.driver_phone, ''), '\D', '', 'g'), 10));

    GET DIAGNOSTICS v_portal_merged = ROW_COUNT;

    -- Step 3: Insert portal-only valid records (PORTAL_FORM)
    SELECT COALESCE(MAX(id), 0) INTO v_max_id FROM public.core_vehicle_allocation;

    WITH portal_ranked AS (
        SELECT p.*,
               REGEXP_REPLACE(UPPER(COALESCE(p.vehicle_number, '')), '[^A-Z0-9]', '', 'g') AS clean_vnum,
               CASE 
                   WHEN UPPER(TRIM(COALESCE(p.driver_id, ''))) ~* '^LR-[0-9]+' AND LENGTH(RIGHT(REGEXP_REPLACE(COALESCE(p.driver_phone, ''), '\D', '', 'g'), 10)) = 10 THEN
                       'LETZ' || CASE 
                           WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('bangalore', 'bengaluru', 'blr') THEN 'BLRIP'
                           WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('hyderabad', 'hyd') THEN 'HYDIP'
                           WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('mumbai', 'mum') THEN 'MUMIP'
                           WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('pune', 'pun') THEN 'PUNIP'
                           ELSE 'BLRIP'
                       END || RIGHT(REGEXP_REPLACE(COALESCE(p.driver_phone, ''), '\D', '', 'g'), 10)
                   ELSE 
                       REGEXP_REPLACE(REGEXP_REPLACE(UPPER(TRIM(COALESCE(p.driver_id, ''))), '^LETZOWN(BLR|HYD|MUM|PUN)', 'LETZ\1IP'), '^(LETZ(?:BLR|HYD|MUM|PUN))OP', '\1IP')
               END AS norm_id,
               ROW_NUMBER() OVER (
                   PARTITION BY p.allocation_date, 
                                REGEXP_REPLACE(UPPER(COALESCE(p.vehicle_number, '')), '[^A-Z0-9]', '', 'g'),
                                CASE 
                                   WHEN UPPER(TRIM(COALESCE(p.driver_id, ''))) ~* '^LR-[0-9]+' AND LENGTH(RIGHT(REGEXP_REPLACE(COALESCE(p.driver_phone, ''), '\D', '', 'g'), 10)) = 10 THEN
                                       'LETZ' || CASE 
                                           WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('bangalore', 'bengaluru', 'blr') THEN 'BLRIP'
                                           WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('hyderabad', 'hyd') THEN 'HYDIP'
                                           WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('mumbai', 'mum') THEN 'MUMIP'
                                           WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('pune', 'pun') THEN 'PUNIP'
                                           ELSE 'BLRIP'
                                       END || RIGHT(REGEXP_REPLACE(COALESCE(p.driver_phone, ''), '\D', '', 'g'), 10)
                                   ELSE 
                                       REGEXP_REPLACE(REGEXP_REPLACE(UPPER(TRIM(COALESCE(p.driver_id, ''))), '^LETZOWN(BLR|HYD|MUM|PUN)', 'LETZ\1IP'), '^(LETZ(?:BLR|HYD|MUM|PUN))OP', '\1IP')
                                END
                   ORDER BY p.created_at DESC NULLS LAST, p.id DESC
               ) as rn
        FROM public.portal_allocation_form p
        WHERE p.allocation_date IS NOT NULL
          AND LENGTH(REGEXP_REPLACE(UPPER(COALESCE(p.vehicle_number, '')), '[^A-Z0-9]', '', 'g')) BETWEEN 8 AND 12
          AND CASE 
                WHEN UPPER(TRIM(COALESCE(p.driver_id, ''))) ~* '^LR-[0-9]+' AND LENGTH(RIGHT(REGEXP_REPLACE(COALESCE(p.driver_phone, ''), '\D', '', 'g'), 10)) = 10 THEN
                    'LETZ' || CASE 
                        WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('bangalore', 'bengaluru', 'blr') THEN 'BLRIP'
                        WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('hyderabad', 'hyd') THEN 'HYDIP'
                        WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('mumbai', 'mum') THEN 'MUMIP'
                        WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('pune', 'pun') THEN 'PUNIP'
                        ELSE 'BLRIP'
                    END || RIGHT(REGEXP_REPLACE(COALESCE(p.driver_phone, ''), '\D', '', 'g'), 10)
                ELSE 
                    REGEXP_REPLACE(REGEXP_REPLACE(UPPER(TRIM(COALESCE(p.driver_id, ''))), '^LETZOWN(BLR|HYD|MUM|PUN)', 'LETZ\1IP'), '^(LETZ(?:BLR|HYD|MUM|PUN))OP', '\1IP')
              END ~ '^LETZ(BLR|HYD|MUM|PUN)(IP)?[0-9]{10}$'
          AND REGEXP_REPLACE(LOWER(TRIM(COALESCE(p.allocation_type, ''))), '[\s\-_]', '', 'g') != 'dropoff'
    ),
    portal_clean AS (
        SELECT * FROM portal_ranked WHERE rn = 1
    ),
    portal_new_records AS (
        SELECT p.*,
               ROW_NUMBER() OVER (ORDER BY p.allocation_date ASC, p.created_at ASC NULLS LAST, p.id ASC) AS portal_seq
        FROM portal_clean p
        LEFT JOIN public.core_vehicle_allocation c 
          ON c.allocation_date = p.allocation_date
         AND c.vehicle_number = p.clean_vnum
         AND (c.partner_id = p.norm_id OR c.driver_phone = RIGHT(REGEXP_REPLACE(COALESCE(p.driver_phone, ''), '\D', '', 'g'), 10))
        WHERE c.id IS NULL
    )
    INSERT INTO public.core_vehicle_allocation (
        id, source_origin, sheet_record_id, portal_record_id,
        allocation_date, vehicle_number, partner_id, driver_phone, driver_name,
        city, allocation_type, sub_type, car_model, hub_name,
        driver_plan, type_of_plan, rental_plan, partner_type,
        odometer_reading, ola_negative_balance, ola_negative_balance_proof,
        fastag_balance_amount, fastag_balance_proof, damage_penalty, deposit_refund_status, pending_dues, gps_active, duplicate_key_status,
        driver_agreement_doc, photo_front_side, photo_back_side, photo_lh_side, photo_rh_side, vehicle_driver_photo, battery_photo, odometer_photo, police_verification_doc, insp_stepney_photo, customer_address,
        security_cheque_1, security_cheque_2, security_cheque_3, security_cheque_4, security_cheques,
        jack, jack_rod_tommy, spanner_pana, stepney_tyre, parking_triangle, fire_extinguishers, floor_carpet, seat_cover, music_system, insp_remarks,
        old_vehicle_number, dropoff_odometer, dropoff_remarks, dropoff_photo, dropoff_location, manual_dropoff_location, jama_form_filled, pdi_completed,
        ret_jack, ret_jack_rod, ret_spanner, ret_parking_triangle, ret_fire_extinguishers, ret_seat_cover, ret_floor_carpet, ret_music_system, ret_insp_remarks,
        status, created_by, updated_by, current_approver_id, approval_status, approved_by, approval_remarks,
        reason_to_visit, vehicle_manager_poc, submitter_email, sheet_row_number,
        submission_timestamp, event_date_time, is_deleted, deleted_at, created_at, updated_at
    )
    SELECT
        v_max_id + p.portal_seq AS id,
        'PORTAL_FORM' AS source_origin,
        NULL::BIGINT AS sheet_record_id,
        p.id AS portal_record_id,
        p.allocation_date,
        p.clean_vnum AS vehicle_number,
        p.norm_id AS partner_id,
        RIGHT(REGEXP_REPLACE(COALESCE(p.driver_phone, ''), '\D', '', 'g'), 10) AS driver_phone,
        LEFT(TRIM(REGEXP_REPLACE(COALESCE(p.driver_name, 'UNKNOWN'), '\s+', ' ', 'g')), 255) AS driver_name,
        CASE 
            WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('bangalore', 'bengaluru', 'blr') THEN 'Bengaluru'
            WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('hyderabad', 'hyd') THEN 'Hyderabad'
            WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('mumbai', 'mum') THEN 'Mumbai'
            WHEN LOWER(TRIM(COALESCE(p.city_name, ''))) IN ('pune', 'pun') THEN 'Pune'
            ELSE LEFT(INITCAP(TRIM(COALESCE(p.city_name, 'Unknown'))), 100)
        END AS city,
        CASE
            WHEN LOWER(TRIM(COALESCE(p.allocation_type, ''))) IN ('fresh allocation', 'allocation', 'new allocation') THEN 'New Allocation'
            WHEN LOWER(TRIM(COALESCE(p.allocation_type, ''))) IN ('swap', 'car swap') THEN 'Car Swap'
            WHEN LOWER(TRIM(COALESCE(p.allocation_type, ''))) = 'reallocation' THEN 'Reallocation'
            WHEN LOWER(TRIM(COALESCE(p.allocation_type, ''))) = 'drop-off' THEN 'Drop-Off'
            ELSE INITCAP(TRIM(COALESCE(p.allocation_type, 'New Allocation')))
        END AS allocation_type,
        LEFT(p.sub_type, 100) AS sub_type,
        LEFT(p.car_model, 100) AS car_model,
        LEFT(p.hub_name, 100) AS hub_name,
        LEFT(p.driver_plan, 100) AS driver_plan,
        LEFT(p.type_of_plan, 100) AS type_of_plan,
        NULL::VARCHAR AS rental_plan,
        NULL::VARCHAR AS partner_type,
        CASE 
            WHEN p.odometer_reading ~ '^[0-9]+(\.[0-9]+)?$' AND p.odometer_reading::numeric BETWEEN 0 AND 2000000 
            THEN ROUND(p.odometer_reading::numeric)::integer 
            ELSE NULL 
        END AS odometer_reading,
        p.ola_negative_balance,
        p.ola_negative_balance_proof,
        p.fastag_balance_amount,
        p.fastag_balance_proof,
        p.damage_penalty,
        LEFT(p.deposit_refund_status, 50) AS deposit_refund_status,
        p.pending_dues,
        LEFT(p.gps_active, 10) AS gps_active,
        LEFT(p.duplicate_key_status, 10) AS duplicate_key_status,
        p.driver_agreement_doc,
        p.photo_front_side,
        p.photo_back_side,
        p.photo_lh_side,
        p.photo_rh_side,
        p.vehicle_driver_photo,
        p.battery_photo,
        p.odometer_photo,
        p.police_verification_doc,
        p.insp_stepney_photo,
        p.customer_address,
        p.security_cheque_1,
        p.security_cheque_2,
        p.security_cheque_3,
        p.security_cheque_4,
        p.security_cheques,
        p.insp_jack AS jack,
        p.insp_jack_rod AS jack_rod_tommy,
        p.insp_spanner AS spanner_pana,
        p.insp_stepney AS stepney_tyre,
        p.insp_parking_triangle AS parking_triangle,
        p.insp_fire_extinguishers AS fire_extinguishers,
        p.insp_floor_carpet AS floor_carpet,
        p.insp_seat_cover AS seat_cover,
        p.insp_music_system AS music_system,
        p.insp_remarks,
        LEFT(p.old_vehicle_number, 50) AS old_vehicle_number,
        p.dropoff_odometer,
        p.dropoff_remarks,
        p.dropoff_photo,
        LEFT(p.dropoff_location, 50) AS dropoff_location,
        p.manual_dropoff_location,
        p.jama_form_filled,
        p.pdi_completed,
        LEFT(p.ret_jack, 30) AS ret_jack,
        LEFT(p.ret_jack_rod, 30) AS ret_jack_rod,
        LEFT(p.ret_spanner, 30) AS ret_spanner,
        LEFT(p.ret_parking_triangle, 30) AS ret_parking_triangle,
        LEFT(p.ret_fire_extinguishers, 30) AS ret_fire_extinguishers,
        LEFT(p.ret_seat_cover, 30) AS ret_seat_cover,
        LEFT(p.ret_floor_carpet, 30) AS ret_floor_carpet,
        LEFT(p.ret_music_system, 30) AS ret_music_system,
        p.ret_insp_remarks,
        COALESCE(LEFT(p.status, 50), 'Submitted') AS status,
        p.created_by,
        p.updated_by,
        p.current_approver_id,
        LEFT(p.approval_status, 50) AS approval_status,
        p.approved_by,
        p.approval_remarks,
        NULL::VARCHAR AS reason_to_visit,
        NULL::VARCHAR AS vehicle_manager_poc,
        NULL::VARCHAR AS submitter_email,
        NULL::INTEGER AS sheet_row_number,
        NULL::TIMESTAMP WITHOUT TIME ZONE AS submission_timestamp,
        p.event_date_time AT TIME ZONE 'Asia/Kolkata' AS event_date_time,
        FALSE AS is_deleted,
        NULL::TIMESTAMP WITHOUT TIME ZONE AS deleted_at,
        COALESCE(p.created_at AT TIME ZONE 'Asia/Kolkata', CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata') AS created_at,
        COALESCE(p.updated_at AT TIME ZONE 'Asia/Kolkata', CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata') AS updated_at
    FROM portal_new_records p;

    GET DIAGNOSTICS v_portal_new = ROW_COUNT;

    -- Step 4: Reset the ID sequence to exactly match MAX(id)
    PERFORM setval('public.core_vehicle_allocation_id_seq', COALESCE((SELECT MAX(id) FROM public.core_vehicle_allocation), 1), true);

    RAISE NOTICE 'Backfill Completed: Sheet Rows = %, Portal Merged = %, Portal New = %, Total Core Rows = %',
        v_sheet_count, v_portal_merged, v_portal_new, (v_sheet_count + v_portal_new);
END;
$procedure$
;

-- -----------------------------------------------------------------------------
-- PROCEDURE: sp_rebuild_core_maintenance (original: sp_rebuild_core_maintenance)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE public.sp_rebuild_core_maintenance()
 LANGUAGE plpgsql
AS $procedure$
    DECLARE
        v_in RECORD;
        v_out RECORD;
        v_sheet RECORD;
        v_curr_id BIGINT := 0;
        v_clean_veh VARCHAR(50);
        v_clean_city VARCHAR(100);
        v_in_dt TIMESTAMP WITHOUT TIME ZONE;
        v_out_dt TIMESTAMP WITHOUT TIME ZONE;
        v_start_date DATE;
        v_end_date DATE;
        v_est_delivery DATE;
        v_appr_date DATE;
        v_est_amt NUMERIC(12, 2);
        v_inv_amt NUMERIC(12, 2);
        v_ins_disc NUMERIC(12, 2);
        v_payable NUMERIC(12, 2);
        v_in_kms INTEGER;
        v_out_kms INTEGER;
        v_ins_claimed BOOLEAN;
        v_status VARCHAR(50);
        v_attrs JSONB;
    BEGIN
        PERFORM pg_advisory_xact_lock(888999111);

        TRUNCATE TABLE public.core_maintenance;

        -- STEP 1: Ingest Web Portal Inward & Outward Records (Portal Priority)
        FOR v_in IN 
            SELECT * FROM public.portal_maintenance_in ORDER BY id ASC
        LOOP
            v_curr_id := v_curr_id + 1;
            v_clean_veh := public.fn_clean_maintenance_vehicle(v_in.vehicle_number);
            v_clean_city := public.fn_clean_maintenance_city(v_in.city_name, v_clean_veh);
            v_in_dt := public.fn_parse_maintenance_timestamp(v_in.vehicle_in_date_time);
            v_start_date := COALESCE(v_in_dt::DATE, v_in.created_at::DATE, (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')::DATE);
            v_est_delivery := public.fn_parse_maintenance_date(v_in.estimated_delivery_date);
            v_appr_date := public.fn_parse_maintenance_date(v_in.approval_date);
            v_est_amt := public.fn_parse_maintenance_numeric(v_in.estimated_amount);
            v_in_kms := public.fn_parse_maintenance_int(v_in.vehicle_k_m_s);
            v_ins_claimed := CASE WHEN LOWER(TRIM(COALESCE(v_in.insurance_claimed, ''))) IN ('yes', 'true', '1') THEN TRUE ELSE FALSE END;

            v_attrs := '{}'::jsonb;
            IF v_clean_veh IN ('TEST', 'TESTVEHICLE', 'ROLLERTEST') OR v_clean_veh ILIKE '%TEST%' THEN
                v_attrs := jsonb_set(v_attrs, '{is_test}', 'true'::jsonb);
            END IF;

            SELECT * INTO v_out FROM public.portal_maintenance_out WHERE inward_id = v_in.id ORDER BY id DESC LIMIT 1;
            IF FOUND THEN
                v_out_dt := public.fn_parse_maintenance_timestamp(v_out.vehicle_out_date_time);
                v_end_date := COALESCE(public.fn_parse_maintenance_date(v_out.rfd_date), v_out_dt::DATE);
                IF v_end_date IS NOT NULL AND v_end_date < v_start_date THEN
                    v_end_date := v_start_date;
                END IF;
                v_out_kms := public.fn_parse_maintenance_int(v_out.vehicle_out_k_m_s);
                IF v_in_kms IS NOT NULL AND v_out_kms IS NOT NULL AND v_out_kms < v_in_kms THEN
                    v_attrs := jsonb_set(v_attrs, '{odometer_warning}', to_jsonb(format('Outward odometer (%s) lower than intake odometer (%s)', v_out_kms, v_in_kms)));
                END IF;
                v_inv_amt := public.fn_parse_maintenance_numeric(v_out.invoice_amount);
                v_ins_disc := public.fn_parse_maintenance_numeric(v_out.insurance_liability_discounts);
                v_payable := public.fn_parse_maintenance_numeric(v_out.letzryd_payable);
                v_status := COALESCE(v_out.final_status, 'Completed & RFD');
            ELSE
                v_end_date := NULL;
                v_out_dt := NULL;
                v_out_kms := NULL;
                v_inv_amt := 0.00;
                v_ins_disc := 0.00;
                v_payable := 0.00;
                v_status := CASE WHEN v_in.is_closed = TRUE THEN 'COMPLETED' ELSE 'IN_PROGRESS' END;
            END IF;

            INSERT INTO public.core_maintenance (
                id, source_type, portal_maintenance_in_id, portal_maintenance_out_id, sheet_maintenance_id,
                vehicle_number, city, vehicle_location, vehicle_model,
                start_date, end_date, in_date_time, out_date_time, estimated_delivery_date, rfd_date,
                maintenance_status, cohort, partner_name, partner_ids, new_partner_name_default, dm_name, type, mapping,
                repair_type, workshop_name, in_kms, out_kms, job_card_number, remarks,
                estimated_amount, invoice_no, invoice_date, invoice_amount,
                insurance_claimed, insurance_brokerage, claim_number, insurance_liability_discounts, letzryd_payable,
                type_of_payment, payment_status, utr_no, approved_by, approval_date,
                approval_file, damage_photos, outward_photos, invoice_file,
                extra_attributes, is_deleted, deleted_at, created_at, updated_at
            ) VALUES (
                v_curr_id, 'WEB_PORTAL', v_in.id, v_out.id, NULL,
                v_clean_veh, v_clean_city, v_in.vehicle_location, NULL,
                v_start_date, v_end_date, v_in_dt, v_out_dt, v_est_delivery, v_end_date,
                v_status, 'Off Road', 
                COALESCE(v_out.partner_name, v_out.driver_name),
                COALESCE(v_out.partner_id, v_out.driver_id),
                NULL, NULL, NULL, NULL,
                v_in.repair_type, v_in.workshop_name, v_in_kms, v_out_kms, NULL, COALESCE(v_in.remarks, v_out.remarks),
                v_est_amt, v_out.invoice_no, public.fn_parse_maintenance_date(v_out.invoice_date), v_inv_amt,
                v_ins_claimed, v_in.insurance_brokerage, v_in.claim_number, v_ins_disc, v_payable,
                v_out.type_of_payment, v_out.payment_status, v_out.utr_no, COALESCE(v_in.approved_by, v_out.approved_by), COALESCE(v_appr_date, public.fn_parse_maintenance_date(v_out.approval_date)),
                COALESCE(v_in.approval_file, v_out.approval_file), v_in.vehicle_damage_photos, v_out.vehicle_out_photos, v_out.invoice_file,
                v_attrs, FALSE, NULL,
                COALESCE(v_in.created_at, (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')),
                (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
            );
        END LOOP;

        -- STEP 2: Ingest Google Sheets Staging Records (Reconciliation & Deduplication)
        FOR v_sheet IN 
            SELECT * FROM public.sheet_maintenance WHERE is_deleted = FALSE ORDER BY id ASC
        LOOP
            v_clean_veh := public.fn_clean_maintenance_vehicle(v_sheet.vehicle_number);
            v_clean_city := public.fn_clean_maintenance_city(v_sheet.city, v_clean_veh);
            v_start_date := v_sheet.date;

            -- Portal Priority check (including open-ended tickets end_date IS NULL)
            IF EXISTS (
                SELECT 1 FROM public.core_maintenance 
                WHERE vehicle_number = v_clean_veh 
                  AND source_type = 'WEB_PORTAL'
                  AND is_deleted = FALSE
                  AND (
                      start_date = v_start_date 
                      OR (end_date IS NOT NULL AND v_start_date BETWEEN start_date AND end_date)
                      OR (end_date IS NULL AND v_start_date >= start_date)
                  )
            ) THEN
                -- Enrich existing portal record with sheet metadata
                UPDATE public.core_maintenance SET
                    vehicle_model = COALESCE(vehicle_model, v_sheet.vehicle_model),
                    partner_name = COALESCE(partner_name, v_sheet.partner_name),
                    partner_ids = COALESCE(partner_ids, v_sheet.partner_ids),
                    dm_name = COALESCE(dm_name, v_sheet.dm_name),
                    type = COALESCE(type, v_sheet.type),
                    mapping = COALESCE(mapping, v_sheet.mapping),
                    updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
                WHERE vehicle_number = v_clean_veh 
                  AND source_type = 'WEB_PORTAL'
                  AND is_deleted = FALSE
                  AND (
                      start_date = v_start_date 
                      OR (end_date IS NOT NULL AND v_start_date BETWEEN start_date AND end_date)
                      OR (end_date IS NULL AND v_start_date >= start_date)
                  );
            ELSE
                v_curr_id := v_curr_id + 1;

                INSERT INTO public.core_maintenance (
                    id, source_type, portal_maintenance_in_id, portal_maintenance_out_id, sheet_maintenance_id,
                    vehicle_number, city, vehicle_location, vehicle_model,
                    start_date, end_date, in_date_time, out_date_time, estimated_delivery_date, rfd_date,
                    maintenance_status, cohort, partner_name, partner_ids, new_partner_name_default, dm_name, type, mapping,
                    repair_type, workshop_name, in_kms, out_kms, job_card_number, remarks,
                    estimated_amount, invoice_no, invoice_date, invoice_amount,
                    insurance_claimed, insurance_brokerage, claim_number, insurance_liability_discounts, letzryd_payable,
                    type_of_payment, payment_status, utr_no, approved_by, approval_date,
                    approval_file, damage_photos, outward_photos, invoice_file,
                    extra_attributes, is_deleted, deleted_at, created_at, updated_at
                ) VALUES (
                    v_curr_id, 'GOOGLE_SHEET', NULL, NULL, v_sheet.id,
                    v_clean_veh, v_clean_city, NULL, v_sheet.vehicle_model,
                    v_start_date, v_sheet.drop_off_date, NULL, NULL, NULL, v_sheet.drop_off_date,
                    CASE WHEN LOWER(TRIM(v_sheet.final_status)) = 'maintenance' THEN 'IN_PROGRESS' ELSE v_sheet.final_status END,
                    COALESCE(v_sheet.cohort, 'Off Road'), v_sheet.partner_name, v_sheet.partner_ids, v_sheet.new_partner_name_default, v_sheet.dm_name, v_sheet.type, v_sheet.mapping,
                    NULL, NULL, NULL, NULL, NULL, NULL,
                    0.00, NULL, NULL, 0.00,
                    FALSE, NULL, NULL, 0.00, 0.00,
                    NULL, NULL, NULL, NULL, NULL,
                    NULL, NULL, NULL, NULL,
                    '{}'::jsonb, FALSE, NULL,
                    COALESCE(v_sheet.created_at, (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')),
                    (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
                );
            END IF;
        END LOOP;

        RAISE NOTICE 'sp_rebuild_core_maintenance completed. Total records inserted: %', v_curr_id;
    END;
    $procedure$
;

-- -----------------------------------------------------------------------------
-- FUNCTION: sync_core_allocation_from_portal (original: sync_core_allocation_from_portal)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.sync_core_allocation_from_portal()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_clean_vnum VARCHAR(100);
    v_norm_partner_id VARCHAR(150);
    v_clean_phone VARCHAR(50);
    v_clean_city VARCHAR(100);
    v_clean_alloc_type VARCHAR(100);
    v_clean_name VARCHAR(255);
    v_existing_id BIGINT;
    v_existing_sheet_id BIGINT;
    v_source_origin VARCHAR(50);
    v_next_id BIGINT;
    v_event_ts TIMESTAMP WITHOUT TIME ZONE;
    v_created_ts TIMESTAMP WITHOUT TIME ZONE;
    v_updated_ts TIMESTAMP WITHOUT TIME ZONE;
    v_odo_val INTEGER;
BEGIN
    BEGIN
        IF TG_OP = 'DELETE' THEN
            UPDATE public.core_vehicle_allocation
            SET is_deleted = TRUE,
                deleted_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'),
                updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
            WHERE portal_record_id = OLD.id;
            RETURN OLD;
        END IF;

    -- City canonicalization
    v_clean_city := CASE 
        WHEN LOWER(TRIM(COALESCE(NEW.city_name, ''))) IN ('bangalore', 'bengaluru', 'blr') THEN 'Bengaluru'
        WHEN LOWER(TRIM(COALESCE(NEW.city_name, ''))) IN ('hyderabad', 'hyd') THEN 'Hyderabad'
        WHEN LOWER(TRIM(COALESCE(NEW.city_name, ''))) IN ('mumbai', 'mum') THEN 'Mumbai'
        WHEN LOWER(TRIM(COALESCE(NEW.city_name, ''))) IN ('pune', 'pun') THEN 'Pune'
        ELSE LEFT(INITCAP(TRIM(COALESCE(NEW.city_name, 'Unknown'))), 100)
    END;

    -- Normalization
    v_clean_vnum := REGEXP_REPLACE(UPPER(COALESCE(NEW.vehicle_number, '')), '[^A-Z0-9]', '', 'g');
    v_clean_phone := RIGHT(REGEXP_REPLACE(COALESCE(NEW.driver_phone, ''), '\D', '', 'g'), 10);
    v_norm_partner_id := REGEXP_REPLACE(UPPER(TRIM(COALESCE(NEW.driver_id, ''))), '^LETZOWN(BLR|HYD|MUM|PUN)', 'LETZ\1IP');
    v_norm_partner_id := REGEXP_REPLACE(v_norm_partner_id, '^(LETZ(?:BLR|HYD|MUM|PUN))OP', '\1IP');

    -- Walk-in lead code resolution (e.g. LR-6720 entered instead of LETZ partner ID)
    IF v_norm_partner_id ~* '^LR-[0-9]+' AND LENGTH(v_clean_phone) = 10 THEN
        v_norm_partner_id := 'LETZ' || CASE 
            WHEN v_clean_city = 'Bengaluru' THEN 'BLRIP'
            WHEN v_clean_city = 'Hyderabad' THEN 'HYDIP'
            WHEN v_clean_city = 'Mumbai' THEN 'MUMIP'
            WHEN v_clean_city = 'Pune' THEN 'PUNIP'
            ELSE 'BLRIP'
        END || v_clean_phone;
    END IF;

    -- Drop-off filter: Drop-off entries belong strictly to the drop-off pipeline (soft-delete to preserve sequence & audit trail)
    IF REGEXP_REPLACE(LOWER(TRIM(COALESCE(NEW.allocation_type, ''))), '[\s\-_]', '', 'g') = 'dropoff' THEN
        UPDATE public.core_vehicle_allocation
        SET is_deleted = TRUE,
            deleted_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'),
            updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
        WHERE portal_record_id = NEW.id;
        RETURN NEW;
    END IF;

    -- Gatekeeper check (Rejects invalid test records)
    IF NEW.allocation_date IS NULL OR LENGTH(v_clean_vnum) NOT BETWEEN 8 AND 12 OR v_norm_partner_id !~ '^LETZ(BLR|HYD|MUM|PUN)(IP)?[0-9]{10}$' THEN
        RETURN NEW;
    END IF;

    -- Allocation type standardization
    v_clean_alloc_type := CASE
        WHEN LOWER(TRIM(COALESCE(NEW.allocation_type, ''))) IN ('fresh allocation', 'allocation', 'new allocation') THEN 'New Allocation'
        WHEN LOWER(TRIM(COALESCE(NEW.allocation_type, ''))) IN ('swap', 'car swap') THEN 'Car Swap'
        WHEN LOWER(TRIM(COALESCE(NEW.allocation_type, ''))) = 'reallocation' THEN 'Reallocation'
        WHEN LOWER(TRIM(COALESCE(NEW.allocation_type, ''))) = 'drop-off' THEN 'Drop-Off'
        ELSE INITCAP(TRIM(COALESCE(NEW.allocation_type, 'New Allocation')))
    END;

    v_clean_name := LEFT(TRIM(REGEXP_REPLACE(COALESCE(NEW.driver_name, 'UNKNOWN'), '\s+', ' ', 'g')), 255);
    IF v_clean_name = '' OR v_clean_name IS NULL THEN v_clean_name := 'UNKNOWN'; END IF;

    -- Odometer reading parsing
    v_odo_val := CASE 
        WHEN NEW.odometer_reading ~ '^[0-9]+(\.[0-9]+)?$' AND NEW.odometer_reading::numeric BETWEEN 0 AND 2000000 
        THEN ROUND(NEW.odometer_reading::numeric)::integer
        ELSE NULL
    END;

    v_event_ts := NEW.event_date_time AT TIME ZONE 'Asia/Kolkata';
    v_created_ts := COALESCE(NEW.created_at AT TIME ZONE 'Asia/Kolkata', (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'));
    v_updated_ts := COALESCE(NEW.updated_at AT TIME ZONE 'Asia/Kolkata', (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'));

    PERFORM pg_advisory_xact_lock(888999111);

    -- Check if record exists on (allocation_date, vehicle_number, partner_id) or portal_record_id
    SELECT id, sheet_record_id 
    INTO v_existing_id, v_existing_sheet_id
    FROM public.core_vehicle_allocation
    WHERE (portal_record_id = NEW.id) 
       OR (allocation_date = NEW.allocation_date AND vehicle_number = v_clean_vnum AND (partner_id = v_norm_partner_id OR driver_phone = v_clean_phone))
    ORDER BY (portal_record_id = NEW.id) DESC
    LIMIT 1;

    IF v_existing_id IS NOT NULL THEN
        -- Record exists: overlay portal inspection data, photos, cheques & mark MERGED
        IF v_existing_sheet_id IS NOT NULL THEN
            v_source_origin := 'MERGED';
        ELSE
            v_source_origin := 'PORTAL_FORM';
        END IF;

        UPDATE public.core_vehicle_allocation SET
            source_origin = v_source_origin,
            portal_record_id = NEW.id,
            allocation_date = NEW.allocation_date,
            vehicle_number = v_clean_vnum,
            partner_id = v_norm_partner_id,
            driver_phone = COALESCE(NULLIF(v_clean_phone, ''), driver_phone),
            driver_name = COALESCE(NULLIF(v_clean_name, 'UNKNOWN'), driver_name),
            city = COALESCE(NULLIF(v_clean_city, 'Unknown'), city),
            allocation_type = COALESCE(v_clean_alloc_type, allocation_type),
            sub_type = LEFT(NEW.sub_type, 100),
            car_model = COALESCE(LEFT(NEW.car_model, 100), car_model),
            hub_name = LEFT(NEW.hub_name, 100),
            driver_plan = COALESCE(LEFT(NEW.driver_plan, 100), driver_plan),
            type_of_plan = COALESCE(LEFT(NEW.type_of_plan, 100), type_of_plan),
            gps_active = LEFT(NEW.gps_active, 10),
            ola_negative_balance = COALESCE(NEW.ola_negative_balance, ola_negative_balance),
            ola_negative_balance_proof = COALESCE(NEW.ola_negative_balance_proof, ola_negative_balance_proof),
            fastag_balance_amount = NEW.fastag_balance_amount,
            fastag_balance_proof = NEW.fastag_balance_proof,
            damage_penalty = NEW.damage_penalty,
            deposit_refund_status = LEFT(NEW.deposit_refund_status, 50),
            pending_dues = NEW.pending_dues,
            duplicate_key_status = LEFT(NEW.duplicate_key_status, 10),
            driver_agreement_doc = COALESCE(NEW.driver_agreement_doc, driver_agreement_doc),
            photo_front_side = COALESCE(NEW.photo_front_side, photo_front_side),
            photo_back_side = COALESCE(NEW.photo_back_side, photo_back_side),
            photo_lh_side = COALESCE(NEW.photo_lh_side, photo_lh_side),
            photo_rh_side = COALESCE(NEW.photo_rh_side, photo_rh_side),
            vehicle_driver_photo = COALESCE(NEW.vehicle_driver_photo, vehicle_driver_photo),
            battery_photo = COALESCE(NEW.battery_photo, battery_photo),
            odometer_photo = NEW.odometer_photo,
            insp_stepney_photo = NEW.insp_stepney_photo,
            police_verification_doc = NEW.police_verification_doc,
            customer_address = NEW.customer_address,
            security_cheque_1 = NEW.security_cheque_1,
            security_cheque_2 = NEW.security_cheque_2,
            security_cheque_3 = NEW.security_cheque_3,
            security_cheque_4 = NEW.security_cheque_4,
            security_cheques = NEW.security_cheques,
            jack = COALESCE(NEW.insp_jack, jack),
            jack_rod_tommy = COALESCE(NEW.insp_jack_rod, jack_rod_tommy),
            spanner_pana = COALESCE(NEW.insp_spanner, spanner_pana),
            stepney_tyre = COALESCE(NEW.insp_stepney, stepney_tyre),
            parking_triangle = COALESCE(NEW.insp_parking_triangle, parking_triangle),
            fire_extinguishers = COALESCE(NEW.insp_fire_extinguishers, fire_extinguishers),
            floor_carpet = COALESCE(NEW.insp_floor_carpet, floor_carpet),
            seat_cover = COALESCE(NEW.insp_seat_cover, seat_cover),
            music_system = COALESCE(NEW.insp_music_system, music_system),
            insp_remarks = NEW.insp_remarks,
            old_vehicle_number = LEFT(NEW.old_vehicle_number, 50),
            dropoff_odometer = NEW.dropoff_odometer,
            dropoff_remarks = NEW.dropoff_remarks,
            dropoff_photo = NEW.dropoff_photo,
            dropoff_location = LEFT(NEW.dropoff_location, 50),
            manual_dropoff_location = NEW.manual_dropoff_location,
            jama_form_filled = NEW.jama_form_filled,
            pdi_completed = NEW.pdi_completed,
            ret_jack = LEFT(NEW.ret_jack, 30),
            ret_jack_rod = LEFT(NEW.ret_jack_rod, 30),
            ret_spanner = LEFT(NEW.ret_spanner, 30),
            ret_parking_triangle = LEFT(NEW.ret_parking_triangle, 30),
            ret_fire_extinguishers = LEFT(NEW.ret_fire_extinguishers, 30),
            ret_seat_cover = LEFT(NEW.ret_seat_cover, 30),
            ret_floor_carpet = LEFT(NEW.ret_floor_carpet, 30),
            ret_music_system = LEFT(NEW.ret_music_system, 30),
            ret_insp_remarks = NEW.ret_insp_remarks,
            status = COALESCE(LEFT(NEW.status, 50), status),
            created_by = COALESCE(NEW.created_by, created_by),
            updated_by = COALESCE(NEW.updated_by, updated_by),
            current_approver_id = NEW.current_approver_id,
            approval_status = LEFT(NEW.approval_status, 50),
            approved_by = NEW.approved_by,
            approval_remarks = NEW.approval_remarks,
            odometer_reading = COALESCE(v_odo_val, odometer_reading),
            event_date_time = COALESCE(v_event_ts, event_date_time),
            is_deleted = FALSE,
            deleted_at = NULL,
            updated_at = v_updated_ts
        WHERE id = v_existing_id;

    ELSE
        -- Record does not exist: insert new with MAX(id) + 1
        SELECT COALESCE(MAX(id), 0) + 1 INTO v_next_id FROM public.core_vehicle_allocation;

        INSERT INTO public.core_vehicle_allocation (
            id, source_origin, sheet_record_id, portal_record_id,
            allocation_date, vehicle_number, partner_id, driver_phone, driver_name,
            city, allocation_type, sub_type, car_model, hub_name,
            driver_plan, type_of_plan, rental_plan, partner_type,
            odometer_reading, ola_negative_balance, ola_negative_balance_proof,
            fastag_balance_amount, fastag_balance_proof, damage_penalty, deposit_refund_status, pending_dues, gps_active, duplicate_key_status,
            driver_agreement_doc, photo_front_side, photo_back_side, photo_lh_side, photo_rh_side, vehicle_driver_photo, battery_photo, odometer_photo, police_verification_doc, insp_stepney_photo, customer_address,
            security_cheque_1, security_cheque_2, security_cheque_3, security_cheque_4, security_cheques,
            jack, jack_rod_tommy, spanner_pana, stepney_tyre, parking_triangle, fire_extinguishers, floor_carpet, seat_cover, music_system, insp_remarks,
            old_vehicle_number, dropoff_odometer, dropoff_remarks, dropoff_photo, dropoff_location, manual_dropoff_location, jama_form_filled, pdi_completed,
            ret_jack, ret_jack_rod, ret_spanner, ret_parking_triangle, ret_fire_extinguishers, ret_seat_cover, ret_floor_carpet, ret_music_system, ret_insp_remarks,
            status, created_by, updated_by, current_approver_id, approval_status, approved_by, approval_remarks,
            reason_to_visit, vehicle_manager_poc, submitter_email, sheet_row_number,
            submission_timestamp, event_date_time, is_deleted, deleted_at, created_at, updated_at
        ) VALUES (
            v_next_id, 'PORTAL_FORM', NULL, NEW.id,
            NEW.allocation_date, v_clean_vnum, v_norm_partner_id, v_clean_phone, v_clean_name,
            v_clean_city, v_clean_alloc_type, LEFT(NEW.sub_type, 100), LEFT(NEW.car_model, 100), LEFT(NEW.hub_name, 100),
            LEFT(NEW.driver_plan, 100), LEFT(NEW.type_of_plan, 100), NULL, NULL,
            v_odo_val, NEW.ola_negative_balance, NEW.ola_negative_balance_proof,
            NEW.fastag_balance_amount, NEW.fastag_balance_proof, NEW.damage_penalty, LEFT(NEW.deposit_refund_status, 50), NEW.pending_dues, LEFT(NEW.gps_active, 10), LEFT(NEW.duplicate_key_status, 10),
            NEW.driver_agreement_doc, NEW.photo_front_side, NEW.photo_back_side, NEW.photo_lh_side, NEW.photo_rh_side, NEW.vehicle_driver_photo, NEW.battery_photo, NEW.odometer_photo, NEW.police_verification_doc, NEW.insp_stepney_photo, NEW.customer_address,
            NEW.security_cheque_1, NEW.security_cheque_2, NEW.security_cheque_3, NEW.security_cheque_4, NEW.security_cheques,
            NEW.insp_jack, NEW.insp_jack_rod, NEW.insp_spanner, NEW.insp_stepney, NEW.insp_parking_triangle, NEW.insp_fire_extinguishers, NEW.insp_floor_carpet, NEW.insp_seat_cover, NEW.insp_music_system, NEW.insp_remarks,
            LEFT(NEW.old_vehicle_number, 50), NEW.dropoff_odometer, NEW.dropoff_remarks, NEW.dropoff_photo, LEFT(NEW.dropoff_location, 50), NEW.manual_dropoff_location, NEW.jama_form_filled, NEW.pdi_completed,
            LEFT(NEW.ret_jack, 30), LEFT(NEW.ret_jack_rod, 30), LEFT(NEW.ret_spanner, 30), LEFT(NEW.ret_parking_triangle, 30), LEFT(NEW.ret_fire_extinguishers, 30), LEFT(NEW.ret_seat_cover, 30), LEFT(NEW.ret_floor_carpet, 30), LEFT(NEW.ret_music_system, 30), NEW.ret_insp_remarks,
            COALESCE(LEFT(NEW.status, 50), 'Submitted'), NEW.created_by, NEW.updated_by, NEW.current_approver_id, LEFT(NEW.approval_status, 50), NEW.approved_by, NEW.approval_remarks,
            NULL, NULL, NULL, NULL,
            NULL, v_event_ts, FALSE, NULL, v_created_ts, v_updated_ts
        );

        PERFORM setval('public.core_vehicle_allocation_id_seq', v_next_id, true);
    END IF;

    EXCEPTION WHEN OTHERS THEN
        -- Fail-safe Exception Shield: Guarantees that source table portal_allocation_form operations NEVER fail
        RAISE WARNING 'core_vehicle_allocation sync warning for portal_allocation_form: %', SQLERRM;
    END;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$function$
;

-- -----------------------------------------------------------------------------
-- FUNCTION: fn_sync_portal_partner_adjustment (original: fn_sync_july_partner_adjustment)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.fn_sync_portal_partner_adjustment()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_clean_phone TEXT;
    v_clean_veh TEXT;
    v_clean_city TEXT;
    v_partner_id TEXT;
    v_adj_date DATE;
    v_amount NUMERIC(12,2);
    v_status TEXT;
    v_existing_id BIGINT;
    v_next_id BIGINT;
BEGIN
    IF TG_OP = 'DELETE' THEN
        UPDATE public.core_adjustments
        SET is_deleted = TRUE, 
            deleted_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'), 
            updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
        WHERE adjustment_id = 'ADJ-PORTAL-' || OLD.id::TEXT;
        RETURN OLD;
    END IF;

    v_clean_phone := RIGHT(REGEXP_REPLACE(COALESCE(NEW.partner_number, ''), '[^0-9]', '', 'g'), 10);
    v_clean_veh := UPPER(REGEXP_REPLACE(COALESCE(NEW.vehicle_number, ''), '[^A-Za-z0-9]', '', 'g'));
    v_clean_city := COALESCE(NEW.city_name, 'Bengaluru');
    v_partner_id := COALESCE(NEW.driver_id, NEW.partner_code, public.fn_adj_canonical_partner_id(v_clean_city, v_clean_phone));
    
    v_adj_date := COALESCE(
        CASE 
            WHEN NEW.adjustment_date ~ '^\d{4}-\d{2}-\d{2}' THEN NEW.adjustment_date::DATE
            WHEN NEW.adjustment_date ~ '^\d{2}/\d{2}/\d{4}' THEN TO_DATE(NEW.adjustment_date, 'DD/MM/YYYY')
            ELSE NULL
        END,
        NEW.created_at::DATE,
        CURRENT_DATE
    );

    v_amount := COALESCE(NULLIF(REGEXP_REPLACE(COALESCE(NEW.enter_amount, ''), '[^0-9.]', '', 'g'), '')::NUMERIC, 0.00);
    v_status := public.fn_standardize_approval_status(COALESCE(NEW.approval_status, NEW.status), 'Pending');

    PERFORM pg_advisory_xact_lock(777333444);

    SELECT id INTO v_existing_id
    FROM public.core_adjustments
    WHERE adjustment_id = 'ADJ-PORTAL-' || NEW.id::TEXT;

    IF v_existing_id IS NOT NULL THEN
        UPDATE public.core_adjustments
        SET
            partner_id = v_partner_id,
            partner_name = NEW.partner_name,
            partner_phone = v_clean_phone,
            partner_type = COALESCE(NEW.partner_type, 'Individual'),
            vehicle_number = NEW.vehicle_number,
            city_name = COALESCE(NEW.city_name, 'Bengaluru'),
            adjustment_type = COALESCE(NEW.adjustment_type, 'Credit'),
            adjustment_nature = COALESCE(NEW.adjustment_nature, 'Monetary'),
            adjustment_level = COALESCE(NEW.adjustment_level, 'Driver'),
            adjustment_date = v_adj_date,
            amount = v_amount,
            remittance_towards = NEW.remittance_towards,
            adjustment_related_to = NEW.adjustment_related_to,
            hisaab_number = NEW.hisaab_number,
            contested_line_items = CASE WHEN NEW.contested_line_items IS NOT NULL AND NEW.contested_line_items != '' AND NEW.contested_line_items != 'nan' THEN NEW.contested_line_items::JSONB ELSE core_adjustments.contested_line_items END,
            severity_level = NEW.severity_level,
            cost_level = NEW.cost_level,
            remarks = NEW.remarks,
            approval_status = v_status,
            first_level_approver = NEW.first_level_approval_by,
            final_level_approver = NEW.final_level_approval_by,
            current_approver_id = NEW.current_approver_id::TEXT,
            approved_by = NEW.approved_by::TEXT,
            photo_url = NEW.photo,
            data_source = 'PORTAL_FORM',
            source_reference_id = 'ADJ-PORTAL-' || NEW.id::TEXT,
            is_deleted = FALSE,
            deleted_at = NULL,
            updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
        WHERE id = v_existing_id;
    ELSE
        SELECT COALESCE(MAX(id), 0) + 1 INTO v_next_id FROM public.core_adjustments;

        INSERT INTO public.core_adjustments (
            id, adjustment_id, partner_id, partner_name, partner_phone, partner_type,
            vehicle_number, city_name, adjustment_type, adjustment_nature, adjustment_level,
            adjustment_date, amount, remittance_towards, adjustment_related_to,
            hisaab_number, contested_line_items, severity_level, cost_level,
            remarks, approval_status, first_level_approver, final_level_approver,
            current_approver_id, approved_by, photo_url,
            data_source, source_reference_id, is_deleted, created_at, updated_at
        ) VALUES (
            v_next_id,
            'ADJ-PORTAL-' || NEW.id::TEXT,
            v_partner_id,
            NEW.partner_name,
            v_clean_phone,
            COALESCE(NEW.partner_type, 'Individual'),
            NEW.vehicle_number,
            COALESCE(NEW.city_name, 'Bengaluru'),
            COALESCE(NEW.adjustment_type, 'Credit'),
            COALESCE(NEW.adjustment_nature, 'Monetary'),
            COALESCE(NEW.adjustment_level, 'Driver'),
            v_adj_date,
            v_amount,
            NEW.remittance_towards,
            NEW.adjustment_related_to,
            NEW.hisaab_number,
            CASE WHEN NEW.contested_line_items IS NOT NULL AND NEW.contested_line_items != '' AND NEW.contested_line_items != 'nan' THEN NEW.contested_line_items::JSONB ELSE NULL END,
            NEW.severity_level,
            NEW.cost_level,
            NEW.remarks,
            v_status,
            NEW.first_level_approval_by,
            NEW.final_level_approval_by,
            NEW.current_approver_id::TEXT,
            NEW.approved_by::TEXT,
            NEW.photo,
            'PORTAL_FORM',
            'ADJ-PORTAL-' || NEW.id::TEXT,
            FALSE,
            (COALESCE(NEW.created_at, CURRENT_TIMESTAMP) AT TIME ZONE 'Asia/Kolkata'),
            (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
        );

        PERFORM setval('public.core_adjustments_id_seq', v_next_id, true);
    END IF;

    RETURN NEW;
END;
$function$
;

-- -----------------------------------------------------------------------------
-- FUNCTION: fn_sync_core_maintenance_from_portal_out (original: fn_sync_core_maintenance_from_portal_out)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.fn_sync_core_maintenance_from_portal_out()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_out_dt TIMESTAMP WITHOUT TIME ZONE;
    v_end_date DATE;
    v_inv_date DATE;
    v_inv_amt NUMERIC(12, 2);
    v_ins_disc NUMERIC(12, 2);
    v_payable NUMERIC(12, 2);
    v_out_kms INTEGER;
    v_in_kms INTEGER;
    v_veh VARCHAR(50);
    v_start_date DATE;
    v_attrs JSONB;
BEGIN
    IF TG_OP = 'DELETE' THEN
        -- Revert outward details on core_maintenance row
        UPDATE public.core_maintenance SET
            portal_maintenance_out_id = NULL,
            end_date = NULL,
            out_date_time = NULL,
            out_kms = NULL,
            invoice_no = NULL,
            invoice_date = NULL,
            invoice_amount = 0.00,
            insurance_liability_discounts = 0.00,
            letzryd_payable = 0.00,
            type_of_payment = NULL,
            payment_status = NULL,
            utr_no = NULL,
            outward_photos = NULL,
            invoice_file = NULL,
            maintenance_status = 'IN_PROGRESS',
            updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
        WHERE portal_maintenance_in_id = OLD.inward_id;
        RETURN OLD;
    END IF;

    v_out_dt := public.fn_parse_maintenance_timestamp(NEW.vehicle_out_date_time);
    v_end_date := COALESCE(public.fn_parse_maintenance_date(NEW.rfd_date), v_out_dt::DATE);
    v_out_kms := public.fn_parse_maintenance_int(NEW.vehicle_out_k_m_s);
    v_inv_date := public.fn_parse_maintenance_date(NEW.invoice_date);
    v_inv_amt := public.fn_parse_maintenance_numeric(NEW.invoice_amount);
    v_ins_disc := public.fn_parse_maintenance_numeric(NEW.insurance_liability_discounts);
    v_payable := public.fn_parse_maintenance_numeric(NEW.letzryd_payable);

    -- Lookup intake vehicle and in_kms
    SELECT vehicle_number, start_date, in_kms, extra_attributes 
    INTO v_veh, v_start_date, v_in_kms, v_attrs
    FROM public.core_maintenance 
    WHERE portal_maintenance_in_id = NEW.inward_id;

    IF v_end_date IS NOT NULL AND v_start_date IS NOT NULL AND v_end_date < v_start_date THEN
        v_end_date := v_start_date;
    END IF;

    IF v_in_kms IS NOT NULL AND v_out_kms IS NOT NULL AND v_out_kms < v_in_kms THEN
        v_attrs := jsonb_set(COALESCE(v_attrs, '{}'::jsonb), '{odometer_warning}', to_jsonb(format('Outward odometer (%s) lower than intake odometer (%s)', v_out_kms, v_in_kms)));
    END IF;

    UPDATE public.core_maintenance SET
        portal_maintenance_out_id = NEW.id,
        end_date = v_end_date,
        out_date_time = v_out_dt,
        out_kms = v_out_kms,
        rfd_date = v_end_date,
        maintenance_status = COALESCE(NEW.final_status, 'Completed & RFD'),
        invoice_no = NEW.invoice_no,
        invoice_date = v_inv_date,
        invoice_amount = v_inv_amt,
        insurance_liability_discounts = v_ins_disc,
        letzryd_payable = v_payable,
        type_of_payment = NEW.type_of_payment,
        payment_status = NEW.payment_status,
        utr_no = NEW.utr_no,
        approved_by = COALESCE(approved_by, NEW.approved_by),
        approval_date = COALESCE(approval_date, public.fn_parse_maintenance_date(NEW.approval_date)),
        approval_file = COALESCE(approval_file, NEW.approval_file),
        outward_photos = NEW.vehicle_out_photos,
        invoice_file = NEW.invoice_file,
        partner_name = COALESCE(partner_name, NEW.partner_name, NEW.driver_name),
        partner_ids = COALESCE(partner_ids, NEW.partner_id, NEW.driver_id),
        extra_attributes = COALESCE(v_attrs, extra_attributes),
        updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')
    WHERE portal_maintenance_in_id = NEW.inward_id;

    -- If vehicle has subsequent sheet records between start and end date, ensure they are marked superseded
    IF v_veh IS NOT NULL AND v_start_date IS NOT NULL AND v_end_date IS NOT NULL THEN
        UPDATE public.core_maintenance
        SET is_deleted = TRUE,
            deleted_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'),
            updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata'),
            extra_attributes = jsonb_set(COALESCE(extra_attributes, '{}'::jsonb), '{superseded_by_portal}', to_jsonb(NEW.inward_id))
        WHERE vehicle_number = v_veh
          AND source_type = 'GOOGLE_SHEET'
          AND is_deleted = FALSE
          AND start_date BETWEEN v_start_date AND v_end_date;
    END IF;

    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'fn_sync_core_maintenance_from_portal_out error shielded: % (SQLSTATE: %). Source table operation unaffected.', SQLERRM, SQLSTATE;
    RETURN COALESCE(NEW, OLD);
END;
$function$
;


-- =============================================================================
-- SECTION 3: RE-ATTACH REAL-TIME TRIGGERS ON PORTAL TABLES
-- =============================================================================

DO $$
BEGIN
    -- 1. Portal Form Onboarding Sync Trigger
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'portal_form_onboarding') THEN
        DROP TRIGGER IF EXISTS trg_july_form_onboarding_sync ON public.portal_form_onboarding;
        DROP TRIGGER IF EXISTS trg_portal_form_onboarding_sync ON public.portal_form_onboarding;
        CREATE TRIGGER trg_portal_form_onboarding_sync
        AFTER INSERT OR UPDATE OR DELETE ON public.portal_form_onboarding
        FOR EACH ROW EXECUTE FUNCTION public.fn_sync_portal_form_onboarding();
        RAISE NOTICE 'SUCCESS: Attached trg_portal_form_onboarding_sync';
    END IF;

    -- 2. Portal Vehicle Dropoffs Sync Trigger
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'portal_vehicle_dropoffs') THEN
        DROP TRIGGER IF EXISTS trg_july_vehicle_dropoffs_sync ON public.portal_vehicle_dropoffs;
        DROP TRIGGER IF EXISTS trg_portal_vehicle_dropoffs_sync ON public.portal_vehicle_dropoffs;
        CREATE TRIGGER trg_portal_vehicle_dropoffs_sync
        AFTER INSERT OR UPDATE OR DELETE ON public.portal_vehicle_dropoffs
        FOR EACH ROW EXECUTE FUNCTION public.fn_sync_portal_vehicle_dropoffs();
        RAISE NOTICE 'SUCCESS: Attached trg_portal_vehicle_dropoffs_sync';
    END IF;

    -- 3. Portal Accidents Registry Sync Trigger
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'portal_accidents_registry') THEN
        DROP TRIGGER IF EXISTS trg_july_accidents_registry_sync ON public.portal_accidents_registry;
        DROP TRIGGER IF EXISTS trg_portal_accidents_registry_sync ON public.portal_accidents_registry;
        CREATE TRIGGER trg_portal_accidents_registry_sync
        AFTER INSERT OR UPDATE OR DELETE ON public.portal_accidents_registry
        FOR EACH ROW EXECUTE FUNCTION public.fn_sync_portal_accidents_registry();
        RAISE NOTICE 'SUCCESS: Attached trg_portal_accidents_registry_sync';
    END IF;

    -- 4. Portal Partner Adjustment Sync Trigger
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'portal_partner_adjustment') THEN
        DROP TRIGGER IF EXISTS trg_july_partner_adjustment_sync ON public.portal_partner_adjustment;
        DROP TRIGGER IF EXISTS trg_portal_partner_adjustment_sync ON public.portal_partner_adjustment;
        CREATE TRIGGER trg_portal_partner_adjustment_sync
        AFTER INSERT OR UPDATE OR DELETE ON public.portal_partner_adjustment
        FOR EACH ROW EXECUTE FUNCTION public.fn_sync_portal_partner_adjustment();
        RAISE NOTICE 'SUCCESS: Attached trg_portal_partner_adjustment_sync';
    END IF;

    -- 5. Portal Allocation Form Sync Trigger
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'portal_allocation_form') THEN
        DROP TRIGGER IF EXISTS trg_sync_core_allocation_from_portal ON public.portal_allocation_form;
        CREATE TRIGGER trg_sync_core_allocation_from_portal
        AFTER INSERT OR UPDATE OR DELETE ON public.portal_allocation_form
        FOR EACH ROW EXECUTE FUNCTION public.sync_core_allocation_from_portal();
        RAISE NOTICE 'SUCCESS: Attached trg_sync_core_allocation_from_portal';
    END IF;

    -- 6. Portal Vehicle Onboarding Sync Trigger
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'portal_vehicle_onboarding') THEN
        DROP TRIGGER IF EXISTS trg_sync_core_veh_from_portal ON public.portal_vehicle_onboarding;
        CREATE TRIGGER trg_sync_core_veh_from_portal
        AFTER INSERT OR UPDATE OR DELETE ON public.portal_vehicle_onboarding
        FOR EACH ROW EXECUTE FUNCTION public.fn_sync_core_vehicle_from_portal();
        RAISE NOTICE 'SUCCESS: Attached trg_sync_core_veh_from_portal';
    END IF;

    -- 7. Portal Walkin New Trigger
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'portal_new_walkins') THEN
        DROP TRIGGER IF EXISTS trg_sync_core_walkin_from_portal_new ON public.portal_new_walkins;
        CREATE TRIGGER trg_sync_core_walkin_from_portal_new
        AFTER INSERT OR UPDATE OR DELETE ON public.portal_new_walkins
        FOR EACH ROW EXECUTE FUNCTION public.fn_sync_core_walkin_from_portal_new();
        RAISE NOTICE 'SUCCESS: Attached trg_sync_core_walkin_from_portal_new';
    END IF;

    -- 8. Portal Walkin Existing Trigger
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'portal_existing_walkins') THEN
        DROP TRIGGER IF EXISTS trg_sync_core_walkin_from_portal_existing ON public.portal_existing_walkins;
        CREATE TRIGGER trg_sync_core_walkin_from_portal_existing
        AFTER INSERT OR UPDATE OR DELETE ON public.portal_existing_walkins
        FOR EACH ROW EXECUTE FUNCTION public.fn_sync_core_walkin_from_portal_existing();
        RAISE NOTICE 'SUCCESS: Attached trg_sync_core_walkin_from_portal_existing';
    END IF;

    -- 9. Portal Maintenance In Trigger
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'portal_maintenance_in') THEN
        DROP TRIGGER IF EXISTS trg_sync_core_maintenance_from_portal_in ON public.portal_maintenance_in;
        CREATE TRIGGER trg_sync_core_maintenance_from_portal_in
        AFTER INSERT OR UPDATE OR DELETE ON public.portal_maintenance_in
        FOR EACH ROW EXECUTE FUNCTION public.fn_sync_core_maintenance_from_portal_in();
        RAISE NOTICE 'SUCCESS: Attached trg_sync_core_maintenance_from_portal_in';
    END IF;

    -- 10. Portal Maintenance Out Trigger
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'portal_maintenance_out') THEN
        DROP TRIGGER IF EXISTS trg_sync_core_maintenance_from_portal_out ON public.portal_maintenance_out;
        CREATE TRIGGER trg_sync_core_maintenance_from_portal_out
        AFTER INSERT OR UPDATE OR DELETE ON public.portal_maintenance_out
        FOR EACH ROW EXECUTE FUNCTION public.fn_sync_core_maintenance_from_portal_out();
        RAISE NOTICE 'SUCCESS: Attached trg_sync_core_maintenance_from_portal_out';
    END IF;
END $$;

-- Backward-compatibility aliases for legacy trigger function names
CREATE OR REPLACE FUNCTION public.fn_sync_july_form_onboarding() RETURNS TRIGGER AS $$
BEGIN
    RETURN public.fn_sync_portal_form_onboarding();
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.fn_sync_july_vehicle_dropoffs() RETURNS TRIGGER AS $$
BEGIN
    RETURN public.fn_sync_portal_vehicle_dropoffs();
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.fn_sync_july_accidents_registry() RETURNS TRIGGER AS $$
BEGIN
    RETURN public.fn_sync_portal_accidents_registry();
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.fn_sync_july_partner_adjustment() RETURNS TRIGGER AS $$
BEGIN
    RETURN public.fn_sync_portal_partner_adjustment();
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- End of Script 02
-- =============================================================================


-- ============================================================================
-- HELPER FUNCTIONS & TRIGGERS (ENSURING DEV/PROD PARITY)
-- ============================================================================

CREATE OR REPLACE FUNCTION public.fn_adj_canonical_partner_id(p_city character varying, p_phone character varying)
 RETURNS character varying
 LANGUAGE plpgsql
 IMMUTABLE
AS $function$
DECLARE
    v_clean_phone VARCHAR(10);
    v_prefix VARCHAR(10);
    v_clean_city VARCHAR(100);
BEGIN
    v_clean_phone := RIGHT(REGEXP_REPLACE(COALESCE(p_phone, ''), '[^0-9]', '', 'g'), 10);
    IF LENGTH(v_clean_phone) < 10 THEN
        v_clean_phone := '0000000000';
    END IF;

    v_clean_city := UPPER(TRIM(COALESCE(p_city, 'BLR')));
    
    v_prefix := CASE 
        WHEN v_clean_city IN ('BANGALORE', 'BENGALURU', 'BLR') THEN 'LETZBLR'
        WHEN v_clean_city IN ('HYDERABAD', 'HYD') THEN 'LETZHYD'
        WHEN v_clean_city IN ('MUMBAI', 'MUM') THEN 'LETZMUM'
        WHEN v_clean_city IN ('PUNE', 'PUN') THEN 'LETZPUN'
        WHEN v_clean_city IN ('DELHI', 'DEL') THEN 'LETZDEL'
        WHEN v_clean_city IN ('CHENNAI', 'CHN') THEN 'LETZCHN'
        ELSE 'LETZ' || UPPER(LEFT(v_clean_city, 3))
    END;

    RETURN v_prefix || v_clean_phone;
END;
$function$;

CREATE OR REPLACE FUNCTION public.fn_sync_dropoff_from_portal()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    NEW.city_name := CASE 
        WHEN LOWER(TRIM(COALESCE(NEW.city_name, ''))) IN ('bangalore', 'bengaluru', 'blr') THEN 'Bangalore'
        WHEN LOWER(TRIM(COALESCE(NEW.city_name, ''))) IN ('hyderabad', 'hyd') THEN 'Hyderabad'
        WHEN LOWER(TRIM(COALESCE(NEW.city_name, ''))) IN ('mumbai', 'mum') THEN 'Mumbai'
        ELSE LEFT(INITCAP(TRIM(COALESCE(NEW.city_name, 'Bangalore'))), 50)
    END;

    NEW.vehicle_number := UPPER(REGEXP_REPLACE(COALESCE(NEW.vehicle_number, ''), '[^A-Za-z0-9]', '', 'g'));
    NEW.pending_dues := COALESCE(NEW.pending_dues, 0.00);
    NEW.damage_penalty := COALESCE(NEW.damage_penalty, 0.00);

    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS trg_sync_dropoff_from_portal ON public.portal_vehicle_dropoffs;
CREATE TRIGGER trg_sync_dropoff_from_portal
BEFORE INSERT OR UPDATE ON public.portal_vehicle_dropoffs
FOR EACH ROW
EXECUTE FUNCTION public.fn_sync_dropoff_from_portal();


CREATE OR REPLACE PROCEDURE public.sp_sync_all_sequences()
LANGUAGE plpgsql
AS $$
DECLARE
    r RECORD;
    v_max BIGINT;
    v_last BIGINT;
    v_fixed INT := 0;
BEGIN
    FOR r IN 
        SELECT 
            s.relname AS seq_name,
            t.relname AS tbl_name,
            a.attname AS col_name
        FROM pg_class s
        JOIN pg_depend d ON d.objid = s.oid
        JOIN pg_class t ON t.oid = d.refobjid
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = d.refobjsubid
        WHERE s.relkind = 'S'
          AND t.relkind = 'r'
          AND s.relnamespace = 'public'::regnamespace
    LOOP
        BEGIN
            EXECUTE format('SELECT COALESCE(MAX(%I), 1) FROM public.%I', r.col_name, r.tbl_name) INTO v_max;
            EXECUTE format('SELECT last_value FROM public.%I', r.seq_name) INTO v_last;
            IF v_last < v_max THEN
                EXECUTE format('SELECT setval(%L, %s, true)', r.seq_name, v_max);
                v_fixed := v_fixed + 1;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            NULL;
        END;
    END LOOP;
END;
$$;
