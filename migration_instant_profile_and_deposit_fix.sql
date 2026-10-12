-- ==============================================================================
-- LETZRYD DATABASE MIGRATION: INSTANT PROFILE CREATION & SECURITY DEPOSIT FIX
-- Database: PostgreSQL 14+ (letzryd_dev / Production)
-- Target Tables: app_drivers, app_operators, app_driver_bank_accounts
-- Source Table: core_partner_onboarding (READ-ONLY, ZERO MODIFICATION TO CORE)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- PART 1: ENSURE PREREQUISITE INDEXES & CONSTRAINTS (IDEMPOTENT)
-- ------------------------------------------------------------------------------
DO $$
BEGIN
    -- 1. Ensure phone UNIQUE constraint on app_drivers
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conrelid = 'public.app_drivers'::regclass 
          AND contype = 'u' 
          AND conname = 'app_drivers_phone_key'
    ) THEN
        ALTER TABLE public.app_drivers ADD CONSTRAINT app_drivers_phone_key UNIQUE (phone);
        RAISE NOTICE 'Added UNIQUE constraint app_drivers_phone_key to app_drivers(phone).';
    END IF;

    -- 2. Ensure phone UNIQUE constraint on app_operators
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conrelid = 'public.app_operators'::regclass 
          AND contype = 'u' 
          AND conname = 'app_operators_phone_key'
    ) THEN
        ALTER TABLE public.app_operators ADD CONSTRAINT app_operators_phone_key UNIQUE (phone);
        RAISE NOTICE 'Added UNIQUE constraint app_operators_phone_key to app_operators(phone).';
    END IF;

    -- 3. Ensure (account_number, ifsc_code) UNIQUE constraint on app_driver_bank_accounts
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conrelid = 'public.app_driver_bank_accounts'::regclass 
          AND contype = 'u' 
          AND conname = 'uq_driver_bank_acc'
    ) THEN
        ALTER TABLE public.app_driver_bank_accounts ADD CONSTRAINT uq_driver_bank_acc UNIQUE (account_number, ifsc_code);
        RAISE NOTICE 'Added UNIQUE constraint uq_driver_bank_acc to app_driver_bank_accounts.';
    END IF;

    -- 4. Correct schema column defaults on app_drivers
    ALTER TABLE public.app_drivers ALTER COLUMN deposit_paid SET DEFAULT 0.00;
    ALTER TABLE public.app_drivers ALTER COLUMN deposit_pending SET DEFAULT 5000.00;
    ALTER TABLE public.app_drivers ALTER COLUMN deposit_total_req SET DEFAULT 5000.00;
END $$;


-- ------------------------------------------------------------------------------
-- PART 2: REAL-TIME AUTOMATION TRIGGER FUNCTION (fn_trg_sync_core_partner_to_app)
-- Fixes:
--  - Instant app_drivers / app_operators row creation upon core_partner_onboarding INSERT.
--  - deposit_total_req = COALESCE(NEW.security_deposit, 5000.00)
--  - deposit_paid = 0.00
--  - deposit_pending = deposit_total_req
--  - On conflict / update: deposit_pending = EXCLUDED.deposit_total_req - COALESCE(app_drivers.deposit_paid, 0.00)
--  - Preserves core_partner_onboarding with 100% read-only integrity.
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.fn_trg_sync_core_partner_to_app()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $function$
DECLARE
    v_clean_phone VARCHAR(15);
    v_req_deposit NUMERIC(10,2);
BEGIN
    -- 1. SOFT DELETION HANDLER
    IF TG_OP = 'DELETE' THEN
        v_clean_phone := RIGHT(REGEXP_REPLACE(COALESCE(OLD.phone_number, ''), '[^0-9]', '', 'g'), 10);
        UPDATE public.app_drivers SET is_active = FALSE WHERE phone = v_clean_phone;
        UPDATE public.app_operators SET is_active = FALSE WHERE phone = v_clean_phone;
        RETURN OLD;
    END IF;

    -- 2. PHONE NORMALIZATION
    v_clean_phone := RIGHT(REGEXP_REPLACE(COALESCE(NEW.phone_number, ''), '[^0-9]', '', 'g'), 10);
    
    -- Filter invalid numbers
    IF LENGTH(v_clean_phone) = 10 AND v_clean_phone NOT IN ('0000000000', '1234567890') THEN
        
        -- 3. FLEET OPERATOR ROUTING
        IF NEW.onboarding_type ILIKE '%operator%' OR NEW.partner_id ILIKE '%OP%' OR NEW.partner_id ILIKE '%IP%' THEN
            v_req_deposit := COALESCE(NULLIF(NEW.security_deposit, 0.00), 10000.00);

            INSERT INTO public.app_operators (
                operator_id, operator_code, phone, company_name, contact_person_name, initials,
                address, deposit_total_req, deposit_paid, deposit_pending, upi_id, is_active, last_synced_at
            ) VALUES (
                NEW.id,
                COALESCE(NULLIF(TRIM(NEW.partner_id), ''), 'OPR-' || NEW.id::text),
                v_clean_phone,
                TRIM(COALESCE(NEW.driver_name, 'Fleet Operator')),
                TRIM(COALESCE(NEW.driver_name, 'Fleet Operator')),
                UPPER(SUBSTRING(TRIM(COALESCE(NEW.driver_name, 'OP')), 1, 2)),
                COALESCE(NULLIF(TRIM(NEW.permanent_address), ''), NULLIF(TRIM(NEW.present_address), '')),
                v_req_deposit,
                0.00,
                v_req_deposit,
                COALESCE(NULLIF(TRIM(NEW.upi_id), ''), v_clean_phone || '@upi'),
                CASE WHEN NEW.is_deleted = TRUE THEN FALSE ELSE TRUE END,
                NOW()
            )
            ON CONFLICT (phone) DO UPDATE SET
                company_name = EXCLUDED.company_name,
                contact_person_name = EXCLUDED.contact_person_name,
                is_active = EXCLUDED.is_active,
                deposit_total_req = EXCLUDED.deposit_total_req,
                deposit_pending = EXCLUDED.deposit_total_req - COALESCE(app_operators.deposit_paid, 0.00),
                last_synced_at = NOW();

        -- 4. INDIVIDUAL DRIVER ROUTING
        ELSE
            v_req_deposit := COALESCE(NEW.security_deposit, 5000.00);

            INSERT INTO public.app_drivers (
                driver_id, full_name, phone, initials, driver_code, aadhar_number, dob, address,
                joined_date, emergency_name, emergency_relation, emergency_phone, dl_number, dl_expiry,
                deposit_total_req, deposit_paid, deposit_pending, operator_id, upi_id, is_active, last_synced_at
            ) VALUES (
                NEW.id,
                TRIM(COALESCE(NEW.driver_name, 'Driver')),
                v_clean_phone,
                UPPER(SUBSTRING(TRIM(COALESCE(NEW.driver_name, 'DR')), 1, 2)),
                COALESCE(NULLIF(TRIM(NEW.partner_id), ''), 'DRV-' || NEW.id::text),
                NULLIF(TRIM(NEW.aadhaar_number), ''),
                CASE 
                    WHEN EXTRACT(YEAR FROM NEW.dob) = 21992 THEN MAKE_DATE(1992, EXTRACT(MONTH FROM NEW.dob)::int, EXTRACT(DAY FROM NEW.dob)::int)
                    WHEN EXTRACT(YEAR FROM NEW.dob) NOT BETWEEN 1920 AND 2026 THEN NULL
                    ELSE NEW.dob
                END,
                COALESCE(NULLIF(TRIM(NEW.permanent_address), ''), NULLIF(TRIM(NEW.present_address), '')),
                COALESCE(NEW.onboarding_timestamp::DATE, NEW.created_at::DATE, CURRENT_DATE),
                NULLIF(TRIM(NEW.emergency_name), ''),
                NULLIF(TRIM(NEW.emergency_relationship), ''),
                RIGHT(REGEXP_REPLACE(COALESCE(NEW.emergency_phone, ''), '[^0-9]', '', 'g'), 10),
                NULLIF(TRIM(NEW.dl_number), ''),
                CASE 
                    WHEN EXTRACT(YEAR FROM NEW.dl_expiry_date) BETWEEN 20 AND 99 THEN MAKE_DATE(2000 + EXTRACT(YEAR FROM NEW.dl_expiry_date)::int, EXTRACT(MONTH FROM NEW.dl_expiry_date)::int, EXTRACT(DAY FROM NEW.dl_expiry_date)::int)
                    WHEN EXTRACT(YEAR FROM NEW.dl_expiry_date) NOT BETWEEN 2000 AND 2099 THEN NULL
                    ELSE NEW.dl_expiry_date
                END,
                v_req_deposit,
                0.00,
                v_req_deposit,
                0,
                COALESCE(NULLIF(TRIM(NEW.upi_id), ''), v_clean_phone || '@upi'),
                CASE WHEN NEW.is_deleted = TRUE THEN FALSE ELSE TRUE END,
                NOW()
            )
            ON CONFLICT (phone) DO UPDATE SET
                driver_id = COALESCE(app_drivers.driver_id, EXCLUDED.driver_id),
                driver_code = COALESCE(NULLIF(TRIM(NEW.partner_id), ''), EXCLUDED.driver_code, app_drivers.driver_code),
                operator_id = 0,
                full_name = EXCLUDED.full_name,
                aadhar_number = EXCLUDED.aadhar_number,
                dl_number = EXCLUDED.dl_number,
                dl_expiry = EXCLUDED.dl_expiry,
                is_active = EXCLUDED.is_active,
                deposit_total_req = EXCLUDED.deposit_total_req,
                deposit_pending = EXCLUDED.deposit_total_req - COALESCE(app_drivers.deposit_paid, 0.00),
                last_synced_at = NOW();
        END IF;

        -- 5. IMPS / UPI BANK BENEFICIARY LINKAGE
        IF NULLIF(TRIM(NEW.account_number), '') IS NOT NULL AND NULLIF(TRIM(NEW.ifsc_code), '') IS NOT NULL THEN
            INSERT INTO public.app_driver_bank_accounts (
                app_driver_id, app_operator_id, account_number, ifsc_code, account_holder_name, bank_name, upi_id
            )
            SELECT 
                d.app_driver_id,
                op.app_operator_id,
                SUBSTRING(TRIM(NEW.account_number), 1, 100),
                SUBSTRING(UPPER(TRIM(NEW.ifsc_code)), 1, 100),
                SUBSTRING(TRIM(COALESCE(NEW.account_name, NEW.driver_name, 'Account Holder')), 1, 150),
                SUBSTRING(TRIM(COALESCE(NEW.bank_name, 'Bank')), 1, 150),
                COALESCE(NULLIF(TRIM(NEW.upi_id), ''), v_clean_phone || '@upi')
            FROM (SELECT 1) _
            LEFT JOIN public.app_drivers d ON d.phone = v_clean_phone
            LEFT JOIN public.app_operators op ON op.phone = v_clean_phone
            WHERE d.app_driver_id IS NOT NULL OR op.app_operator_id IS NOT NULL
            ON CONFLICT (account_number, ifsc_code) DO NOTHING;
        END IF;
    END IF;

    RETURN NEW;
END;
$function$;

-- Ensure trigger is active on core_partner_onboarding
DROP TRIGGER IF EXISTS trg_sync_core_partner_to_app ON public.core_partner_onboarding;
CREATE TRIGGER trg_sync_core_partner_to_app
AFTER INSERT OR UPDATE OR DELETE ON public.core_partner_onboarding
FOR EACH ROW EXECUTE FUNCTION public.fn_trg_sync_core_partner_to_app();


-- ------------------------------------------------------------------------------
-- PART 3: OPTIONAL BACKFILL RECONCILIATION FOR HISTORICAL ERRONEOUS RECORDS
-- Resets deposit_paid = 0.00 and deposit_pending = deposit_total_req for onboarded
-- profiles where deposit_paid was previously set equal to deposit_total_req without
-- any actual payment having occurred.
-- Excludes seed test driver records (IDs 1-6) and seed operators (IDs 0-2).
-- ------------------------------------------------------------------------------
-- UPDATE public.app_drivers
-- SET 
--     deposit_paid = 0.00,
--     deposit_pending = COALESCE(deposit_total_req, 5000.00),
--     last_synced_at = NOW()
-- WHERE app_driver_id > 6
--   AND deposit_paid = deposit_total_req 
--   AND deposit_pending = 0.00;

-- UPDATE public.app_operators
-- SET 
--     deposit_paid = 0.00,
--     deposit_pending = COALESCE(deposit_total_req, 10000.00),
--     last_synced_at = NOW()
-- WHERE app_operator_id > 2
--   AND deposit_paid = deposit_total_req 
--   AND deposit_pending = 0.00;
