-- =============================================================================
-- LETZRYD DATABASE MIGRATION SCRIPT 04: CLEANUP DROP BRIDGE VIEWS
-- =============================================================================
-- WARNING:
--   DO NOT RUN THIS SCRIPT IMMEDIATELY AFTER MIGRATION!
--
-- When to Run:
--   Run this script 1 to 2 weeks AFTER all GitHub repositories, Cloud Run
--   services, ETL pipelines, and API endpoints have been completely deployed
--   and verified to be querying 'portal_*' directly.
--
-- Purpose:
--   Permanently removes all temporary backward-compatibility 'july_*' views.
-- =============================================================================

BEGIN;

DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
        SELECT table_name 
        FROM information_schema.views 
        WHERE table_schema = 'public' 
          AND (table_name LIKE 'july_%' OR table_name LIKE 'z_july_%')
    ) LOOP
        EXECUTE 'DROP VIEW IF EXISTS public.' || quote_ident(r.table_name) || ' CASCADE;';
        RAISE NOTICE 'Dropped bridge view: public.%', r.table_name;
    END LOOP;
END $$;

COMMIT;

\echo 'SUCCESS: All temporary bridge views have been dropped.'
