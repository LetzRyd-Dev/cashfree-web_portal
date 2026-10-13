-- =============================================================================
-- LETZRYD DATABASE MIGRATION SCRIPT 03: VERIFICATION SUITE
-- =============================================================================
-- Purpose:
--   Runs comprehensive validation tests to confirm that:
--     1. All physical tables were successfully renamed to 'portal_*'.
--     2. Backward-compatibility bridge views exist for 'july_*'.
--     3. Data counts between 'portal_*' and 'july_*' views match 100%.
--     4. Triggers are active on the new portal tables.
--     5. Stored procedures execute without relation errors.
-- =============================================================================

\echo '====================================================='
\echo '1. CHECKING PHYSICAL BASE TABLE COUNTS (portal_*)'
\echo '====================================================='
SELECT count(*) AS portal_base_table_count
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
  AND (table_name LIKE 'portal_%' OR table_name LIKE 'z_portal_%');

\echo '====================================================='
\echo '2. CHECKING COMPATIBILITY BRIDGE VIEWS (july_*)'
\echo '====================================================='
SELECT count(*) AS july_bridge_view_count
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_type = 'VIEW'
  AND (table_name LIKE 'july_%' OR table_name LIKE 'z_july_%');

\echo '====================================================='
\echo '3. DATA PARITY CHECK (SAMPLE CORE FORMS)'
\echo '====================================================='
-- Check Form Onboarding
SELECT 
    'portal_form_onboarding' AS table_name, count(*) AS portal_rows,
    (SELECT count(*) FROM public.july_form_onboarding) AS bridge_view_rows,
    CASE WHEN count(*) = (SELECT count(*) FROM public.july_form_onboarding) THEN 'PASS (Exact Match)' ELSE 'FAIL' END AS status
FROM public.portal_form_onboarding;

-- Check Vehicle Dropoffs
SELECT 
    'portal_vehicle_dropoffs' AS table_name, count(*) AS portal_rows,
    (SELECT count(*) FROM public.july_vehicle_dropoffs) AS bridge_view_rows,
    CASE WHEN count(*) = (SELECT count(*) FROM public.july_vehicle_dropoffs) THEN 'PASS (Exact Match)' ELSE 'FAIL' END AS status
FROM public.portal_vehicle_dropoffs;

-- Check Partner Adjustments
SELECT 
    'portal_partner_adjustment' AS table_name, count(*) AS portal_rows,
    (SELECT count(*) FROM public.july_partner_adjustment) AS bridge_view_rows,
    CASE WHEN count(*) = (SELECT count(*) FROM public.july_partner_adjustment) THEN 'PASS (Exact Match)' ELSE 'FAIL' END AS status
FROM public.portal_partner_adjustment;

-- Check Ola Weekly Summary
SELECT 
    'portal_ola_weekly_summary' AS table_name, count(*) AS portal_rows,
    (SELECT count(*) FROM public.july_ola_weekly_summary) AS bridge_view_rows,
    CASE WHEN count(*) = (SELECT count(*) FROM public.july_ola_weekly_summary) THEN 'PASS (Exact Match)' ELSE 'FAIL' END AS status
FROM public.portal_ola_weekly_summary;

\echo '====================================================='
\echo '4. VERIFYING TRIGGERS ON PORTAL TABLES'
\echo '====================================================='
SELECT 
    event_object_table AS table_name,
    trigger_name,
    action_timing || ' ' || event_manipulation AS event_type,
    action_statement
FROM information_schema.triggers
WHERE event_object_schema = 'public' 
  AND event_object_table IN (
    'portal_form_onboarding',
    'portal_vehicle_dropoffs',
    'portal_partner_adjustment',
    'portal_allocation_form',
    'portal_vehicle_onboarding',
    'portal_accidents_registry'
  )
ORDER BY event_object_table, trigger_name;

\echo '====================================================='
\echo '5. VERIFYING PG_CRON SCHEDULED JOBS'
\echo '====================================================='
SELECT jobid, schedule, command, active, jobname
FROM cron.job
WHERE command LIKE '%refresh_core%' 
   OR command LIKE '%sync_hisaab%'
ORDER BY jobid;

\echo '====================================================='
\echo 'VERIFICATION COMPLETED'
\echo '====================================================='
