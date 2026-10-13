-- =============================================================================
-- LETZRYD DATABASE MIGRATION SCRIPT 01: RENAME TABLES & CREATE BRIDGE VIEWS
-- =============================================================================
-- Purpose:
--   Renames all 55 physical tables prefixed with 'july_' (and 'z_july_') to 'portal_'
--   and immediately creates updatable compatibility bridge views under the old names.
--
-- Why This Is Zero-Downtime:
--   Existing backend services, Cloud Run endpoints, and pg_cron jobs querying
--   'july_*' will continue reading and writing through the bridge views without error.
--
-- Supported Environments:
--   - DEV DB  : 34.93.205.164:5432/letzryd_dev
--   - PROD DB : 35.200.196.113:5432/postgres
--
-- Idempotency:
--   Safe to run multiple times. If a table is already renamed, it skips renaming
--   and ensures the bridge view is present.
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- Rename july_accidents_registry -> portal_accidents_registry
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_accidents_registry' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_accidents_registry'
    ) THEN
        ALTER TABLE public.july_accidents_registry RENAME TO portal_accidents_registry;
        RAISE NOTICE 'SUCCESS: Renamed public.july_accidents_registry -> public.portal_accidents_registry';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_accidents_registry' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_accidents_registry already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_accidents_registry' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_accidents_registry AS SELECT * FROM public.portal_accidents_registry';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_accidents_registry -> public.portal_accidents_registry';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_allocation_form -> portal_allocation_form
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_allocation_form' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_allocation_form'
    ) THEN
        ALTER TABLE public.july_allocation_form RENAME TO portal_allocation_form;
        RAISE NOTICE 'SUCCESS: Renamed public.july_allocation_form -> public.portal_allocation_form';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_allocation_form' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_allocation_form already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_allocation_form' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_allocation_form AS SELECT * FROM public.portal_allocation_form';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_allocation_form -> public.portal_allocation_form';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_allocation_form_logs -> portal_allocation_form_logs
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_allocation_form_logs' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_allocation_form_logs'
    ) THEN
        ALTER TABLE public.july_allocation_form_logs RENAME TO portal_allocation_form_logs;
        RAISE NOTICE 'SUCCESS: Renamed public.july_allocation_form_logs -> public.portal_allocation_form_logs';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_allocation_form_logs' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_allocation_form_logs already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_allocation_form_logs' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_allocation_form_logs AS SELECT * FROM public.portal_allocation_form_logs';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_allocation_form_logs -> public.portal_allocation_form_logs';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_app_sessions -> portal_app_sessions
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_app_sessions' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_app_sessions'
    ) THEN
        ALTER TABLE public.july_app_sessions RENAME TO portal_app_sessions;
        RAISE NOTICE 'SUCCESS: Renamed public.july_app_sessions -> public.portal_app_sessions';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_app_sessions' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_app_sessions already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_app_sessions' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_app_sessions AS SELECT * FROM public.portal_app_sessions';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_app_sessions -> public.portal_app_sessions';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_app_users -> portal_app_users
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_app_users' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_app_users'
    ) THEN
        ALTER TABLE public.july_app_users RENAME TO portal_app_users;
        RAISE NOTICE 'SUCCESS: Renamed public.july_app_users -> public.portal_app_users';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_app_users' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_app_users already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_app_users' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_app_users AS SELECT * FROM public.portal_app_users';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_app_users -> public.portal_app_users';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_approval_chain_logs -> portal_approval_chain_logs
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_approval_chain_logs' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_approval_chain_logs'
    ) THEN
        ALTER TABLE public.july_approval_chain_logs RENAME TO portal_approval_chain_logs;
        RAISE NOTICE 'SUCCESS: Renamed public.july_approval_chain_logs -> public.portal_approval_chain_logs';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_approval_chain_logs' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_approval_chain_logs already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_approval_chain_logs' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_approval_chain_logs AS SELECT * FROM public.portal_approval_chain_logs';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_approval_chain_logs -> public.portal_approval_chain_logs';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_cities -> portal_cities
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_cities' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_cities'
    ) THEN
        ALTER TABLE public.july_cities RENAME TO portal_cities;
        RAISE NOTICE 'SUCCESS: Renamed public.july_cities -> public.portal_cities';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_cities' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_cities already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_cities' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_cities AS SELECT * FROM public.portal_cities';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_cities -> public.portal_cities';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_driver_onboarding -> portal_driver_onboarding
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_driver_onboarding' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_driver_onboarding'
    ) THEN
        ALTER TABLE public.july_driver_onboarding RENAME TO portal_driver_onboarding;
        RAISE NOTICE 'SUCCESS: Renamed public.july_driver_onboarding -> public.portal_driver_onboarding';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_driver_onboarding' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_driver_onboarding already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_driver_onboarding' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_driver_onboarding AS SELECT * FROM public.portal_driver_onboarding';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_driver_onboarding -> public.portal_driver_onboarding';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_driver_tickets -> portal_driver_tickets
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_driver_tickets' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_driver_tickets'
    ) THEN
        ALTER TABLE public.july_driver_tickets RENAME TO portal_driver_tickets;
        RAISE NOTICE 'SUCCESS: Renamed public.july_driver_tickets -> public.portal_driver_tickets';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_driver_tickets' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_driver_tickets already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_driver_tickets' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_driver_tickets AS SELECT * FROM public.portal_driver_tickets';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_driver_tickets -> public.portal_driver_tickets';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_driver_users -> portal_driver_users
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_driver_users' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_driver_users'
    ) THEN
        ALTER TABLE public.july_driver_users RENAME TO portal_driver_users;
        RAISE NOTICE 'SUCCESS: Renamed public.july_driver_users -> public.portal_driver_users';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_driver_users' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_driver_users already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_driver_users' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_driver_users AS SELECT * FROM public.portal_driver_users';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_driver_users -> public.portal_driver_users';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_employees -> portal_employees
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_employees' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_employees'
    ) THEN
        ALTER TABLE public.july_employees RENAME TO portal_employees;
        RAISE NOTICE 'SUCCESS: Renamed public.july_employees -> public.portal_employees';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_employees' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_employees already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_employees' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_employees AS SELECT * FROM public.portal_employees';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_employees -> public.portal_employees';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_existing_walkins -> portal_existing_walkins
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_existing_walkins' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_existing_walkins'
    ) THEN
        ALTER TABLE public.july_existing_walkins RENAME TO portal_existing_walkins;
        RAISE NOTICE 'SUCCESS: Renamed public.july_existing_walkins -> public.portal_existing_walkins';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_existing_walkins' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_existing_walkins already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_existing_walkins' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_existing_walkins AS SELECT * FROM public.portal_existing_walkins';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_existing_walkins -> public.portal_existing_walkins';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_fleet_operator_summary -> portal_fleet_operator_summary
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_fleet_operator_summary' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_fleet_operator_summary'
    ) THEN
        ALTER TABLE public.july_fleet_operator_summary RENAME TO portal_fleet_operator_summary;
        RAISE NOTICE 'SUCCESS: Renamed public.july_fleet_operator_summary -> public.portal_fleet_operator_summary';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_fleet_operator_summary' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_fleet_operator_summary already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_fleet_operator_summary' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_fleet_operator_summary AS SELECT * FROM public.portal_fleet_operator_summary';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_fleet_operator_summary -> public.portal_fleet_operator_summary';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_form_onboarding -> portal_form_onboarding
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_form_onboarding' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_form_onboarding'
    ) THEN
        ALTER TABLE public.july_form_onboarding RENAME TO portal_form_onboarding;
        RAISE NOTICE 'SUCCESS: Renamed public.july_form_onboarding -> public.portal_form_onboarding';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_form_onboarding' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_form_onboarding already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_form_onboarding' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_form_onboarding AS SELECT * FROM public.portal_form_onboarding';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_form_onboarding -> public.portal_form_onboarding';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_hisaab_weekly_statement -> portal_hisaab_weekly_statement
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_hisaab_weekly_statement' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_hisaab_weekly_statement'
    ) THEN
        ALTER TABLE public.july_hisaab_weekly_statement RENAME TO portal_hisaab_weekly_statement;
        RAISE NOTICE 'SUCCESS: Renamed public.july_hisaab_weekly_statement -> public.portal_hisaab_weekly_statement';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_hisaab_weekly_statement' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_hisaab_weekly_statement already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_hisaab_weekly_statement' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_hisaab_weekly_statement AS SELECT * FROM public.portal_hisaab_weekly_statement';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_hisaab_weekly_statement -> public.portal_hisaab_weekly_statement';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_hubs_parking -> portal_hubs_parking
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_hubs_parking' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_hubs_parking'
    ) THEN
        ALTER TABLE public.july_hubs_parking RENAME TO portal_hubs_parking;
        RAISE NOTICE 'SUCCESS: Renamed public.july_hubs_parking -> public.portal_hubs_parking';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_hubs_parking' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_hubs_parking already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_hubs_parking' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_hubs_parking AS SELECT * FROM public.portal_hubs_parking';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_hubs_parking -> public.portal_hubs_parking';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_inspections -> portal_inspections
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_inspections' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_inspections'
    ) THEN
        ALTER TABLE public.july_inspections RENAME TO portal_inspections;
        RAISE NOTICE 'SUCCESS: Renamed public.july_inspections -> public.portal_inspections';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_inspections' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_inspections already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_inspections' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_inspections AS SELECT * FROM public.portal_inspections';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_inspections -> public.portal_inspections';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_maintenance_in -> portal_maintenance_in
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_maintenance_in' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_maintenance_in'
    ) THEN
        ALTER TABLE public.july_maintenance_in RENAME TO portal_maintenance_in;
        RAISE NOTICE 'SUCCESS: Renamed public.july_maintenance_in -> public.portal_maintenance_in';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_maintenance_in' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_maintenance_in already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_maintenance_in' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_maintenance_in AS SELECT * FROM public.portal_maintenance_in';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_maintenance_in -> public.portal_maintenance_in';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_maintenance_out -> portal_maintenance_out
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_maintenance_out' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_maintenance_out'
    ) THEN
        ALTER TABLE public.july_maintenance_out RENAME TO portal_maintenance_out;
        RAISE NOTICE 'SUCCESS: Renamed public.july_maintenance_out -> public.portal_maintenance_out';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_maintenance_out' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_maintenance_out already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_maintenance_out' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_maintenance_out AS SELECT * FROM public.portal_maintenance_out';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_maintenance_out -> public.portal_maintenance_out';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_maintenance_registry -> portal_maintenance_registry
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_maintenance_registry' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_maintenance_registry'
    ) THEN
        ALTER TABLE public.july_maintenance_registry RENAME TO portal_maintenance_registry;
        RAISE NOTICE 'SUCCESS: Renamed public.july_maintenance_registry -> public.portal_maintenance_registry';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_maintenance_registry' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_maintenance_registry already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_maintenance_registry' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_maintenance_registry AS SELECT * FROM public.portal_maintenance_registry';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_maintenance_registry -> public.portal_maintenance_registry';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_new_walkins -> portal_new_walkins
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_new_walkins' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_new_walkins'
    ) THEN
        ALTER TABLE public.july_new_walkins RENAME TO portal_new_walkins;
        RAISE NOTICE 'SUCCESS: Renamed public.july_new_walkins -> public.portal_new_walkins';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_new_walkins' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_new_walkins already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_new_walkins' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_new_walkins AS SELECT * FROM public.portal_new_walkins';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_new_walkins -> public.portal_new_walkins';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_notifications -> portal_notifications
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_notifications' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_notifications'
    ) THEN
        ALTER TABLE public.july_notifications RENAME TO portal_notifications;
        RAISE NOTICE 'SUCCESS: Renamed public.july_notifications -> public.portal_notifications';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_notifications' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_notifications already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_notifications' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_notifications AS SELECT * FROM public.portal_notifications';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_notifications -> public.portal_notifications';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_ola_incentive -> portal_ola_incentive
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_ola_incentive' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_ola_incentive'
    ) THEN
        ALTER TABLE public.july_ola_incentive RENAME TO portal_ola_incentive;
        RAISE NOTICE 'SUCCESS: Renamed public.july_ola_incentive -> public.portal_ola_incentive';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_ola_incentive' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_ola_incentive already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_ola_incentive' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_ola_incentive AS SELECT * FROM public.portal_ola_incentive';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_ola_incentive -> public.portal_ola_incentive';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_ola_raw -> portal_ola_raw
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_ola_raw' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_ola_raw'
    ) THEN
        ALTER TABLE public.july_ola_raw RENAME TO portal_ola_raw;
        RAISE NOTICE 'SUCCESS: Renamed public.july_ola_raw -> public.portal_ola_raw';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_ola_raw' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_ola_raw already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_ola_raw' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_ola_raw AS SELECT * FROM public.portal_ola_raw';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_ola_raw -> public.portal_ola_raw';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_ola_weekly_summary -> portal_ola_weekly_summary
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_ola_weekly_summary' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_ola_weekly_summary'
    ) THEN
        ALTER TABLE public.july_ola_weekly_summary RENAME TO portal_ola_weekly_summary;
        RAISE NOTICE 'SUCCESS: Renamed public.july_ola_weekly_summary -> public.portal_ola_weekly_summary';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_ola_weekly_summary' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_ola_weekly_summary already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_ola_weekly_summary' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_ola_weekly_summary AS SELECT * FROM public.portal_ola_weekly_summary';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_ola_weekly_summary -> public.portal_ola_weekly_summary';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_onboarding -> portal_onboarding
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_onboarding' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_onboarding'
    ) THEN
        ALTER TABLE public.july_onboarding RENAME TO portal_onboarding;
        RAISE NOTICE 'SUCCESS: Renamed public.july_onboarding -> public.portal_onboarding';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_onboarding' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_onboarding already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_onboarding' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_onboarding AS SELECT * FROM public.portal_onboarding';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_onboarding -> public.portal_onboarding';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_onboarding_logs -> portal_onboarding_logs
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_onboarding_logs' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_onboarding_logs'
    ) THEN
        ALTER TABLE public.july_onboarding_logs RENAME TO portal_onboarding_logs;
        RAISE NOTICE 'SUCCESS: Renamed public.july_onboarding_logs -> public.portal_onboarding_logs';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_onboarding_logs' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_onboarding_logs already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_onboarding_logs' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_onboarding_logs AS SELECT * FROM public.portal_onboarding_logs';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_onboarding_logs -> public.portal_onboarding_logs';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_operator_users -> portal_operator_users
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_operator_users' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_operator_users'
    ) THEN
        ALTER TABLE public.july_operator_users RENAME TO portal_operator_users;
        RAISE NOTICE 'SUCCESS: Renamed public.july_operator_users -> public.portal_operator_users';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_operator_users' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_operator_users already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_operator_users' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_operator_users AS SELECT * FROM public.portal_operator_users';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_operator_users -> public.portal_operator_users';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_partner_adjustment -> portal_partner_adjustment
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_partner_adjustment' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_partner_adjustment'
    ) THEN
        ALTER TABLE public.july_partner_adjustment RENAME TO portal_partner_adjustment;
        RAISE NOTICE 'SUCCESS: Renamed public.july_partner_adjustment -> public.portal_partner_adjustment';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_partner_adjustment' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_partner_adjustment already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_partner_adjustment' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_partner_adjustment AS SELECT * FROM public.portal_partner_adjustment';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_partner_adjustment -> public.portal_partner_adjustment';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_partner_expenses -> portal_partner_expenses
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_partner_expenses' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_partner_expenses'
    ) THEN
        ALTER TABLE public.july_partner_expenses RENAME TO portal_partner_expenses;
        RAISE NOTICE 'SUCCESS: Renamed public.july_partner_expenses -> public.portal_partner_expenses';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_partner_expenses' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_partner_expenses already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_partner_expenses' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_partner_expenses AS SELECT * FROM public.portal_partner_expenses';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_partner_expenses -> public.portal_partner_expenses';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_permissions -> portal_permissions
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_permissions' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_permissions'
    ) THEN
        ALTER TABLE public.july_permissions RENAME TO portal_permissions;
        RAISE NOTICE 'SUCCESS: Renamed public.july_permissions -> public.portal_permissions';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_permissions' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_permissions already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_permissions' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_permissions AS SELECT * FROM public.portal_permissions';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_permissions -> public.portal_permissions';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_portal_users -> portal_portal_users
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_portal_users' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_portal_users'
    ) THEN
        ALTER TABLE public.july_portal_users RENAME TO portal_portal_users;
        RAISE NOTICE 'SUCCESS: Renamed public.july_portal_users -> public.portal_portal_users';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_portal_users' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_portal_users already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_portal_users' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_portal_users AS SELECT * FROM public.portal_portal_users';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_portal_users -> public.portal_portal_users';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_referrals -> portal_referrals
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_referrals' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_referrals'
    ) THEN
        ALTER TABLE public.july_referrals RENAME TO portal_referrals;
        RAISE NOTICE 'SUCCESS: Renamed public.july_referrals -> public.portal_referrals';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_referrals' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_referrals already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_referrals' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_referrals AS SELECT * FROM public.portal_referrals';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_referrals -> public.portal_referrals';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_rent_ledger -> portal_rent_ledger
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_rent_ledger' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_rent_ledger'
    ) THEN
        ALTER TABLE public.july_rent_ledger RENAME TO portal_rent_ledger;
        RAISE NOTICE 'SUCCESS: Renamed public.july_rent_ledger -> public.portal_rent_ledger';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_rent_ledger' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_rent_ledger already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_rent_ledger' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_rent_ledger AS SELECT * FROM public.portal_rent_ledger';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_rent_ledger -> public.portal_rent_ledger';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_rents -> portal_rents
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_rents' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_rents'
    ) THEN
        ALTER TABLE public.july_rents RENAME TO portal_rents;
        RAISE NOTICE 'SUCCESS: Renamed public.july_rents -> public.portal_rents';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_rents' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_rents already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_rents' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_rents AS SELECT * FROM public.portal_rents';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_rents -> public.portal_rents';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_role_permissions -> portal_role_permissions
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_role_permissions' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_role_permissions'
    ) THEN
        ALTER TABLE public.july_role_permissions RENAME TO portal_role_permissions;
        RAISE NOTICE 'SUCCESS: Renamed public.july_role_permissions -> public.portal_role_permissions';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_role_permissions' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_role_permissions already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_role_permissions' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_role_permissions AS SELECT * FROM public.portal_role_permissions';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_role_permissions -> public.portal_role_permissions';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_roles -> portal_roles
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_roles' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_roles'
    ) THEN
        ALTER TABLE public.july_roles RENAME TO portal_roles;
        RAISE NOTICE 'SUCCESS: Renamed public.july_roles -> public.portal_roles';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_roles' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_roles already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_roles' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_roles AS SELECT * FROM public.portal_roles';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_roles -> public.portal_roles';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_tickets -> portal_tickets
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_tickets' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_tickets'
    ) THEN
        ALTER TABLE public.july_tickets RENAME TO portal_tickets;
        RAISE NOTICE 'SUCCESS: Renamed public.july_tickets -> public.portal_tickets';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_tickets' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_tickets already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_tickets' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_tickets AS SELECT * FROM public.portal_tickets';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_tickets -> public.portal_tickets';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_traffic_challans -> portal_traffic_challans
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_traffic_challans' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_traffic_challans'
    ) THEN
        ALTER TABLE public.july_traffic_challans RENAME TO portal_traffic_challans;
        RAISE NOTICE 'SUCCESS: Renamed public.july_traffic_challans -> public.portal_traffic_challans';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_traffic_challans' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_traffic_challans already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_traffic_challans' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_traffic_challans AS SELECT * FROM public.portal_traffic_challans';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_traffic_challans -> public.portal_traffic_challans';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_user_approval_chain -> portal_user_approval_chain
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_user_approval_chain' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_user_approval_chain'
    ) THEN
        ALTER TABLE public.july_user_approval_chain RENAME TO portal_user_approval_chain;
        RAISE NOTICE 'SUCCESS: Renamed public.july_user_approval_chain -> public.portal_user_approval_chain';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_user_approval_chain' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_user_approval_chain already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_user_approval_chain' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_user_approval_chain AS SELECT * FROM public.portal_user_approval_chain';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_user_approval_chain -> public.portal_user_approval_chain';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_user_form_access -> portal_user_form_access
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_user_form_access' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_user_form_access'
    ) THEN
        ALTER TABLE public.july_user_form_access RENAME TO portal_user_form_access;
        RAISE NOTICE 'SUCCESS: Renamed public.july_user_form_access -> public.portal_user_form_access';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_user_form_access' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_user_form_access already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_user_form_access' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_user_form_access AS SELECT * FROM public.portal_user_form_access';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_user_form_access -> public.portal_user_form_access';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_user_login_logs -> portal_user_login_logs
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_user_login_logs' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_user_login_logs'
    ) THEN
        ALTER TABLE public.july_user_login_logs RENAME TO portal_user_login_logs;
        RAISE NOTICE 'SUCCESS: Renamed public.july_user_login_logs -> public.portal_user_login_logs';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_user_login_logs' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_user_login_logs already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_user_login_logs' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_user_login_logs AS SELECT * FROM public.portal_user_login_logs';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_user_login_logs -> public.portal_user_login_logs';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_user_permission_overrides -> portal_user_permission_overrides
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_user_permission_overrides' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_user_permission_overrides'
    ) THEN
        ALTER TABLE public.july_user_permission_overrides RENAME TO portal_user_permission_overrides;
        RAISE NOTICE 'SUCCESS: Renamed public.july_user_permission_overrides -> public.portal_user_permission_overrides';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_user_permission_overrides' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_user_permission_overrides already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_user_permission_overrides' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_user_permission_overrides AS SELECT * FROM public.portal_user_permission_overrides';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_user_permission_overrides -> public.portal_user_permission_overrides';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_vehicle_dropoffs -> portal_vehicle_dropoffs
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_vehicle_dropoffs' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_vehicle_dropoffs'
    ) THEN
        ALTER TABLE public.july_vehicle_dropoffs RENAME TO portal_vehicle_dropoffs;
        RAISE NOTICE 'SUCCESS: Renamed public.july_vehicle_dropoffs -> public.portal_vehicle_dropoffs';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_vehicle_dropoffs' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_vehicle_dropoffs already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_vehicle_dropoffs' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_vehicle_dropoffs AS SELECT * FROM public.portal_vehicle_dropoffs';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_vehicle_dropoffs -> public.portal_vehicle_dropoffs';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_vehicle_logs -> portal_vehicle_logs
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_vehicle_logs' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_vehicle_logs'
    ) THEN
        ALTER TABLE public.july_vehicle_logs RENAME TO portal_vehicle_logs;
        RAISE NOTICE 'SUCCESS: Renamed public.july_vehicle_logs -> public.portal_vehicle_logs';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_vehicle_logs' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_vehicle_logs already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_vehicle_logs' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_vehicle_logs AS SELECT * FROM public.portal_vehicle_logs';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_vehicle_logs -> public.portal_vehicle_logs';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_vehicle_models -> portal_vehicle_models
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_vehicle_models' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_vehicle_models'
    ) THEN
        ALTER TABLE public.july_vehicle_models RENAME TO portal_vehicle_models;
        RAISE NOTICE 'SUCCESS: Renamed public.july_vehicle_models -> public.portal_vehicle_models';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_vehicle_models' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_vehicle_models already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_vehicle_models' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_vehicle_models AS SELECT * FROM public.portal_vehicle_models';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_vehicle_models -> public.portal_vehicle_models';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_vehicle_onboarding -> portal_vehicle_onboarding
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_vehicle_onboarding' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_vehicle_onboarding'
    ) THEN
        ALTER TABLE public.july_vehicle_onboarding RENAME TO portal_vehicle_onboarding;
        RAISE NOTICE 'SUCCESS: Renamed public.july_vehicle_onboarding -> public.portal_vehicle_onboarding';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_vehicle_onboarding' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_vehicle_onboarding already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_vehicle_onboarding' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_vehicle_onboarding AS SELECT * FROM public.portal_vehicle_onboarding';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_vehicle_onboarding -> public.portal_vehicle_onboarding';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_vehicles -> portal_vehicles
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_vehicles' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_vehicles'
    ) THEN
        ALTER TABLE public.july_vehicles RENAME TO portal_vehicles;
        RAISE NOTICE 'SUCCESS: Renamed public.july_vehicles -> public.portal_vehicles';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_vehicles' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_vehicles already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_vehicles' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_vehicles AS SELECT * FROM public.portal_vehicles';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_vehicles -> public.portal_vehicles';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_walkin_form_links -> portal_walkin_form_links
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_walkin_form_links' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_walkin_form_links'
    ) THEN
        ALTER TABLE public.july_walkin_form_links RENAME TO portal_walkin_form_links;
        RAISE NOTICE 'SUCCESS: Renamed public.july_walkin_form_links -> public.portal_walkin_form_links';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_walkin_form_links' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_walkin_form_links already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_walkin_form_links' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_walkin_form_links AS SELECT * FROM public.portal_walkin_form_links';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_walkin_form_links -> public.portal_walkin_form_links';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_walkin_logs -> portal_walkin_logs
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_walkin_logs' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_walkin_logs'
    ) THEN
        ALTER TABLE public.july_walkin_logs RENAME TO portal_walkin_logs;
        RAISE NOTICE 'SUCCESS: Renamed public.july_walkin_logs -> public.portal_walkin_logs';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_walkin_logs' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_walkin_logs already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_walkin_logs' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_walkin_logs AS SELECT * FROM public.portal_walkin_logs';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_walkin_logs -> public.portal_walkin_logs';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_walkin_onboarding_links -> portal_walkin_onboarding_links
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_walkin_onboarding_links' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_walkin_onboarding_links'
    ) THEN
        ALTER TABLE public.july_walkin_onboarding_links RENAME TO portal_walkin_onboarding_links;
        RAISE NOTICE 'SUCCESS: Renamed public.july_walkin_onboarding_links -> public.portal_walkin_onboarding_links';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_walkin_onboarding_links' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_walkin_onboarding_links already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_walkin_onboarding_links' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_walkin_onboarding_links AS SELECT * FROM public.portal_walkin_onboarding_links';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_walkin_onboarding_links -> public.portal_walkin_onboarding_links';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_walkins -> portal_walkins
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_walkins' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_walkins'
    ) THEN
        ALTER TABLE public.july_walkins RENAME TO portal_walkins;
        RAISE NOTICE 'SUCCESS: Renamed public.july_walkins -> public.portal_walkins';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_walkins' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_walkins already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_walkins' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_walkins AS SELECT * FROM public.portal_walkins';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_walkins -> public.portal_walkins';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename july_workshop_vendors -> portal_workshop_vendors
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'july_workshop_vendors' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_workshop_vendors'
    ) THEN
        ALTER TABLE public.july_workshop_vendors RENAME TO portal_workshop_vendors;
        RAISE NOTICE 'SUCCESS: Renamed public.july_workshop_vendors -> public.portal_workshop_vendors';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_workshop_vendors' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.portal_workshop_vendors already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_workshop_vendors' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.july_workshop_vendors AS SELECT * FROM public.portal_workshop_vendors';
        RAISE NOTICE 'SUCCESS: Created bridge view public.july_workshop_vendors -> public.portal_workshop_vendors';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename z_july_vehicle_onboarding_1 -> z_portal_vehicle_onboarding_1
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'z_july_vehicle_onboarding_1' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'z_portal_vehicle_onboarding_1'
    ) THEN
        ALTER TABLE public.z_july_vehicle_onboarding_1 RENAME TO z_portal_vehicle_onboarding_1;
        RAISE NOTICE 'SUCCESS: Renamed public.z_july_vehicle_onboarding_1 -> public.z_portal_vehicle_onboarding_1';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'z_portal_vehicle_onboarding_1' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.z_portal_vehicle_onboarding_1 already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'z_portal_vehicle_onboarding_1' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.z_july_vehicle_onboarding_1 AS SELECT * FROM public.z_portal_vehicle_onboarding_1';
        RAISE NOTICE 'SUCCESS: Created bridge view public.z_july_vehicle_onboarding_1 -> public.z_portal_vehicle_onboarding_1';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Rename z_july_vehicle_onboarding_1_logs -> z_portal_vehicle_onboarding_1_logs
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'z_july_vehicle_onboarding_1_logs' AND table_type = 'BASE TABLE'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'z_portal_vehicle_onboarding_1_logs'
    ) THEN
        ALTER TABLE public.z_july_vehicle_onboarding_1_logs RENAME TO z_portal_vehicle_onboarding_1_logs;
        RAISE NOTICE 'SUCCESS: Renamed public.z_july_vehicle_onboarding_1_logs -> public.z_portal_vehicle_onboarding_1_logs';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'z_portal_vehicle_onboarding_1_logs' AND table_type = 'BASE TABLE'
    ) THEN
        RAISE NOTICE 'INFO: Target table public.z_portal_vehicle_onboarding_1_logs already exists. Skipping ALTER TABLE.';
    END IF;

    -- Ensure backward-compatible bridge view exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'z_portal_vehicle_onboarding_1_logs' AND table_type = 'BASE TABLE'
    ) THEN
        EXECUTE 'CREATE OR REPLACE VIEW public.z_july_vehicle_onboarding_1_logs AS SELECT * FROM public.z_portal_vehicle_onboarding_1_logs';
        RAISE NOTICE 'SUCCESS: Created bridge view public.z_july_vehicle_onboarding_1_logs -> public.z_portal_vehicle_onboarding_1_logs';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Convenience alias: portal_users -> portal_portal_users
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'portal_portal_users' AND table_type = 'BASE TABLE'
    ) THEN
        CREATE OR REPLACE VIEW public.portal_users AS SELECT * FROM public.portal_portal_users;
        RAISE NOTICE 'SUCCESS: Created convenience alias view public.portal_users -> public.portal_portal_users';
    END IF;
END $$;

COMMIT;
-- =============================================================================
-- End of Script 01
-- =============================================================================
