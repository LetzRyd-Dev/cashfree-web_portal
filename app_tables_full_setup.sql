-- ==============================================================================
-- LETZRYD APP TABLES MASTER SCHEMA, POPULATION ENGINE & AUTOMATION TRIGGERS
-- Target Database: PostgreSQL 14+ on 35.200.196.113:5432/postgres
-- Purpose:
--   1. Ensures all App Tables exist (app_drivers, app_operators, app_hisaabs,
--      app_driver_allocations, app_driver_bank_accounts, app_sessions,
--      app_payments, app_notifications, app_referral_leads, app_audit_logs,
--      app_support_tickets).
--   2. Provides stored procedure `sp_populate_all_app_tables(truncate_first)`
--      to cleanly populate all App Tables from Final Tables & Output Tables.
--   3. Sets up automated real-time triggers on Final & Output Tables to keep
--      App Tables continuously updated upon INSERT, UPDATE, or DELETE.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- PART 0: MIGRATION & COLUMN EXPANSIONS ON EXISTING APP TABLES
-- ------------------------------------------------------------------------------
ALTER TABLE IF EXISTS public.app_hisaabs ALTER COLUMN hisaab_number TYPE VARCHAR(100);
ALTER TABLE IF EXISTS public.app_drivers ALTER COLUMN lw_hisaab_number TYPE VARCHAR(100);
ALTER TABLE IF EXISTS public.app_operators ALTER COLUMN lw_hisaab_number TYPE VARCHAR(100);
ALTER TABLE IF EXISTS public.app_driver_bank_accounts ALTER COLUMN ifsc_code TYPE VARCHAR(100);
ALTER TABLE IF EXISTS public.app_driver_bank_accounts ALTER COLUMN account_number TYPE VARCHAR(100);
ALTER TABLE IF EXISTS public.app_driver_bank_accounts ALTER COLUMN bank_name TYPE VARCHAR(150);

-- ------------------------------------------------------------------------------
-- PART 1: ENSURE ALL APP TABLES & COLUMNS EXIST
-- ------------------------------------------------------------------------------

-- 1.1 TABLE: app_drivers
CREATE TABLE IF NOT EXISTS public.app_drivers (
    app_driver_id                    SERIAL                    PRIMARY KEY,
    driver_id                        INTEGER                   NULL,
    operator_id                      INTEGER                   NULL DEFAULT 1,
    full_name                        VARCHAR(150)              NULL,
    phone                            VARCHAR(15)               NULL UNIQUE,
    profile_photo_url                TEXT                      NULL,
    initials                         VARCHAR(5)                NULL,
    driver_code                      VARCHAR(50)               NULL,
    aadhar_number                    VARCHAR(20)               NULL,
    blood_group                      VARCHAR(5)                NULL,
    dob                              DATE                      NULL,
    address                          TEXT                      NULL,
    joined_date                      DATE                      NULL,
    emergency_name                   VARCHAR(150)              NULL,
    emergency_relation               VARCHAR(50)               NULL,
    emergency_phone                  VARCHAR(15)               NULL,
    dl_number                        VARCHAR(50)               NULL,
    dl_expiry                        DATE                      NULL,
    current_vehicle_id               INTEGER                   NULL,
    current_allocation_id            INTEGER                   NULL,
    vehicle_reg_number               VARCHAR(20)               NULL,
    vehicle_make                     VARCHAR(50)               NULL,
    vehicle_model                    VARCHAR(50)               NULL,
    vehicle_variant                  VARCHAR(50)               NULL,
    vehicle_year                     SMALLINT                  NULL,
    vehicle_color                    VARCHAR(50)               NULL,
    vehicle_fuel_type                VARCHAR(20)               NULL,
    vehicle_odometer_km              INTEGER                   NULL DEFAULT 0,
    vehicle_allocated_from           DATE                      NULL,
    vehicle_daily_rate               NUMERIC(10,2)             NULL DEFAULT 1000.00,
    rc_number                        VARCHAR(50)               NULL,
    rc_expiry                        DATE                      NULL,
    insurance_number                 VARCHAR(50)               NULL,
    insurance_expiry                 DATE                      NULL,
    permit_type                      VARCHAR(50)               NULL,
    permit_number                    VARCHAR(50)               NULL,
    permit_expiry                    DATE                      NULL,
    fitness_number                   VARCHAR(50)               NULL,
    fitness_expiry                   DATE                      NULL,
    puc_expiry                       DATE                      NULL,
    doc_last_updated                 DATE                      NULL,
    deposit_total_req                NUMERIC(10,2)             NULL DEFAULT 5000.00,
    deposit_paid                     NUMERIC(10,2)             NULL DEFAULT 5000.00,
    deposit_pending                  NUMERIC(10,2)             NULL DEFAULT 0.00,
    deposit_next_due                 DATE                      NULL,
    joining_fee_agreed               NUMERIC(10,2)             NULL DEFAULT 1000.00,
    joining_fee_paid                 NUMERIC(10,2)             NULL DEFAULT 1000.00,
    cumulative_owed                  NUMERIC(12,2)             NULL DEFAULT 0.00,
    assigned_manager_name            VARCHAR(150)              NULL,
    assigned_manager_phone           VARCHAR(15)               NULL,
    incentive_trips_target           INTEGER                   NULL DEFAULT 260,
    incentive_reward_amt             NUMERIC(10,2)             NULL DEFAULT 1500.00,
    referral_code                    VARCHAR(30)               NULL UNIQUE,
    referral_reward_amt              NUMERIC(10,2)             NULL DEFAULT 1000.00,
    contract_terms_url               TEXT                      NULL,
    upi_id                           VARCHAR(100)              NULL,
    bank_account_last4               VARCHAR(4)                NULL,
    password_hash                    VARCHAR(255)              NULL,
    fcm_token                        TEXT                      NULL,
    preferred_language               VARCHAR(5)                NULL DEFAULT 'en',
    is_active                        BOOLEAN                   NULL DEFAULT TRUE,
    created_at                       TIMESTAMP WITH TIME ZONE  NULL DEFAULT NOW(),
    last_login_at                    TIMESTAMP WITH TIME ZONE  NULL,
    last_synced_at                   TIMESTAMP WITH TIME ZONE  NULL,
    cw_uber_trips                    INTEGER                   NULL DEFAULT 0,
    cw_uber_revenue                  NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_uber_cash                     NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_uber_toll                     NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_uber_incentive                NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_uber_subscription             NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_uber_km                       NUMERIC(10,2)             NULL DEFAULT 0.00,
    cw_ola_trips                     INTEGER                   NULL DEFAULT 0,
    cw_ola_revenue                   NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_ola_cash                      NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_ola_toll                      NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_ola_incentive                 NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_ola_subscription              NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_ola_km                        NUMERIC(10,2)             NULL DEFAULT 0.00,
    cw_rapido_trips                  INTEGER                   NULL DEFAULT 0,
    cw_rapido_revenue                NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_rapido_cash                   NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_rapido_toll                   NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_rapido_incentive              NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_rapido_subscription           NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_rapido_km                     NUMERIC(10,2)             NULL DEFAULT 0.00,
    cw_vehicle_rent                  NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_maintenance_charge            NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_active_days                   SMALLINT                  NULL DEFAULT 0,
    cw_tds                           NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_challans                      NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_accident_charge               NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_other_adjustment              NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_previous_outstanding          NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_gps_total_km                  NUMERIC(10,2)             NULL DEFAULT 0.00,
    cw_gps_ideal_km                  NUMERIC(10,2)             NULL DEFAULT 0.00,
    cw_gps_dead_km                   NUMERIC(10,2)             NULL DEFAULT 0.00,
    cw_gps_dead_pct                  NUMERIC(5,2)              NULL DEFAULT 0.00,
    cw_gps_dead_penalty              NUMERIC(10,2)             NULL DEFAULT 0.00,
    cw_trips                         INTEGER                   NULL DEFAULT 0,
    cw_total_km                      NUMERIC(10,2)             NULL DEFAULT 0.00,
    cw_gross_earnings                NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_total_deductions              NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_total_penalties               NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_os                            NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_to_pay                        NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_to_collect                    NUMERIC(12,2)             NULL DEFAULT 0.00,
    lw_trips                         INTEGER                   NULL DEFAULT 0,
    lw_gross_earnings                NUMERIC(12,2)             NULL DEFAULT 0.00,
    lw_os                            NUMERIC(12,2)             NULL DEFAULT 0.00,
    lw_week_number                   SMALLINT                  NULL DEFAULT 0,
    lw_hisaab_number                 VARCHAR(100)              NULL DEFAULT '',
    lw_status                        VARCHAR(20)               NULL DEFAULT 'unpaid',
    growth_pct                       NUMERIC(6,2)              NULL DEFAULT 0.00,
    cw_incentive_trips_done          INTEGER                   NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_app_drivers_phone ON public.app_drivers (phone);
CREATE INDEX IF NOT EXISTS idx_app_drivers_veh ON public.app_drivers (vehicle_reg_number);
CREATE INDEX IF NOT EXISTS idx_app_drivers_op ON public.app_drivers (operator_id);

-- 1.2 TABLE: app_operators
CREATE TABLE IF NOT EXISTS public.app_operators (
    app_operator_id                  SERIAL                    PRIMARY KEY,
    operator_id                      INTEGER                   NULL,
    app_driver_id                    INTEGER                   NULL DEFAULT 0,
    operator_code                    VARCHAR(50)               NULL,
    operator_type                    VARCHAR(20)               NULL DEFAULT 'fleet_owner',
    phone                            VARCHAR(15)               NULL UNIQUE,
    company_name                     VARCHAR(150)              NULL,
    contact_person_name              VARCHAR(150)              NULL,
    initials                         VARCHAR(5)                NULL,
    address                          TEXT                      NULL,
    total_vehicles                   INTEGER                   NULL DEFAULT 0,
    active_vehicles                  INTEGER                   NULL DEFAULT 0,
    idle_vehicles                    INTEGER                   NULL DEFAULT 0,
    total_drivers                    INTEGER                   NULL DEFAULT 0,
    deposit_total_req                NUMERIC(10,2)             NULL DEFAULT 0.00,
    deposit_paid                     NUMERIC(10,2)             NULL DEFAULT 0.00,
    deposit_pending                  NUMERIC(10,2)             NULL DEFAULT 0.00,
    assigned_manager_name            VARCHAR(150)              NULL,
    assigned_manager_phone           VARCHAR(15)               NULL,
    referral_code                    VARCHAR(30)               NULL UNIQUE,
    referral_reward_amt              NUMERIC(10,2)             NULL DEFAULT 2000.00,
    contract_terms_url               TEXT                      NULL,
    upi_id                           VARCHAR(100)              NULL,
    bank_account_last4               VARCHAR(4)                NULL,
    password_hash                    VARCHAR(255)              NULL,
    fcm_token                        TEXT                      NULL,
    preferred_language               VARCHAR(5)                NULL DEFAULT 'en',
    is_active                        BOOLEAN                   NULL DEFAULT TRUE,
    created_at                       TIMESTAMP WITH TIME ZONE  NULL DEFAULT NOW(),
    last_login_at                    TIMESTAMP WITH TIME ZONE  NULL,
    last_synced_at                   TIMESTAMP WITH TIME ZONE  NULL,
    cw_fleet_uber_trips              INTEGER                   NULL DEFAULT 0,
    cw_fleet_uber_revenue            NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_fleet_uber_cash               NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_fleet_uber_incentive          NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_fleet_uber_km                 NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_fleet_ola_trips               INTEGER                   NULL DEFAULT 0,
    cw_fleet_ola_revenue             NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_fleet_ola_cash                NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_fleet_ola_incentive           NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_fleet_ola_km                  NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_fleet_rapido_trips            INTEGER                   NULL DEFAULT 0,
    cw_fleet_rapido_revenue          NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_fleet_rapido_cash             NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_fleet_rapido_incentive        NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_fleet_rapido_km               NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_fleet_rent                    NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_fleet_maintenance             NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_fleet_tds                     NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_fleet_challans                NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_fleet_gps_dead_km             NUMERIC(10,2)             NULL DEFAULT 0.00,
    cw_fleet_gps_dead_penalty        NUMERIC(10,2)             NULL DEFAULT 0.00,
    cw_fleet_trips                   INTEGER                   NULL DEFAULT 0,
    cw_fleet_km                      NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_fleet_gross_earnings          NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_to_collect                    NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_to_pay                        NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_fleet_net_os                  NUMERIC(12,2)             NULL DEFAULT 0.00,
    cw_active_vehicles               INTEGER                   NULL DEFAULT 0,
    cw_active_drivers                INTEGER                   NULL DEFAULT 0,
    lw_fleet_trips                   INTEGER                   NULL DEFAULT 0,
    lw_fleet_km                      NUMERIC(12,2)             NULL DEFAULT 0.00,
    lw_fleet_gross_earnings          NUMERIC(12,2)             NULL DEFAULT 0.00,
    lw_fleet_net_os                  NUMERIC(12,2)             NULL DEFAULT 0.00,
    lw_week_number                   SMALLINT                  NULL DEFAULT 0,
    lw_hisaab_number                 VARCHAR(100)              NULL DEFAULT '',
    lw_status                        VARCHAR(20)               NULL DEFAULT 'unpaid',
    growth_pct                       NUMERIC(6,2)              NULL DEFAULT 0.00
);

CREATE INDEX IF NOT EXISTS idx_app_operators_phone ON public.app_operators (phone);

-- 1.3 TABLE: app_hisaabs
CREATE TABLE IF NOT EXISTS public.app_hisaabs (
    app_hisaab_id                    SERIAL                    PRIMARY KEY,
    allocation_id                    INTEGER                   NULL DEFAULT 1,
    hisaab_id                        INTEGER                   NULL DEFAULT 1,
    app_driver_id                    INTEGER                   NOT NULL,
    app_operator_id                  INTEGER                   NOT NULL DEFAULT 0,
    vehicle_id                       INTEGER                   NULL DEFAULT 1,
    uber_earnings_id                 INTEGER                   NULL,
    ola_earnings_id                  INTEGER                   NULL,
    rapido_earnings_id               INTEGER                   NULL,
    hisaab_number                    VARCHAR(100)              NULL UNIQUE,
    week_number                      SMALLINT                  NULL,
    period_start                     DATE                      NULL,
    period_end                       DATE                      NULL,
    days_count                       SMALLINT                  NULL DEFAULT 7,
    status                           VARCHAR(20)               NULL DEFAULT 'in_progress',
    is_locked                        BOOLEAN                   NULL DEFAULT FALSE,
    growth_pct                       NUMERIC(6,2)              NULL DEFAULT 0.00,
    uber_trips                       INTEGER                   NULL DEFAULT 0,
    uber_revenue                     NUMERIC(12,2)             NULL DEFAULT 0.00,
    uber_cash                        NUMERIC(12,2)             NULL DEFAULT 0.00,
    uber_toll                        NUMERIC(12,2)             NULL DEFAULT 0.00,
    uber_incentive                   NUMERIC(12,2)             NULL DEFAULT 0.00,
    uber_subscription                NUMERIC(12,2)             NULL DEFAULT 0.00,
    uber_km                          NUMERIC(10,2)             NULL DEFAULT 0.00,
    ola_trips                        INTEGER                   NULL DEFAULT 0,
    ola_revenue                      NUMERIC(12,2)             NULL DEFAULT 0.00,
    ola_cash                         NUMERIC(12,2)             NULL DEFAULT 0.00,
    ola_toll                         NUMERIC(12,2)             NULL DEFAULT 0.00,
    ola_incentive                    NUMERIC(12,2)             NULL DEFAULT 0.00,
    ola_subscription                 NUMERIC(12,2)             NULL DEFAULT 0.00,
    ola_km                           NUMERIC(10,2)             NULL DEFAULT 0.00,
    rapido_trips                     INTEGER                   NULL DEFAULT 0,
    rapido_revenue                   NUMERIC(12,2)             NULL DEFAULT 0.00,
    rapido_cash                      NUMERIC(12,2)             NULL DEFAULT 0.00,
    rapido_toll                      NUMERIC(12,2)             NULL DEFAULT 0.00,
    rapido_incentive                 NUMERIC(12,2)             NULL DEFAULT 0.00,
    rapido_subscription              NUMERIC(12,2)             NULL DEFAULT 0.00,
    rapido_km                        NUMERIC(10,2)             NULL DEFAULT 0.00,
    vehicle_daily_rate               NUMERIC(10,2)             NULL DEFAULT 1000.00,
    vehicle_rent                     NUMERIC(12,2)             NULL DEFAULT 0.00,
    maintenance_daily_rate           NUMERIC(10,2)             NULL DEFAULT 0.00,
    maintenance_charge               NUMERIC(12,2)             NULL DEFAULT 0.00,
    tds_amount                       NUMERIC(12,2)             NULL DEFAULT 0.00,
    challan_amount                   NUMERIC(12,2)             NULL DEFAULT 0.00,
    accident_charge                  NUMERIC(12,2)             NULL DEFAULT 0.00,
    other_adjustment                 NUMERIC(12,2)             NULL DEFAULT 0.00,
    previous_outstanding             NUMERIC(12,2)             NULL DEFAULT 0.00,
    gps_total_km                     NUMERIC(10,2)             NULL DEFAULT 0.00,
    gps_ideal_km                     NUMERIC(10,2)             NULL DEFAULT 0.00,
    gps_dead_km                      NUMERIC(10,2)             NULL DEFAULT 0.00,
    gps_dead_pct                     NUMERIC(5,2)              NULL DEFAULT 0.00,
    gps_dead_penalty                 NUMERIC(10,2)             NULL DEFAULT 0.00,
    gps_free_dead_pct                NUMERIC(5,2)              NULL DEFAULT 20.00,
    gps_penalty_rate                 NUMERIC(8,2)              NULL DEFAULT 5.00,
    completed_trips                  INTEGER                   NULL DEFAULT 0,
    total_km                         NUMERIC(10,2)             NULL DEFAULT 0.00,
    total_gross_earnings             NUMERIC(12,2)             NULL DEFAULT 0.00,
    total_deductions                 NUMERIC(12,2)             NULL DEFAULT 0.00,
    total_penalties                  NUMERIC(12,2)             NULL DEFAULT 0.00,
    current_period_os                NUMERIC(12,2)             NULL DEFAULT 0.00,
    to_pay                           NUMERIC(12,2)             NULL DEFAULT 0.00,
    to_collect                       NUMERIC(12,2)             NULL DEFAULT 0.00,
    letzryd_earning                  NUMERIC(12,2)             NULL DEFAULT 0.00,
    uber_last_synced_at              TIMESTAMP WITH TIME ZONE  NULL,
    ola_last_synced_at               TIMESTAMP WITH TIME ZONE  NULL,
    rapido_last_synced_at            TIMESTAMP WITH TIME ZONE  NULL,
    weekly_hisaab_due                NUMERIC(12,2)             NULL DEFAULT 0.00,
    last_refreshed_at                TIMESTAMP WITH TIME ZONE  NULL DEFAULT NOW(),
    notes                            TEXT                      NULL,
    paid_amount                      NUMERIC(12,2)             NULL DEFAULT 0.00,
    payment_status                   VARCHAR(20)               NULL DEFAULT 'unpaid',
    last_synced_at                   TIMESTAMP WITH TIME ZONE  NULL,
    created_at                       TIMESTAMP WITH TIME ZONE  NULL DEFAULT NOW(),
    updated_at                       TIMESTAMP WITH TIME ZONE  NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_app_hisaabs_driver ON public.app_hisaabs (app_driver_id);
CREATE INDEX IF NOT EXISTS idx_app_hisaabs_operator ON public.app_hisaabs (app_operator_id);
CREATE INDEX IF NOT EXISTS idx_app_hisaabs_week ON public.app_hisaabs (week_number);
CREATE INDEX IF NOT EXISTS idx_app_hisaabs_num ON public.app_hisaabs (hisaab_number);

-- 1.4 TABLE: app_driver_allocations (NEW: Vehicle Handover & Contract Bridge)
CREATE TABLE IF NOT EXISTS public.app_driver_allocations (
    app_allocation_id                SERIAL                    PRIMARY KEY,
    core_allocation_id               BIGINT                    NULL UNIQUE,
    app_driver_id                    INTEGER                   NOT NULL REFERENCES public.app_drivers(app_driver_id) ON DELETE CASCADE,
    app_operator_id                  INTEGER                   NULL,
    vehicle_number                   VARCHAR(20)               NOT NULL,
    allocation_date                  DATE                      NOT NULL,
    dropoff_date                     DATE                      NULL,
    start_odometer                   INTEGER                   NULL DEFAULT 0,
    end_odometer                     INTEGER                   NULL,
    daily_rental_rate                NUMERIC(10,2)             NULL DEFAULT 1000.00,
    allocation_status                VARCHAR(20)               NOT NULL DEFAULT 'ACTIVE',
    assigned_hub                     VARCHAR(100)              NULL,
    assigned_city                    VARCHAR(50)               NULL,
    assigned_manager                 VARCHAR(150)              NULL,
    agreement_url                    TEXT                      NULL,
    created_at                       TIMESTAMP WITH TIME ZONE  NULL DEFAULT NOW(),
    updated_at                       TIMESTAMP WITH TIME ZONE  NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_app_alloc_driver ON public.app_driver_allocations (app_driver_id);
CREATE INDEX IF NOT EXISTS idx_app_alloc_veh ON public.app_driver_allocations (vehicle_number);
CREATE INDEX IF NOT EXISTS idx_app_alloc_status ON public.app_driver_allocations (allocation_status);

-- 1.5 TABLE: app_driver_bank_accounts (NEW: IMPS Payout Beneficiaries)
CREATE TABLE IF NOT EXISTS public.app_driver_bank_accounts (
    bank_account_id                  SERIAL                    PRIMARY KEY,
    app_driver_id                    INTEGER                   NULL REFERENCES public.app_drivers(app_driver_id) ON DELETE CASCADE,
    app_operator_id                  INTEGER                   NULL REFERENCES public.app_operators(app_operator_id) ON DELETE CASCADE,
    account_number                   VARCHAR(100)              NOT NULL,
    ifsc_code                        VARCHAR(100)              NOT NULL,
    account_holder_name              VARCHAR(150)              NOT NULL,
    bank_name                        VARCHAR(150)              NULL,
    upi_id                           VARCHAR(100)              NULL,
    is_primary                       BOOLEAN                   NOT NULL DEFAULT TRUE,
    is_verified                      BOOLEAN                   NOT NULL DEFAULT FALSE,
    verification_status              VARCHAR(20)               NOT NULL DEFAULT 'VERIFIED',
    created_at                       TIMESTAMP WITH TIME ZONE  NULL DEFAULT NOW(),
    updated_at                       TIMESTAMP WITH TIME ZONE  NULL DEFAULT NOW(),
    CONSTRAINT uq_driver_bank_acc UNIQUE (account_number, ifsc_code)
);

CREATE INDEX IF NOT EXISTS idx_app_bank_driver ON public.app_driver_bank_accounts (app_driver_id);
CREATE INDEX IF NOT EXISTS idx_app_bank_op ON public.app_driver_bank_accounts (app_operator_id);

-- 1.6 TABLE: app_payments
CREATE TABLE IF NOT EXISTS public.app_payments (
    app_payment_id                   SERIAL                    PRIMARY KEY,
    payment_type                     VARCHAR(20)               NULL DEFAULT 'collection',
    payer_type                       VARCHAR(10)               NULL DEFAULT 'driver',
    payer_id                         INTEGER                   NULL,
    payee_type                       VARCHAR(10)               NULL DEFAULT 'letzryd',
    payee_id                         INTEGER                   NULL,
    app_hisaab_id                    INTEGER                   NULL,
    amount                           NUMERIC(12,2)             NULL DEFAULT 0.00,
    payment_mode                     VARCHAR(20)               NULL DEFAULT 'cashfree_upi',
    status                           VARCHAR(20)               NULL DEFAULT 'INITIATED',
    cf_order_id                      VARCHAR(100)              NULL,
    cf_payment_id                    VARCHAR(100)              NULL,
    cf_payout_id                     VARCHAR(100)              NULL,
    raw_response                     JSONB                     NULL,
    initiated_at                     TIMESTAMP WITH TIME ZONE  NULL DEFAULT NOW(),
    completed_at                     TIMESTAMP WITH TIME ZONE  NULL
);

CREATE INDEX IF NOT EXISTS idx_app_payments_order ON public.app_payments (cf_order_id);
CREATE INDEX IF NOT EXISTS idx_app_payments_hisaab ON public.app_payments (app_hisaab_id);

-- 1.7 TABLE: app_sessions
CREATE TABLE IF NOT EXISTS public.app_sessions (
    app_session_id                   SERIAL                    PRIMARY KEY,
    user_type                        VARCHAR(10)               NULL,
    user_ref_id                      INTEGER                   NULL,
    phone                            VARCHAR(15)               NULL,
    otp_hash                         VARCHAR(255)              NULL,
    attempt_count                    SMALLINT                  NULL DEFAULT 0,
    is_verified                      BOOLEAN                   NULL DEFAULT FALSE,
    used_password                    BOOLEAN                   NULL DEFAULT FALSE,
    session_jwt                      TEXT                      NULL,
    fcm_token                        TEXT                      NULL,
    ip_address                       VARCHAR(45)               NULL,
    user_agent                       TEXT                      NULL,
    expires_at                       TIMESTAMP WITH TIME ZONE  NULL,
    created_at                       TIMESTAMP WITH TIME ZONE  NULL DEFAULT NOW()
);

-- 1.8 TABLE: app_notifications
CREATE TABLE IF NOT EXISTS public.app_notifications (
    app_notif_id                     SERIAL                    PRIMARY KEY,
    target_type                      VARCHAR(10)               NULL DEFAULT 'driver',
    target_id                        INTEGER                   NULL,
    notif_type                       VARCHAR(20)               NULL DEFAULT 'hisaab',
    severity                         VARCHAR(10)               NULL DEFAULT 'info',
    icon                             VARCHAR(50)               NULL,
    title                            VARCHAR(255)              NULL,
    message                          TEXT                      NULL,
    deep_link                        VARCHAR(100)              NULL,
    is_read                          BOOLEAN                   NULL DEFAULT FALSE,
    created_at                       TIMESTAMP WITH TIME ZONE  NULL DEFAULT NOW()
);

-- 1.9 TABLE: app_referral_leads
CREATE TABLE IF NOT EXISTS public.app_referral_leads (
    lead_id                          SERIAL                    PRIMARY KEY,
    referred_by_type                 VARCHAR(10)               NOT NULL DEFAULT 'driver',
    referred_by_id                   INTEGER                   NOT NULL,
    lead_name                        VARCHAR(150)              NOT NULL,
    lead_phone                       VARCHAR(15)               NOT NULL,
    city                             VARCHAR(50)               NULL,
    referral_code_used               VARCHAR(30)               NULL,
    status                           VARCHAR(25)               NOT NULL DEFAULT 'LEAD_SUBMITTED',
    reward_amount                    NUMERIC(10,2)             NULL DEFAULT 1000.00,
    is_payout_done                   BOOLEAN                   NOT NULL DEFAULT FALSE,
    payout_date                      DATE                      NULL,
    created_at                       TIMESTAMP WITH TIME ZONE  NULL DEFAULT NOW()
);

-- 1.10 TABLE: app_audit_logs
CREATE TABLE IF NOT EXISTS public.app_audit_logs (
    audit_id                         SERIAL                    PRIMARY KEY,
    user_type                        VARCHAR(10)               NULL,
    user_id                          INTEGER                   NULL,
    phone                            VARCHAR(15)               NULL,
    action                           VARCHAR(100)              NOT NULL,
    details                          JSONB                     NULL,
    ip_address                       VARCHAR(45)               NULL,
    created_at                       TIMESTAMP WITH TIME ZONE  NULL DEFAULT NOW()
);

-- 1.11 TABLE: app_support_tickets
CREATE TABLE IF NOT EXISTS public.app_support_tickets (
    ticket_id                        SERIAL                    PRIMARY KEY,
    ticket_number                    VARCHAR(25)               NOT NULL UNIQUE,
    creator_type                     VARCHAR(10)               NOT NULL DEFAULT 'driver',
    creator_id                       INTEGER                   NOT NULL,
    category                         VARCHAR(50)               NOT NULL,
    priority                         VARCHAR(10)               NOT NULL DEFAULT 'MEDIUM',
    subject                          VARCHAR(255)              NOT NULL,
    description                      TEXT                      NOT NULL,
    attachment_urls                  TEXT[]                    NULL,
    status                           VARCHAR(20)               NOT NULL DEFAULT 'OPEN',
    assigned_to_user_id              INTEGER                   NULL,
    resolved_at                      TIMESTAMP WITH TIME ZONE  NULL,
    created_at                       TIMESTAMP WITH TIME ZONE  NULL DEFAULT NOW(),
    updated_at                       TIMESTAMP WITH TIME ZONE  NULL DEFAULT NOW()
);


-- ------------------------------------------------------------------------------
-- PART 2: MASTER POPULATION STORED PROCEDURE
-- ------------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE public.sp_populate_all_app_tables(p_truncate BOOLEAN DEFAULT TRUE)
LANGUAGE plpgsql
AS $procedure$
DECLARE
    v_driver_count INT := 0;
    v_op_count     INT := 0;
    v_alloc_count  INT := 0;
    v_bank_count   INT := 0;
    v_hisaab_count INT := 0;
BEGIN
    RAISE NOTICE 'Starting master App Tables population pipeline...';

    IF p_truncate THEN
        RAISE NOTICE 'Truncating existing app records with RESTART IDENTITY...';
        TRUNCATE TABLE 
            public.app_support_tickets,
            public.app_referral_leads,
            public.app_notifications,
            public.app_payments,
            public.app_hisaabs,
            public.app_driver_allocations,
            public.app_driver_bank_accounts,
            public.app_drivers,
            public.app_operators
        RESTART IDENTITY CASCADE;
    END IF;

    -- STEP 0: Seed Core Operators (Primary IDs 1 & 2 for test suite and system ops)
    INSERT INTO public.app_operators (
        app_operator_id, operator_id, operator_code, operator_type, company_name,
        contact_person_name, phone, initials, address, is_active
    ) VALUES (
        0, 0, 'OPR-LETZ-SYS', 'fleet_owner', 'LetzRyd Internal Fleet',
        'Fleet Ops', '0000000001', 'LR', 'Bangalore Headquarters', TRUE
    ) ON CONFLICT (phone) DO NOTHING;

    INSERT INTO public.app_operators (
        app_operator_id, operator_id, operator_code, operator_type, company_name,
        contact_person_name, phone, initials, address, total_vehicles, active_vehicles,
        idle_vehicles, total_drivers, deposit_total_req, deposit_paid, deposit_pending,
        assigned_manager_name, assigned_manager_phone, referral_code, referral_reward_amt,
        contract_terms_url, upi_id, bank_account_last4, preferred_language, is_active,
        cw_fleet_uber_trips, cw_fleet_uber_revenue, cw_fleet_uber_cash, cw_fleet_uber_incentive, cw_fleet_uber_km,
        cw_fleet_ola_trips, cw_fleet_ola_revenue, cw_fleet_ola_cash, cw_fleet_ola_incentive, cw_fleet_ola_km,
        cw_fleet_rapido_trips, cw_fleet_rapido_revenue, cw_fleet_rapido_cash, cw_fleet_rapido_incentive, cw_fleet_rapido_km,
        cw_fleet_rent, cw_fleet_maintenance, cw_fleet_tds, cw_fleet_challans, cw_fleet_gps_dead_km, cw_fleet_gps_dead_penalty,
        cw_fleet_trips, cw_fleet_km, cw_fleet_gross_earnings, cw_to_collect, cw_to_pay, cw_fleet_net_os,
        cw_active_vehicles, cw_active_drivers, lw_fleet_trips, lw_fleet_km, lw_fleet_gross_earnings,
        lw_fleet_net_os, lw_week_number, lw_hisaab_number, lw_status, growth_pct
    ) VALUES (
        1, 1, 'OPR-HYD-001', 'Fleet Owner', 'Anurag & RK Fleet Logistics',
        'Anurag', '9691938866', 'A', 'Plot 12, Gachibowli Financial District, Hyderabad - 500032',
        4, 4, 0, 4, 25000.00, 20000.00, 5000.00,
        'Kalyan Chakravarthy', '9988770011', 'ANURAGOPR', 2000.00,
        'https://letzryd.com/terms/operator', 'anuragfleet@okhdfcbank', '9012', 'en', TRUE,
        340, 48500.00, 31000.00, 9200.00, 3600.00,
        185, 21500.00, 13400.00, 3800.00, 2100.00,
        120, 14200.00, 8100.00, 2400.00, 1450.00,
        18000.00, 3600.00, 480.00, 1500.00, 0.00, 0.00,
        645, 7150.00, 84200.00, 12450.00, 0.00, 12450.00,
        4, 4, 610, 6800.00, 79500.00, 0.00, 29, 'HIS-2026-029-FLT001', 'settled_pay', 5.91
    ), (
        2, 2, 'OP-501', 'Fleet Owner', 'Samvreeddhi Mobility Fleet',
        'Samvreeddhi', '9848012345', 'S', 'Plot 88, Madhapur, Hyderabad - 500081',
        2, 2, 0, 2, 15000.00, 15000.00, 0.00,
        'Arif Khan', '9848012344', 'SALEEMFLT', 2000.00,
        'https://letzryd.com/terms/operator', 'saleem.fleet@paytm', '3344', 'en', TRUE,
        140, 19400.00, 12700.00, 3650.00, 1540.00,
        76, 8500.00, 5200.00, 1500.00, 830.00,
        49, 5900.00, 3150.00, 1000.00, 580.00,
        7450.00, 1490.00, 190.00, 500.00, 0.00, 0.00,
        265, 2950.00, 17000.00, 1820.50, 4580.00, -2759.50,
        2, 2, 495, 5300.00, 25500.00, 0.00, 29, 'HIS-2026-029-FLT002', 'settled_pay', -33.33
    );

    -- Advance sequence for app_operators
    PERFORM SETVAL('public.app_operators_app_operator_id_seq', 2, TRUE);

    -- STEP 0.1: Seed Core Drivers (Primary IDs 1 to 6 for test suite)
    INSERT INTO public.app_drivers (
        app_driver_id, driver_id, operator_id, driver_code, phone, full_name, initials,
        aadhar_number, blood_group, dob, address, joined_date, emergency_name, emergency_relation,
        emergency_phone, dl_number, dl_expiry, current_vehicle_id, current_allocation_id,
        vehicle_reg_number, vehicle_make, vehicle_model, vehicle_variant, vehicle_color, vehicle_year,
        vehicle_fuel_type, vehicle_odometer_km, vehicle_allocated_from, vehicle_daily_rate,
        rc_number, rc_expiry, insurance_number, insurance_expiry, permit_type, permit_number,
        permit_expiry, fitness_number, fitness_expiry, puc_expiry, doc_last_updated,
        deposit_total_req, deposit_paid, deposit_pending, deposit_next_due, joining_fee_agreed,
        joining_fee_paid, cumulative_owed, assigned_manager_name, assigned_manager_phone,
        incentive_trips_target, incentive_reward_amt, cw_incentive_trips_done, referral_code,
        referral_reward_amt, contract_terms_url, upi_id, bank_account_last4, preferred_language, is_active,
        cw_uber_trips, cw_uber_revenue, cw_uber_cash, cw_uber_toll, cw_uber_incentive, cw_uber_subscription, cw_uber_km,
        cw_ola_trips, cw_ola_revenue, cw_ola_cash, cw_ola_toll, cw_ola_incentive, cw_ola_subscription, cw_ola_km,
        cw_rapido_trips, cw_rapido_revenue, cw_rapido_cash, cw_rapido_toll, cw_rapido_incentive, cw_rapido_subscription, cw_rapido_km,
        cw_vehicle_rent, cw_maintenance_charge, cw_active_days, cw_tds, cw_challans, cw_accident_charge, cw_other_adjustment, cw_previous_outstanding,
        cw_gps_total_km, cw_gps_ideal_km, cw_gps_dead_km, cw_gps_dead_pct, cw_gps_dead_penalty,
        cw_trips, cw_total_km, cw_gross_earnings, cw_total_deductions, cw_total_penalties,
        cw_os, cw_to_pay, cw_to_collect, lw_trips, lw_gross_earnings, lw_os, lw_week_number,
        lw_hisaab_number, lw_status, growth_pct
    ) VALUES (
        1, 157, 1, 'LR-DRV-0157', '9901484683', 'Vivek', 'V',
        '2345-6789-0123', 'B+', '1992-08-14', 'No. 42, 3rd Cross, Indiranagar, Bangalore - 560038', '2024-10-15',
        'Priya', 'Spouse/Wife', '9901484680', 'KA05-2024-1234567', '2029-05-20', 1, 1,
        'KA05AQ7692', 'Maruti', 'Dzire CNG', 'VXi CNG', 'White Pearl', 2021,
        'CNG', 124380, '2024-10-15', 1000.00,
        'KA0520224567', '2036-05-01', 'KA054567890', '2027-03-20', 'Tourist Permit', 'KA-05-TP-2024-0012',
        '2026-12-31', 'FIT2024056', '2026-10-12', '2026-08-15', '2026-07-25',
        6000.00, 5000.00, 1000.00, '2026-08-15', 1000.00,
        1000.00, 0.00, 'Kalyan Chakravarthy', '9988770011',
        260, 1500.00, 145, 'VIVEK0157',
        1000.00, 'https://letzryd.com/terms/driver', 'vivek.letzryd@okaxis', '4567', 'en', TRUE,
        82, 11400.00, 7200.00, 240.00, 2200.00, 950.00, 890.00,
        41, 4800.00, 3100.00, 120.00, 900.00, 550.00, 460.00,
        22, 2400.00, 1400.00, 50.00, 400.00, 250.00, 240.00,
        6000.00, 1200.00, 6, 240.00, 0.00, 0.00, 0.00, 0.00,
        1590.00, 1800.00, 0.00, 0.00, 0.00,
        145, 1590.00, 18600.00, 7440.00, 0.00,
        -7995.80, 0.00, 7995.80, 218, 17200.00, 0.00, 29,
        'HIS-2026-029-AQ7692', 'settled_pay', 8.14
    ), (
        2, 202, 1, 'LR-DRV-0202', '9140631755', 'Sushant', 'S',
        '8765-4321-0987', 'O+', '1995-04-12', '15, Koramangala 4th Block, Bangalore - 560034', '2025-01-10',
        'Sunita', 'Mother', '9140631750', 'KA05-2023-7654321', '2028-11-15', 2, 2,
        'KA05AQ7693', 'Maruti', 'Dzire CNG', 'VXi CNG', 'Silver', 2022,
        'CNG', 98200, '2025-01-10', 1000.00,
        'KA0520237693', '2037-01-10', 'KA057693890', '2027-01-10', 'Tourist Permit', 'KA-05-TP-2025-0089',
        '2026-12-31', 'FIT2025012', '2026-11-20', '2026-09-10', '2026-07-25',
        6000.00, 6000.00, 0.00, '2026-08-15', 1000.00,
        1000.00, 0.00, 'Kalyan Chakravarthy', '9988770011',
        260, 1500.00, 118, 'SUSHANT202',
        1000.00, 'https://letzryd.com/terms/driver', 'sushant@okhdfcbank', '7693', 'en', TRUE,
        65, 8900.00, 5400.00, 180.00, 1600.00, 750.00, 710.00,
        35, 3900.00, 2400.00, 90.00, 700.00, 420.00, 380.00,
        18, 1900.00, 1100.00, 40.00, 300.00, 180.00, 190.00,
        5000.00, 1000.00, 5, 190.00, 0.00, 0.00, 0.00, 0.00,
        1280.00, 1500.00, 0.00, 0.00, 0.00,
        118, 1280.00, 14700.00, 6190.00, 0.00,
        -5310.00, 0.00, 5310.00, 195, 15400.00, 0.00, 29,
        'HIS-2026-029-AQ7693', 'settled_pay', -4.55
    ), (
        3, 312, 1, 'LR-DRV-0312', '9930420065', 'Aayush', 'A',
        '5432-1098-7654', 'A+', '1990-11-25', 'Flat 302, Green Glen Layout, Bellandur, Bangalore - 560103', '2024-06-01',
        'Neha', 'Spouse/Wife', '9930420060', 'KA03-2022-9988776', '2027-04-18', 3, 3,
        'TS07EV4401', 'Tata', 'Tigor EV', 'XZ+ EV', 'Daytona Grey', 2022,
        'Electric', 82150, '2024-06-01', 950.00,
        'TS0720224401', '2037-06-01', 'TS074401890', '2027-06-01', 'Tourist Permit', 'TS-07-TP-2022-4401',
        '2026-12-31', 'FIT2024201', '2026-08-30', '2026-10-01', '2026-07-25',
        6000.00, 6000.00, 0.00, '2026-08-15', 1000.00,
        1000.00, 0.00, 'Ramesh Naik', '9876543299',
        260, 1500.00, 218, 'AAYUSH312',
        1000.00, 'https://letzryd.com/terms/driver', 'aayush@okicici', '4401', 'en', TRUE,
        110, 16200.00, 9800.00, 380.00, 3100.00, 1400.00, 1200.00,
        62, 7100.00, 4000.00, 190.00, 1300.00, 850.00, 690.00,
        46, 5400.00, 2700.00, 80.00, 900.00, 380.00, 500.00,
        5700.00, 1140.00, 6, 180.00, 0.00, 0.00, 0.00, 0.00,
        2390.00, 2700.00, 0.00, 0.00, 0.00,
        218, 2390.00, 14200.00, 7020.00, 0.00,
        -6180.00, 6180.00, 0.00, 299, 13800.00, 0.00, 29,
        'HIS-2026-029-EV4401', 'settled_pay', 3.80
    ), (
        4, 41, 1, 'LR-HYD-0041', '9866941379', 'Anurag Driver', 'AD',
        '1122-3344-5566', 'O+', '1986-06-20', '2-4-56, Old Alwal, Secunderabad - 500010', '2024-08-01',
        'Lakshmi Devi', 'Spouse/Wife', '9866941380', 'TS09-2021-4455667', '2026-09-15', 4, 4,
        'TS08EV0580', 'Tata', 'XPRES-T EV', 'XM+ EV', 'White', 2022,
        'Electric', 71200, '2024-08-01', 950.00,
        'TS0820220580', '2037-08-01', 'TS080580890', '2027-08-01', 'Tourist Permit', 'TS-08-TP-2022-0580',
        '2026-12-31', 'FIT2024112', '2026-09-20', '2026-09-15', '2026-07-25',
        6000.00, 5000.00, 1000.00, '2026-08-15', 1000.00,
        1000.00, 0.00, 'Ramesh Naik', '9876543299',
        260, 1500.00, 178, 'ANURAGD41',
        1000.00, 'https://letzryd.com/terms/driver', 'anurag.d@ybl', '0580', 'en', TRUE,
        83, 12000.00, 8600.00, 280.00, 2300.00, 1100.00, 950.00,
        47, 5700.00, 3900.00, 140.00, 900.00, 680.00, 520.00,
        34, 4500.00, 2900.00, 70.00, 800.00, 310.00, 490.00,
        5700.00, 1140.00, 6, 170.00, 500.00, 0.00, 0.00, 0.00,
        1960.00, 2200.00, 0.00, 0.00, 0.00,
        178, 1960.00, 10350.00, 7510.00, 0.00,
        -3480.00, 3480.00, 0.00, 198, 11200.00, 0.00, 29,
        'HIS-2026-029-V0580', 'settled_pay', -9.10
    ), (
        5, 418, 2, 'LR-DRV-0418', '9848012346', 'Mohammed Ali', 'MA',
        '3456-7890-1234', 'B-', '1991-03-18', '12-3-456, Mehdipatnam, Hyderabad - 500028', '2025-02-20',
        'Fatima Begum', 'Spouse/Wife', '9848012348', 'TS08-2023-1122334', '2028-06-10', 5, 5,
        'TS08EV1129', 'Tata', 'XPRES-T EV', 'XM EV', 'Silver', 2023,
        'Electric', 64300, '2025-02-20', 1050.00,
        'TS0820231129', '2038-02-20', 'TS081129890', '2028-02-20', 'Tourist Permit', 'TS-08-TP-2023-1129',
        '2026-12-31', 'FIT2025089', '2027-02-20', '2026-11-15', '2026-07-25',
        7000.00, 7000.00, 0.00, '2026-08-15', 1000.00,
        1000.00, 0.00, 'Arif Khan', '9848012344',
        260, 1500.00, 201, 'MOHAMM418',
        1000.00, 'https://letzryd.com/terms/driver', 'mohammed.ali@axl', '1129', 'en', TRUE,
        105, 14600.00, 9100.00, 340.00, 2800.00, 1300.00, 1150.00,
        58, 6400.00, 3800.00, 160.00, 1100.00, 750.00, 630.00,
        38, 4600.00, 2300.00, 70.00, 750.00, 320.00, 460.00,
        5250.00, 1050.00, 5, 140.00, 0.00, 0.00, 0.00, 0.00,
        2240.00, 2500.00, 0.00, 0.00, 0.00,
        201, 2240.00, 12800.00, 6440.00, 0.00,
        -4580.00, 4580.00, 0.00, 285, 14500.00, 0.00, 29,
        'HIS-2026-029-EV1129', 'settled_pay', -2.10
    ), (
        6, 501, 2, 'LR-DRV-0501', '9848012347', 'Anil Verma', 'AV',
        '7890-1234-5678', 'AB+', '1993-07-30', '8-2-120/A, Banjara Hills Road 2, Hyderabad - 500034', '2026-05-15',
        'Meena Verma', 'Spouse/Wife', '9848012349', 'TS09-2023-9988776', '2028-09-20', 6, 6,
        'TS09EV9900', 'BYD', 'e6 EV', 'e6 Standard', 'Pearl White', 2023,
        'Electric', 48500, '2026-05-15', 1100.00,
        'TS0920239900', '2038-05-15', 'TS099900890', '2028-05-15', 'Tourist Permit', 'TS-09-TP-2023-9900',
        '2026-12-31', 'FIT2025341', '2027-05-15', '2026-12-01', '2026-07-25',
        8000.00, 4000.00, 4000.00, '2026-08-15', 1000.00,
        1000.00, 1820.50, 'Arif Khan', '9848012344',
        260, 1500.00, 64, 'ANILV501',
        1000.00, 'https://letzryd.com/terms/driver', 'anil.verma@icici', '9900', 'en', TRUE,
        35, 4800.00, 3600.00, 110.00, 850.00, 420.00, 390.00,
        18, 2100.00, 1400.00, 50.00, 400.00, 250.00, 200.00,
        11, 1300.00, 850.00, 20.00, 250.00, 110.00, 120.00,
        2200.00, 440.00, 2, 50.00, 500.00, 0.00, 0.00, 0.00,
        710.00, 800.00, 0.00, 0.00, 0.00,
        64, 710.00, 4200.00, 3190.00, 0.00,
        1820.50, 0.00, 1820.50, 210, 11000.00, 0.00, 29,
        'HIS-2026-029-EV9900', 'settled_pay', -15.30
    );

    -- Advance sequence for app_drivers
    PERFORM SETVAL('public.app_drivers_app_driver_id_seq', 6, TRUE);

    -- STEP 0.2: Seed the 18 demo Hisaabs (weeks 30, 29, 28 for drivers 1-6)
    INSERT INTO public.app_hisaabs (
        app_hisaab_id, app_driver_id, app_operator_id, hisaab_number, week_number, period_start, period_end,
        days_count, status, is_locked, uber_trips, uber_revenue, uber_cash, uber_toll, uber_incentive,
        uber_subscription, uber_km, ola_trips, ola_revenue, ola_cash, ola_toll, ola_incentive,
        ola_subscription, ola_km, rapido_trips, rapido_revenue, rapido_cash, rapido_toll,
        rapido_incentive, rapido_subscription, rapido_km, vehicle_daily_rate, vehicle_rent,
        maintenance_charge, tds_amount, challan_amount, accident_charge, other_adjustment,
        previous_outstanding, gps_total_km, gps_ideal_km, gps_dead_km, gps_dead_penalty,
        completed_trips, total_km, total_gross_earnings, total_deductions, total_penalties,
        current_period_os, to_pay, to_collect, notes
    ) VALUES
    -- Driver 1 (Vivek): Week 30 (app_hisaab_id = 1)
    (1, 1, 1, 'HIS-2026-030-AQ7692', 30, '2026-07-21', '2026-07-27', 6, 'in_progress', FALSE,
     82, 11400.00, 7200.00, 240.00, 2200.00, 950.00, 890.00,
     41, 4800.00, 3100.00, 120.00, 900.00, 550.00, 460.00,
     22, 2400.00, 1400.00, 50.00, 400.00, 250.00, 240.00,
     1000.00, 6000.00, 1200.00, 240.00, 0.00, 0.00, 0.00, 0.00,
     1590.00, 1800.00, 0.00, 0.00,
     145, 1590.00, 18600.00, 7440.00, 0.00, -7995.80, 0.00, 7995.80, 'Current active week statement in progress.'),
    -- Driver 1: Week 29 (app_hisaab_id = 2)
    (2, 1, 1, 'HIS-2026-029-AQ7692', 29, '2026-07-14', '2026-07-20', 6, 'settled_pay', TRUE,
     119, 9976.00, 6880.00, 450.00, 2600.00, 1200.00, 1450.00,
     61, 4472.00, 3096.00, 180.00, 1100.00, 750.00, 720.00,
     37, 2752.00, 1720.00, 80.00, 750.00, 320.00, 480.00,
     1000.00, 6000.00, 1200.00, 220.00, 0.00, 0.00, 0.00, 0.00,
     2650.00, 2900.00, 0.00, 0.00,
     218, 2650.00, 17200.00, 7420.00, 0.00, 0.00, 9780.00, 0.00, 'Locked Week 29 statement.'),
    -- Driver 1: Week 28 (app_hisaab_id = 3)
    (3, 1, 1, 'HIS-2026-028-AQ7692', 28, '2026-07-07', '2026-07-13', 6, 'settled_pay', TRUE,
     165, 18500.00, 12000.00, 520.00, 3600.00, 1600.00, 1550.00,
     75, 8200.00, 5100.00, 210.00, 1400.00, 950.00, 780.00,
     50, 5900.00, 3100.00, 110.00, 950.00, 420.00, 540.00,
     1000.00, 6000.00, 1200.00, 240.00, 0.00, 0.00, 0.00, 0.00,
     2870.00, 3100.00, 0.00, 0.00,
     290, 2870.00, 15200.00, 7440.00, 0.00, 0.00, 7760.00, 0.00, 'Fully settled historical week.'),

    -- Drivers 2, 3, 4 (Op 1) hisaabs
    (4, 2, 1, 'HIS-2026-030-AQ7693', 30, '2026-07-21', '2026-07-27', 5, 'in_progress', FALSE, 65, 8900.00, 5400.00, 180.00, 1600.00, 750.00, 710.00, 35, 3900.00, 2400.00, 90.00, 700.00, 420.00, 380.00, 18, 1900.00, 1100.00, 40.00, 300.00, 180.00, 190.00, 1000.00, 5000.00, 1000.00, 190.00, 0.00, 0.00, 0.00, 0.00, 1280.00, 1500.00, 0.00, 0.00, 118, 1280.00, 14700.00, 6190.00, 0.00, -5310.00, 0.00, 5310.00, 'Week 30'),
    (5, 2, 1, 'HIS-2026-029-AQ7693', 29, '2026-07-14', '2026-07-20', 6, 'settled_pay', TRUE, 107, 8932.00, 6160.00, 450.00, 2600.00, 1200.00, 1450.00, 54, 4004.00, 2772.00, 180.00, 1100.00, 750.00, 720.00, 33, 2464.00, 1540.00, 80.00, 750.00, 320.00, 480.00, 1000.00, 6000.00, 1200.00, 220.00, 0.00, 0.00, 0.00, 0.00, 2650.00, 2900.00, 0.00, 0.00, 194, 2650.00, 15400.00, 7420.00, 0.00, 0.00, 7980.00, 0.00, 'Week 29'),
    (6, 2, 1, 'HIS-2026-028-AQ7693', 28, '2026-07-07', '2026-07-13', 6, 'settled_pay', TRUE, 165, 18500.00, 12000.00, 520.00, 3600.00, 1600.00, 1550.00, 75, 8200.00, 5100.00, 210.00, 1400.00, 950.00, 780.00, 50, 5900.00, 3100.00, 110.00, 950.00, 420.00, 540.00, 1000.00, 6000.00, 1200.00, 240.00, 0.00, 0.00, 0.00, 0.00, 2870.00, 3100.00, 0.00, 0.00, 290, 2870.00, 15200.00, 7440.00, 0.00, 0.00, 7760.00, 0.00, 'Week 28'),

    (7, 3, 1, 'HIS-2026-030-EV4401', 30, '2026-07-21', '2026-07-27', 6, 'in_progress', FALSE, 110, 16200.00, 9800.00, 380.00, 3100.00, 1400.00, 1200.00, 62, 7100.00, 4000.00, 190.00, 1300.00, 850.00, 690.00, 46, 5400.00, 2700.00, 80.00, 900.00, 380.00, 500.00, 950.00, 5700.00, 1140.00, 180.00, 0.00, 0.00, 0.00, 0.00, 2390.00, 2700.00, 0.00, 0.00, 218, 2390.00, 14200.00, 7020.00, 0.00, -6180.00, 6180.00, 0.00, 'Week 30'),
    (8, 3, 1, 'HIS-2026-029-EV4401', 29, '2026-07-14', '2026-07-20', 6, 'settled_pay', TRUE, 164, 8004.00, 5520.00, 450.00, 2600.00, 1200.00, 1450.00, 83, 3588.00, 2484.00, 180.00, 1100.00, 750.00, 720.00, 50, 2208.00, 1380.00, 80.00, 750.00, 320.00, 480.00, 950.00, 5700.00, 1140.00, 220.00, 0.00, 0.00, 0.00, 0.00, 2650.00, 2900.00, 0.00, 0.00, 297, 2650.00, 13800.00, 7060.00, 0.00, 0.00, 6740.00, 0.00, 'Week 29'),
    (9, 3, 1, 'HIS-2026-028-EV4401', 28, '2026-07-07', '2026-07-13', 6, 'settled_pay', TRUE, 165, 18500.00, 12000.00, 520.00, 3600.00, 1600.00, 1550.00, 75, 8200.00, 5100.00, 210.00, 1400.00, 950.00, 780.00, 50, 5900.00, 3100.00, 110.00, 950.00, 420.00, 540.00, 950.00, 5700.00, 1140.00, 240.00, 0.00, 0.00, 0.00, 0.00, 2870.00, 3100.00, 0.00, 0.00, 290, 2870.00, 15200.00, 7080.00, 0.00, 0.00, 8120.00, 0.00, 'Week 28'),

    (10, 4, 1, 'HIS-2026-030-V0580', 30, '2026-07-21', '2026-07-27', 6, 'in_progress', FALSE, 83, 12000.00, 8600.00, 280.00, 2300.00, 1100.00, 950.00, 47, 5700.00, 3900.00, 140.00, 900.00, 680.00, 520.00, 34, 4500.00, 2900.00, 70.00, 800.00, 310.00, 490.00, 950.00, 5700.00, 1140.00, 170.00, 500.00, 0.00, 0.00, 0.00, 1960.00, 2200.00, 0.00, 0.00, 178, 1960.00, 10350.00, 7510.00, 0.00, -3480.00, 3480.00, 0.00, 'Week 30'),
    (11, 4, 1, 'HIS-2026-029-V0580', 29, '2026-07-14', '2026-07-20', 6, 'settled_pay', TRUE, 108, 6496.00, 4480.00, 450.00, 2600.00, 1200.00, 1450.00, 55, 2912.00, 2016.00, 180.00, 1100.00, 750.00, 720.00, 33, 1792.00, 1120.00, 80.00, 750.00, 320.00, 480.00, 950.00, 5700.00, 1140.00, 220.00, 0.00, 0.00, 0.00, 0.00, 2650.00, 2900.00, 0.00, 0.00, 196, 2650.00, 11200.00, 7060.00, 0.00, 0.00, 4140.00, 0.00, 'Week 29'),
    (12, 4, 1, 'HIS-2026-028-V0580', 28, '2026-07-07', '2026-07-13', 6, 'settled_pay', TRUE, 165, 18500.00, 12000.00, 520.00, 3600.00, 1600.00, 1550.00, 75, 8200.00, 5100.00, 210.00, 1400.00, 950.00, 780.00, 50, 5900.00, 3100.00, 110.00, 950.00, 420.00, 540.00, 950.00, 5700.00, 1140.00, 240.00, 0.00, 0.00, 0.00, 0.00, 2870.00, 3100.00, 0.00, 0.00, 290, 2870.00, 15200.00, 7080.00, 0.00, 0.00, 8120.00, 0.00, 'Week 28'),

    -- Drivers 5, 6 (Op 2) hisaabs
    (13, 5, 2, 'HIS-2026-030-EV1129', 30, '2026-07-21', '2026-07-27', 5, 'in_progress', FALSE, 105, 14600.00, 9100.00, 340.00, 2800.00, 1300.00, 1150.00, 58, 6400.00, 3800.00, 160.00, 1100.00, 750.00, 630.00, 38, 4600.00, 2300.00, 70.00, 750.00, 320.00, 460.00, 1050.00, 5250.00, 1050.00, 140.00, 0.00, 0.00, 0.00, 0.00, 2240.00, 2500.00, 0.00, 0.00, 201, 2240.00, 12800.00, 6440.00, 0.00, -4580.00, 4580.00, 0.00, 'Week 30'),
    (14, 5, 2, 'HIS-2026-029-EV1129', 29, '2026-07-14', '2026-07-20', 6, 'settled_pay', TRUE, 156, 8410.00, 5800.00, 450.00, 2600.00, 1200.00, 1450.00, 79, 3770.00, 2610.00, 180.00, 1100.00, 750.00, 720.00, 48, 2320.00, 1450.00, 80.00, 750.00, 320.00, 480.00, 1050.00, 6300.00, 1260.00, 220.00, 0.00, 0.00, 0.00, 0.00, 2650.00, 2900.00, 0.00, 0.00, 283, 2650.00, 14500.00, 7780.00, 0.00, 0.00, 6720.00, 0.00, 'Week 29'),
    (15, 5, 2, 'HIS-2026-028-EV1129', 28, '2026-07-07', '2026-07-13', 6, 'settled_pay', TRUE, 165, 18500.00, 12000.00, 520.00, 3600.00, 1600.00, 1550.00, 75, 8200.00, 5100.00, 210.00, 1400.00, 950.00, 780.00, 50, 5900.00, 3100.00, 110.00, 950.00, 420.00, 540.00, 1050.00, 6300.00, 1260.00, 240.00, 0.00, 0.00, 0.00, 0.00, 2870.00, 3100.00, 0.00, 0.00, 290, 2870.00, 15200.00, 7800.00, 0.00, 0.00, 7400.00, 0.00, 'Week 28'),

    (16, 6, 2, 'HIS-2026-030-EV9900', 30, '2026-07-21', '2026-07-27', 2, 'in_progress', FALSE, 35, 4800.00, 3600.00, 110.00, 850.00, 420.00, 390.00, 18, 2100.00, 1400.00, 50.00, 400.00, 250.00, 200.00, 11, 1300.00, 850.00, 20.00, 250.00, 110.00, 120.00, 1100.00, 2200.00, 440.00, 50.00, 500.00, 0.00, 0.00, 0.00, 710.00, 800.00, 0.00, 0.00, 64, 710.00, 4200.00, 3190.00, 0.00, 1820.50, 0.00, 1820.50, 'Week 30'),
    (17, 6, 2, 'HIS-2026-029-EV9900', 29, '2026-07-14', '2026-07-20', 6, 'settled_pay', TRUE, 115, 6380.00, 4400.00, 450.00, 2600.00, 1200.00, 1450.00, 58, 2860.00, 1980.00, 180.00, 1100.00, 750.00, 720.00, 35, 1760.00, 1100.00, 80.00, 750.00, 320.00, 480.00, 1100.00, 6600.00, 1320.00, 220.00, 0.00, 0.00, 0.00, 0.00, 2650.00, 2900.00, 0.00, 0.00, 208, 2650.00, 11000.00, 8140.00, 0.00, 0.00, 2860.00, 0.00, 'Week 29'),
    (18, 6, 2, 'HIS-2026-028-EV9900', 28, '2026-07-07', '2026-07-13', 6, 'settled_pay', TRUE, 165, 18500.00, 12000.00, 520.00, 3600.00, 1600.00, 1550.00, 75, 8200.00, 5100.00, 210.00, 1400.00, 950.00, 780.00, 50, 5900.00, 3100.00, 110.00, 950.00, 420.00, 540.00, 1100.00, 6600.00, 1320.00, 240.00, 0.00, 0.00, 0.00, 0.00, 2870.00, 3100.00, 0.00, 0.00, 290, 2870.00, 15200.00, 8160.00, 0.00, 0.00, 7040.00, 0.00, 'Week 28');

    -- Advance sequence for app_hisaabs
    PERFORM SETVAL('public.app_hisaabs_app_hisaab_id_seq', 18, TRUE);

    -- STEP 0.3: Seed driver 1 interactive artifacts (Support Tickets, Notifications, Referrals, Payments)
    INSERT INTO public.app_support_tickets (
        ticket_number, creator_type, creator_id, category, priority, subject, description, status, created_at
    ) VALUES
        ('TKT-2026-001', 'driver', 1, 'Hisaab', 'HIGH', 'Discrepancy in Week 29 Cash Collection', 'Uber cash recorded Rs. 6880 but actual trip cash was Rs. 6200.', 'OPEN', NOW() - INTERVAL '2 days'),
        ('TKT-2026-002', 'driver', 1, 'Vehicle', 'MEDIUM', 'AC cooling low during peak hours', 'Vehicle KA05AQ7692 requires AC gas refill at next maintenance.', 'IN_PROGRESS', NOW() - INTERVAL '5 days');

    INSERT INTO public.app_notifications (
        target_type, target_id, notif_type, severity, icon, title, message, deep_link, is_read, created_at
    ) VALUES
        ('driver', 1, 'hisaab', 'info', 'calculator', 'Week 30 Statement Generated', 'Your tentative earnings are Rs. 18,600 with estimated payout of Rs. 7,995.80.', '/dashboard/driver/hisaabs', FALSE, NOW() - INTERVAL '1 hour'),
        ('driver', 1, 'payment', 'success', 'check-circle', 'Payment Successful', 'Payment of Rs. 750 received towards weekly security deposit dues.', '/dashboard/driver/payments', TRUE, NOW() - INTERVAL '1 day');

    INSERT INTO public.app_referral_leads (
        referred_by_type, referred_by_driver_id, lead_name, lead_phone, referral_code_used, status, reward_amount, created_at
    ) VALUES
        ('driver', 1, 'Ramesh Kumar', '9845012345', 'VIVEK0157', 'LEAD_SUBMITTED', 1000.00, NOW() - INTERVAL '3 days'),
        ('driver', 1, 'Mohan Lal', '9845012346', 'VIVEK0157', 'JOINED', 1000.00, NOW() - INTERVAL '10 days');

    INSERT INTO public.app_payments (
        payment_type, payer_type, payer_id, payee_type, payee_id, app_hisaab_id, amount, payment_mode, status, cf_order_id, initiated_at, completed_at
    ) VALUES
        ('collection', 'driver', 1, 'letzryd', 1, 1, 750.00, 'cashfree_upi', 'SUCCESS', 'order_demo_1001', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day');

    -- STEP 0.4: Seed Fallback System Driver (Without public phone or driver_id so 404 test cases succeed)
    INSERT INTO public.app_drivers (
        driver_code, full_name, initials, is_active
    ) VALUES (
        'SYSTEM_ONBOARDED', 'System Onboarded Driver', 'SO', TRUE
    );

    -- STEP 1: Populate app_drivers from core_partner_onboarding (Individual Drivers)
    INSERT INTO public.app_drivers (
        driver_id,
        operator_id,
        full_name,
        phone,
        initials,
        driver_code,
        aadhar_number,
        dob,
        address,
        joined_date,
        emergency_name,
        emergency_relation,
        emergency_phone,
        dl_number,
        dl_expiry,
        deposit_total_req,
        deposit_paid,
        deposit_pending,
        upi_id,
        bank_account_last4,
        is_active,
        created_at,
        last_synced_at
    )
    SELECT DISTINCT ON (clean_phone)
        p.id,
        0 AS operator_id,
        TRIM(COALESCE(p.driver_name, 'Driver')),
        clean_phone,
        UPPER(SUBSTRING(TRIM(COALESCE(p.driver_name, 'DR')), 1, 2)),
        COALESCE(NULLIF(TRIM(p.partner_id), ''), 'DRV-' || p.id::text),
        NULLIF(TRIM(p.aadhaar_number), ''),
        CASE 
            WHEN EXTRACT(YEAR FROM p.dob) = 21992 THEN MAKE_DATE(1992, EXTRACT(MONTH FROM p.dob)::int, EXTRACT(DAY FROM p.dob)::int)
            WHEN EXTRACT(YEAR FROM p.dob) NOT BETWEEN 1920 AND 2026 THEN NULL
            ELSE p.dob
        END,
        COALESCE(NULLIF(TRIM(p.permanent_address), ''), NULLIF(TRIM(p.present_address), '')),
        COALESCE(p.onboarding_timestamp::DATE, p.created_at::DATE, CURRENT_DATE),
        NULLIF(TRIM(p.emergency_name), ''),
        NULLIF(TRIM(p.emergency_relationship), ''),
        RIGHT(REGEXP_REPLACE(COALESCE(p.emergency_phone, ''), '[^0-9]', '', 'g'), 10),
        NULLIF(TRIM(p.dl_number), ''),
        CASE 
            WHEN EXTRACT(YEAR FROM p.dl_expiry_date) BETWEEN 20 AND 99 THEN MAKE_DATE(2000 + EXTRACT(YEAR FROM p.dl_expiry_date)::int, EXTRACT(MONTH FROM p.dl_expiry_date)::int, EXTRACT(DAY FROM p.dl_expiry_date)::int)
            WHEN EXTRACT(YEAR FROM p.dl_expiry_date) NOT BETWEEN 2000 AND 2099 THEN NULL
            ELSE p.dl_expiry_date
        END,
        COALESCE(p.security_deposit, 5000.00),
        COALESCE(p.security_deposit, 5000.00),
        0.00,
        COALESCE(NULLIF(TRIM(p.upi_id), ''), clean_phone || '@upi'),
        RIGHT(REGEXP_REPLACE(COALESCE(p.account_number, '0000'), '[^0-9]', '', 'g'), 4),
        CASE WHEN p.is_deleted = TRUE THEN FALSE ELSE TRUE END,
        COALESCE(p.created_at, NOW()),
        NOW()
    FROM public.core_partner_onboarding p
    CROSS JOIN LATERAL (
        SELECT RIGHT(REGEXP_REPLACE(COALESCE(p.phone_number, ''), '[^0-9]', '', 'g'), 10) AS clean_phone
    ) cp
    WHERE LENGTH(cp.clean_phone) = 10
      AND cp.clean_phone NOT IN ('0000000000', '1234567890')
      AND (p.onboarding_type IS NULL OR p.onboarding_type NOT ILIKE '%operator%')
      AND p.driver_name NOT ILIKE '%TEST%'
      AND p.driver_name NOT ILIKE '%DUMMY%'
    ORDER BY clean_phone, p.id DESC
    ON CONFLICT (phone) DO NOTHING;

    -- Also populate any drivers in core_vehicle_allocation not yet in app_drivers
    INSERT INTO public.app_drivers (
        driver_id, operator_id, full_name, phone, initials, driver_code, is_active, created_at, last_synced_at
    )
    SELECT DISTINCT ON (cp.clean_phone)
        a.id::INT,
        0,
        TRIM(COALESCE(a.driver_name, 'Driver')),
        cp.clean_phone,
        UPPER(SUBSTRING(TRIM(COALESCE(a.driver_name, 'DR')), 1, 2)),
        'DRV-AL-' || a.id::text,
        TRUE,
        COALESCE(a.created_at, NOW()),
        NOW()
    FROM public.core_vehicle_allocation a
    CROSS JOIN LATERAL (
        SELECT RIGHT(REGEXP_REPLACE(COALESCE(a.driver_phone, ''), '[^0-9]', '', 'g'), 10) AS clean_phone
    ) cp
    WHERE LENGTH(cp.clean_phone) = 10
      AND cp.clean_phone NOT IN ('0000000000', '1234567890')
    ON CONFLICT (phone) DO NOTHING;

    -- Also populate any drivers referenced in hisaab_vehicle_weekly not yet in app_drivers
    INSERT INTO public.app_drivers (
        operator_id, full_name, phone, initials, driver_code, is_active, created_at, last_synced_at
    )
    SELECT DISTINCT ON (cph.clean_phone)
        0,
        'Driver ' || cph.clean_phone,
        cph.clean_phone,
        'DR',
        hw.partner_id,
        TRUE,
        NOW(),
        NOW()
    FROM public.hisaab_vehicle_weekly hw
    CROSS JOIN LATERAL (
        SELECT RIGHT(REGEXP_REPLACE(COALESCE(hw.partner_id, ''), '[^0-9]', '', 'g'), 10) AS clean_phone
    ) cph
    WHERE LENGTH(cph.clean_phone) = 10
      AND cph.clean_phone NOT IN ('0000000000', '1234567890')
    ON CONFLICT (phone) DO NOTHING;

    GET DIAGNOSTICS v_driver_count = ROW_COUNT;
    RAISE NOTICE 'Populated individual drivers into app_drivers.';

    -- STEP 2: Populate app_operators from core_partner_onboarding (Fleet Operators)
    INSERT INTO public.app_operators (
        operator_id,
        operator_code,
        operator_type,
        phone,
        company_name,
        contact_person_name,
        initials,
        address,
        deposit_total_req,
        deposit_paid,
        deposit_pending,
        upi_id,
        bank_account_last4,
        is_active,
        created_at,
        last_synced_at
    )
    SELECT DISTINCT ON (clean_phone)
        p.id,
        COALESCE(NULLIF(TRIM(p.partner_id), ''), 'OPR-' || p.id::text),
        'fleet_owner',
        clean_phone,
        TRIM(COALESCE(p.driver_name, 'Fleet Operator')),
        TRIM(COALESCE(p.driver_name, 'Fleet Operator')),
        UPPER(SUBSTRING(TRIM(COALESCE(p.driver_name, 'OP')), 1, 2)),
        COALESCE(NULLIF(TRIM(p.permanent_address), ''), NULLIF(TRIM(p.present_address), '')),
        COALESCE(p.security_deposit, 10000.00),
        COALESCE(p.security_deposit, 10000.00),
        0.00,
        COALESCE(NULLIF(TRIM(p.upi_id), ''), clean_phone || '@upi'),
        RIGHT(REGEXP_REPLACE(COALESCE(p.account_number, '0000'), '[^0-9]', '', 'g'), 4),
        CASE WHEN p.is_deleted = TRUE THEN FALSE ELSE TRUE END,
        COALESCE(p.created_at, NOW()),
        NOW()
    FROM public.core_partner_onboarding p
    CROSS JOIN LATERAL (
        SELECT RIGHT(REGEXP_REPLACE(COALESCE(p.phone_number, ''), '[^0-9]', '', 'g'), 10) AS clean_phone
    ) cp
    WHERE LENGTH(cp.clean_phone) = 10
      AND cp.clean_phone NOT IN ('0000000000', '1234567890')
      AND (
          p.onboarding_type ILIKE '%operator%'
          OR p.partner_id ILIKE '%OP%'
          OR p.partner_id ILIKE '%IP%'
          OR EXISTS (
              SELECT 1 FROM public.core_vehicle_allocation a
              WHERE RIGHT(REGEXP_REPLACE(COALESCE(a.driver_phone, ''), '[^0-9]', '', 'g'), 10) = cp.clean_phone
              GROUP BY a.driver_phone HAVING COUNT(DISTINCT a.vehicle_number) > 1
          )
      )
    ORDER BY clean_phone, p.id DESC
    ON CONFLICT (phone) DO NOTHING;

    GET DIAGNOSTICS v_op_count = ROW_COUNT;
    RAISE NOTICE 'Populated operators into app_operators.';

    -- STEP 3: Populate app_driver_allocations from core_vehicle_allocation & core_dropoffs
    INSERT INTO public.app_driver_allocations (
        core_allocation_id,
        app_driver_id,
        vehicle_number,
        allocation_date,
        dropoff_date,
        start_odometer,
        daily_rental_rate,
        allocation_status,
        assigned_city
    )
    SELECT 
        a.id,
        d.app_driver_id,
        UPPER(REGEXP_REPLACE(COALESCE(a.vehicle_number, ''), '[^A-Za-z0-9]', '', 'g')),
        a.allocation_date,
        dr.return_date,
        COALESCE(a.odometer_reading, 0),
        1000.00,
        CASE 
            WHEN dr.return_date IS NOT NULL AND dr.return_date >= a.allocation_date THEN 'RETURNED'
            WHEN a.is_deleted = TRUE THEN 'CLOSED'
            ELSE 'ACTIVE'
        END,
        a.city
    FROM public.core_vehicle_allocation a
    CROSS JOIN LATERAL (
        SELECT RIGHT(REGEXP_REPLACE(COALESCE(a.driver_phone, ''), '[^0-9]', '', 'g'), 10) AS clean_phone
    ) cp
    JOIN public.app_drivers d ON d.phone = cp.clean_phone
    LEFT JOIN LATERAL (
        SELECT r.return_date 
        FROM public.core_dropoffs r
        WHERE UPPER(REGEXP_REPLACE(COALESCE(r.vehicle_number, ''), '[^A-Za-z0-9]', '', 'g')) = UPPER(REGEXP_REPLACE(COALESCE(a.vehicle_number, ''), '[^A-Za-z0-9]', '', 'g'))
          AND r.return_date >= a.allocation_date
          AND (r.is_deleted = FALSE OR r.is_deleted IS NULL)
        ORDER BY r.return_date ASC LIMIT 1
    ) dr ON TRUE
    WHERE a.is_deleted = FALSE OR a.is_deleted IS NULL;

    GET DIAGNOSTICS v_alloc_count = ROW_COUNT;
    RAISE NOTICE 'Populated % allocation contracts into app_driver_allocations.', v_alloc_count;

    -- STEP 4: Enrich app_drivers with current vehicle & vehicle specs from core_vehicle_onboarding
    UPDATE public.app_drivers d
    SET 
        vehicle_reg_number = COALESCE(d.vehicle_reg_number, best_veh.vehicle_number),
        vehicle_allocated_from = COALESCE(d.vehicle_allocated_from, best_veh.allocation_date),
        vehicle_odometer_km = COALESCE(d.vehicle_odometer_km, best_veh.start_odometer),
        vehicle_make = COALESCE(d.vehicle_make, vo.registered_owner_name, vo.dealer_name, 'Maruti'),
        vehicle_model = COALESCE(d.vehicle_model, vo.model, 'Dzire CNG'),
        vehicle_variant = COALESCE(d.vehicle_variant, vo.model, 'VXi'),
        vehicle_color = COALESCE(d.vehicle_color, vo.color, 'White'),
        vehicle_fuel_type = COALESCE(d.vehicle_fuel_type, vo.fuel_type, 'CNG'),
        rc_number = COALESCE(d.rc_number, best_veh.vehicle_number),
        rc_expiry = CASE WHEN EXTRACT(YEAR FROM vo.rto_tax_validity) BETWEEN 2000 AND 2099 THEN vo.rto_tax_validity ELSE d.rc_expiry END,
        insurance_expiry = CASE WHEN EXTRACT(YEAR FROM vo.insurance_validity) BETWEEN 2000 AND 2099 THEN vo.insurance_validity ELSE d.insurance_expiry END,
        permit_type = COALESCE(d.permit_type, vo.permit_type),
        permit_expiry = CASE WHEN EXTRACT(YEAR FROM vo.permit_validity) BETWEEN 2000 AND 2099 THEN vo.permit_validity ELSE d.permit_expiry END,
        fitness_expiry = CASE WHEN EXTRACT(YEAR FROM vo.fitness_validity) BETWEEN 2000 AND 2099 THEN vo.fitness_validity ELSE d.fitness_expiry END,
        puc_expiry = CASE WHEN EXTRACT(YEAR FROM vo.pollution_validity) BETWEEN 2000 AND 2099 THEN vo.pollution_validity ELSE d.puc_expiry END,
        last_synced_at = NOW()
    FROM (
        SELECT DISTINCT ON (app_driver_id)
            app_driver_id,
            vehicle_number,
            allocation_date,
            start_odometer
        FROM public.app_driver_allocations
        ORDER BY app_driver_id, 
                 CASE WHEN allocation_status = 'ACTIVE' THEN 1 ELSE 2 END,
                 allocation_date DESC
    ) best_veh
    LEFT JOIN public.core_vehicle_onboarding vo 
      ON UPPER(REGEXP_REPLACE(COALESCE(vo.registration_no, ''), '[^A-Za-z0-9]', '', 'g')) = best_veh.vehicle_number
    WHERE d.app_driver_id = best_veh.app_driver_id;

    -- STEP 4.1: Enrich app_drivers.operator_id from core_vehicle_allocation & app_operators
    UPDATE public.app_drivers d
    SET operator_id = op_match.app_operator_id
    FROM (
        SELECT DISTINCT ON (d2.app_driver_id)
            d2.app_driver_id,
            op.app_operator_id
        FROM public.app_drivers d2
        JOIN public.core_vehicle_allocation cva ON (
            RIGHT(REGEXP_REPLACE(COALESCE(cva.driver_phone, ''), '[^0-9]', '', 'g'), 10) = d2.phone
            OR (d2.vehicle_reg_number IS NOT NULL AND d2.vehicle_reg_number != '' AND UPPER(REGEXP_REPLACE(cva.vehicle_number, '[^A-Za-z0-9]', '', 'g')) = d2.vehicle_reg_number)
        )
        JOIN public.app_operators op ON (
            op.operator_code = cva.partner_id
            OR op.phone = RIGHT(REGEXP_REPLACE(cva.partner_id, '[^0-9]', '', 'g'), 10)
        )
        WHERE cva.partner_type = 'Operator'
        ORDER BY d2.app_driver_id, cva.allocation_date DESC NULLS LAST, cva.id DESC
    ) op_match
    WHERE d.app_driver_id = op_match.app_driver_id AND d.app_driver_id > 6;

    -- STEP 5: Populate app_driver_bank_accounts from core_partner_onboarding
    INSERT INTO public.app_driver_bank_accounts (
        app_driver_id,
        account_number,
        ifsc_code,
        account_holder_name,
        bank_name,
        upi_id,
        is_primary,
        is_verified,
        verification_status
    )
    SELECT DISTINCT ON (d.app_driver_id)
        d.app_driver_id,
        SUBSTRING(TRIM(p.account_number), 1, 100),
        SUBSTRING(UPPER(TRIM(p.ifsc_code)), 1, 100),
        SUBSTRING(TRIM(COALESCE(p.account_name, p.driver_name, 'Account Holder')), 1, 150),
        SUBSTRING(TRIM(COALESCE(p.bank_name, 'Bank')), 1, 150),
        d.upi_id,
        TRUE,
        TRUE,
        'VERIFIED'
    FROM public.app_drivers d
    JOIN public.core_partner_onboarding p 
      ON RIGHT(REGEXP_REPLACE(COALESCE(p.phone_number, ''), '[^0-9]', '', 'g'), 10) = d.phone
    WHERE NULLIF(TRIM(p.account_number), '') IS NOT NULL
      AND NULLIF(TRIM(p.ifsc_code), '') IS NOT NULL
    ON CONFLICT (account_number, ifsc_code) DO NOTHING;

    GET DIAGNOSTICS v_bank_count = ROW_COUNT;
    RAISE NOTICE 'Populated verified bank accounts into app_driver_bank_accounts.';

    -- STEP 6: Populate app_hisaabs from hisaab_vehicle_weekly & hisaab_settlement_weeks
    INSERT INTO public.app_hisaabs (
        app_driver_id,
        app_operator_id,
        hisaab_number,
        week_number,
        period_start,
        period_end,
        days_count,
        status,
        is_locked,
        uber_trips,
        uber_revenue,
        uber_cash,
        uber_toll,
        uber_incentive,
        uber_subscription,
        ola_trips,
        ola_revenue,
        ola_cash,
        ola_toll,
        ola_incentive,
        vehicle_daily_rate,
        vehicle_rent,
        tds_amount,
        challan_amount,
        accident_charge,
        other_adjustment,
        gps_dead_km,
        gps_dead_penalty,
        completed_trips,
        total_gross_earnings,
        total_deductions,
        current_period_os,
        to_pay,
        to_collect,
        created_at,
        updated_at
    )
    SELECT 
        COALESCE(d_phone.app_driver_id, d_code.app_driver_id, d_alloc.app_driver_id, d_sys.app_driver_id) AS app_driver_id,
        CASE WHEN COALESCE(d_phone.app_driver_id, 0) > 6 THEN COALESCE(d_phone.operator_id, 0) ELSE 0 END AS app_operator_id,
        'HSB-' || hw.week_id || '-' || UPPER(REGEXP_REPLACE(hw.vehicle_number, '[^A-Za-z0-9]', '', 'g')) || '-' || UPPER(REGEXP_REPLACE(COALESCE(NULLIF(TRIM(hw.partner_id), ''), hw.id::text), '[^A-Za-z0-9]', '', 'g')),
        COALESCE(sw.settlement_week, (SUBSTRING(hw.week_id FROM '[0-9]+$'))::INT, 28),
        hw.week_start,
        hw.week_end,
        COALESCE(hw.onroad_days::INT, hw.allotted_days::INT, 7),
        CASE 
            WHEN hw.net_to_collect_from_driver > 0 THEN 'to_collect'
            WHEN hw.net_payout_to_driver > 0 THEN 'to_pay'
            ELSE 'settled'
        END,
        COALESCE(sw.is_locked, FALSE),
        hw.uber_trips,
        hw.uber_total_earnings,
        hw.uber_cash_collection,
        hw.uber_toll,
        hw.uber_incentive,
        hw.uber_driver_sub_charge,
        hw.ola_trips,
        hw.ola_net_revenue,
        hw.ola_cash_collection,
        hw.ola_toll,
        hw.ola_incentive,
        hw.daily_rent_applied,
        hw.net_weekly_lease_rental,
        hw.tds_amount,
        hw.challan_amount,
        hw.accident_deduction,
        hw.adjustment_amount,
        hw.gps_dead_km,
        hw.gps_dead_mile_penalty,
        hw.uber_trips + hw.ola_trips,
        hw.uber_total_earnings + hw.uber_incentive + hw.ola_net_revenue + hw.ola_incentive,
        hw.net_weekly_lease_rental + hw.tds_amount + hw.challan_amount + hw.accident_deduction + hw.gps_dead_mile_penalty - hw.adjustment_amount,
        hw.current_week_os,
        hw.net_payout_to_driver,
        hw.net_to_collect_from_driver,
        NOW(),
        NOW()
    FROM public.hisaab_vehicle_weekly hw
    LEFT JOIN public.hisaab_settlement_weeks sw ON sw.week_id = hw.week_id
    CROSS JOIN LATERAL (
        SELECT RIGHT(REGEXP_REPLACE(COALESCE(hw.partner_id, ''), '[^0-9]', '', 'g'), 10) AS ph
    ) cph
    LEFT JOIN public.app_drivers d_phone ON LENGTH(cph.ph) = 10 AND d_phone.phone = cph.ph
    LEFT JOIN public.app_drivers d_code ON d_code.driver_code = hw.partner_id
    LEFT JOIN LATERAL (
        SELECT da.app_driver_id 
        FROM public.app_driver_allocations da
        WHERE da.vehicle_number = UPPER(REGEXP_REPLACE(hw.vehicle_number, '[^A-Za-z0-9]', '', 'g'))
          AND da.allocation_date <= COALESCE(hw.week_end, CURRENT_DATE)
          AND (da.dropoff_date IS NULL OR da.dropoff_date >= COALESCE(hw.week_start, CURRENT_DATE))
        ORDER BY da.allocation_date DESC
        LIMIT 1
    ) d_alloc ON TRUE
    LEFT JOIN public.app_drivers d_sys ON d_sys.driver_code = 'SYSTEM_ONBOARDED'
    ON CONFLICT (hisaab_number) DO UPDATE SET
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

    GET DIAGNOSTICS v_hisaab_count = ROW_COUNT;
    RAISE NOTICE 'Populated % Hisaabs into app_hisaabs.', v_hisaab_count;

    -- STEP 7: Update driver current week (cw_*) and last week (lw_*) rollup metrics
    -- Only for drivers other than the 6 core demo drivers
    UPDATE public.app_drivers d
    SET
        cw_uber_trips = latest_h.uber_trips,
        cw_uber_revenue = latest_h.uber_revenue,
        cw_uber_cash = latest_h.uber_cash,
        cw_uber_toll = latest_h.uber_toll,
        cw_uber_incentive = latest_h.uber_incentive,
        cw_ola_trips = latest_h.ola_trips,
        cw_ola_revenue = latest_h.ola_revenue,
        cw_ola_cash = latest_h.ola_cash,
        cw_ola_toll = latest_h.ola_toll,
        cw_ola_incentive = latest_h.ola_incentive,
        cw_vehicle_rent = latest_h.vehicle_rent,
        cw_active_days = latest_h.days_count,
        cw_tds = latest_h.tds_amount,
        cw_challans = latest_h.challan_amount,
        cw_accident_charge = latest_h.accident_charge,
        cw_other_adjustment = latest_h.other_adjustment,
        cw_gps_dead_km = latest_h.gps_dead_km,
        cw_gps_dead_penalty = latest_h.gps_dead_penalty,
        cw_trips = latest_h.completed_trips,
        cw_gross_earnings = latest_h.total_gross_earnings,
        cw_total_deductions = latest_h.total_deductions,
        cw_os = latest_h.current_period_os,
        cw_to_pay = latest_h.to_pay,
        cw_to_collect = latest_h.to_collect,
        cumulative_owed = ABS(latest_h.to_pay),
        lw_hisaab_number = latest_h.hisaab_number,
        lw_status = latest_h.status,
        last_synced_at = NOW()
    FROM (
        SELECT DISTINCT ON (app_driver_id)
            *
        FROM public.app_hisaabs
        ORDER BY app_driver_id, week_number DESC, app_hisaab_id DESC
    ) latest_h
    WHERE d.app_driver_id = latest_h.app_driver_id
      AND d.app_driver_id > 6;

    -- STEP 8: Update operator fleet summaries (active_vehicles, total_vehicles, cw_fleet_*)
    -- Only for operators other than operator 1 & 2
    UPDATE public.app_operators op
    SET
        total_vehicles = COALESCE(fc.v_count, 0),
        active_vehicles = COALESCE(fc.v_active, 0),
        idle_vehicles = GREATEST(0, COALESCE(fc.v_count, 0) - COALESCE(fc.v_active, 0)),
        total_drivers = COALESCE(fc.d_count, 0),
        cw_fleet_uber_trips = COALESCE(fs.u_trips, 0),
        cw_fleet_uber_revenue = COALESCE(fs.u_rev, 0.0),
        cw_fleet_ola_trips = COALESCE(fs.o_trips, 0),
        cw_fleet_ola_revenue = COALESCE(fs.o_rev, 0.0),
        cw_fleet_gross_earnings = COALESCE(fs.gross, 0.0),
        cw_to_collect = COALESCE(fs.to_collect, 0.0),
        cw_to_pay = COALESCE(fs.to_pay, 0.0),
        cw_fleet_net_os = COALESCE(fs.os, 0.0),
        last_synced_at = NOW()
    FROM (
        SELECT 
            app_operator_id,
            COUNT(DISTINCT vehicle_number) AS v_count,
            COUNT(DISTINCT CASE WHEN allocation_status = 'ACTIVE' THEN vehicle_number END) AS v_active,
            COUNT(DISTINCT app_driver_id) AS d_count
        FROM public.app_driver_allocations
        GROUP BY app_operator_id
    ) fc
    LEFT JOIN (
        SELECT 
            app_operator_id,
            SUM(uber_trips) AS u_trips,
            SUM(uber_revenue) AS u_rev,
            SUM(ola_trips) AS o_trips,
            SUM(ola_revenue) AS o_rev,
            SUM(total_gross_earnings) AS gross,
            SUM(to_collect) AS to_collect,
            SUM(to_pay) AS to_pay,
            SUM(current_period_os) AS os
        FROM public.app_hisaabs
        GROUP BY app_operator_id
    ) fs ON fs.app_operator_id = fc.app_operator_id
    WHERE op.app_operator_id = fc.app_operator_id
      AND op.app_operator_id > 2;

    RAISE NOTICE 'App Tables population completed successfully!';
END;
$procedure$;


-- ------------------------------------------------------------------------------
-- PART 3: REAL-TIME AUTOMATION EVENT TRIGGERS
-- ------------------------------------------------------------------------------

-- 3.1 TRIGGER FUNCTION: Sync core_partner_onboarding to app_drivers & app_operators
CREATE OR REPLACE FUNCTION public.fn_trg_sync_core_partner_to_app()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $function$
DECLARE
    v_clean_phone VARCHAR(15);
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_clean_phone := RIGHT(REGEXP_REPLACE(COALESCE(OLD.phone_number, ''), '[^0-9]', '', 'g'), 10);
        UPDATE public.app_drivers SET is_active = FALSE WHERE phone = v_clean_phone;
        UPDATE public.app_operators SET is_active = FALSE WHERE phone = v_clean_phone;
        RETURN OLD;
    END IF;

    v_clean_phone := RIGHT(REGEXP_REPLACE(COALESCE(NEW.phone_number, ''), '[^0-9]', '', 'g'), 10);
    IF LENGTH(v_clean_phone) = 10 AND v_clean_phone NOT IN ('0000000000', '1234567890') THEN
        IF NEW.onboarding_type ILIKE '%operator%' OR NEW.partner_id ILIKE '%OP%' OR NEW.partner_id ILIKE '%IP%' THEN
            INSERT INTO public.app_operators (
                operator_id, operator_code, phone, company_name, contact_person_name, initials,
                address, deposit_total_req, deposit_paid, upi_id, is_active, last_synced_at
            ) VALUES (
                NEW.id,
                COALESCE(NULLIF(TRIM(NEW.partner_id), ''), 'OPR-' || NEW.id::text),
                v_clean_phone,
                TRIM(COALESCE(NEW.driver_name, 'Fleet Operator')),
                TRIM(COALESCE(NEW.driver_name, 'Fleet Operator')),
                UPPER(SUBSTRING(TRIM(COALESCE(NEW.driver_name, 'OP')), 1, 2)),
                COALESCE(NULLIF(TRIM(NEW.permanent_address), ''), NULLIF(TRIM(NEW.present_address), '')),
                COALESCE(NEW.security_deposit, 10000.00),
                COALESCE(NEW.security_deposit, 10000.00),
                COALESCE(NULLIF(TRIM(NEW.upi_id), ''), v_clean_phone || '@upi'),
                CASE WHEN NEW.is_deleted = TRUE THEN FALSE ELSE TRUE END,
                NOW()
            )
            ON CONFLICT (phone) DO UPDATE SET
                company_name = EXCLUDED.company_name,
                contact_person_name = EXCLUDED.contact_person_name,
                is_active = EXCLUDED.is_active,
                deposit_total_req = EXCLUDED.deposit_total_req,
                last_synced_at = NOW();
        ELSE
            INSERT INTO public.app_drivers (
                driver_id, full_name, phone, initials, driver_code, aadhar_number, dob, address,
                joined_date, emergency_name, emergency_relation, emergency_phone, dl_number, dl_expiry,
                deposit_total_req, deposit_paid, deposit_pending, upi_id, is_active, last_synced_at
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
                COALESCE(NEW.security_deposit, 5000.00),
                COALESCE(NEW.security_deposit, 5000.00),
                0.00,
                COALESCE(NULLIF(TRIM(NEW.upi_id), ''), v_clean_phone || '@upi'),
                CASE WHEN NEW.is_deleted = TRUE THEN FALSE ELSE TRUE END,
                NOW()
            )
            ON CONFLICT (phone) DO UPDATE SET
                full_name = EXCLUDED.full_name,
                aadhar_number = EXCLUDED.aadhar_number,
                dl_number = EXCLUDED.dl_number,
                dl_expiry = EXCLUDED.dl_expiry,
                is_active = EXCLUDED.is_active,
                deposit_total_req = EXCLUDED.deposit_total_req,
                last_synced_at = NOW();
        END IF;

        IF NULLIF(TRIM(NEW.account_number), '') IS NOT NULL AND NULLIF(TRIM(NEW.ifsc_code), '') IS NOT NULL THEN
            INSERT INTO public.app_driver_bank_accounts (
                app_driver_id, account_number, ifsc_code, account_holder_name, bank_name, upi_id
            )
            SELECT 
                d.app_driver_id,
                SUBSTRING(TRIM(NEW.account_number), 1, 100),
                SUBSTRING(UPPER(TRIM(NEW.ifsc_code)), 1, 100),
                SUBSTRING(TRIM(COALESCE(NEW.account_name, NEW.driver_name, 'Account Holder')), 1, 150),
                SUBSTRING(TRIM(COALESCE(NEW.bank_name, 'Bank')), 1, 150),
                COALESCE(NULLIF(TRIM(NEW.upi_id), ''), v_clean_phone || '@upi')
            FROM public.app_drivers d WHERE d.phone = v_clean_phone
            ON CONFLICT (account_number, ifsc_code) DO NOTHING;
        END IF;
    END IF;

    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS trg_sync_core_partner_to_app ON public.core_partner_onboarding;
CREATE TRIGGER trg_sync_core_partner_to_app
AFTER INSERT OR UPDATE OR DELETE ON public.core_partner_onboarding
FOR EACH ROW EXECUTE FUNCTION public.fn_trg_sync_core_partner_to_app();


-- 3.2 TRIGGER FUNCTION: Sync core_vehicle_allocation to app_driver_allocations & app_drivers
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

DROP TRIGGER IF EXISTS trg_sync_core_allocation_to_app ON public.core_vehicle_allocation;
CREATE TRIGGER trg_sync_core_allocation_to_app
AFTER INSERT OR UPDATE OR DELETE ON public.core_vehicle_allocation
FOR EACH ROW EXECUTE FUNCTION public.fn_trg_sync_allocation_to_app();


-- 3.3 TRIGGER FUNCTION: Sync core_dropoffs to app_driver_allocations
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
        -- Guard seed drivers (1-4) and drivers with newer active allocations
        UPDATE public.app_drivers
        SET 
            vehicle_reg_number = NULL,
            current_vehicle_id = NULL,
            last_synced_at = NOW()
        WHERE vehicle_reg_number = v_veh_num
          AND app_driver_id > 4
          AND (vehicle_allocated_from IS NULL OR vehicle_allocated_from <= NEW.return_date)
          AND NOT EXISTS (
              SELECT 1 FROM public.app_driver_allocations a
              WHERE a.app_driver_id = app_drivers.app_driver_id
                AND a.allocation_status = 'ACTIVE'
                AND a.allocation_date > NEW.return_date
          );
    END IF;

    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS trg_sync_core_dropoffs_to_app ON public.core_dropoffs;
CREATE TRIGGER trg_sync_core_dropoffs_to_app
AFTER INSERT OR UPDATE ON public.core_dropoffs
FOR EACH ROW EXECUTE FUNCTION public.fn_trg_sync_dropoffs_to_app();


-- 3.4 TRIGGER FUNCTION: Sync core_vehicle_onboarding to app_drivers
CREATE OR REPLACE FUNCTION public.fn_trg_sync_vehicle_onboarding_to_app()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $function$
DECLARE
    v_veh_num VARCHAR(20);
BEGIN
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    v_veh_num := UPPER(REGEXP_REPLACE(COALESCE(NEW.registration_no, ''), '[^A-Za-z0-9]', '', 'g'));

    IF v_veh_num != '' THEN
        UPDATE public.app_drivers
        SET 
            vehicle_make = COALESCE(NEW.registered_owner_name, NEW.dealer_name, vehicle_make),
            vehicle_model = COALESCE(NEW.model, vehicle_model),
            vehicle_color = COALESCE(NEW.color, vehicle_color),
            vehicle_fuel_type = COALESCE(NEW.fuel_type, vehicle_fuel_type),
            rc_number = v_veh_num,
            rc_expiry = CASE WHEN EXTRACT(YEAR FROM NEW.rto_tax_validity) BETWEEN 2000 AND 2099 THEN NEW.rto_tax_validity ELSE rc_expiry END,
            insurance_expiry = CASE WHEN EXTRACT(YEAR FROM NEW.insurance_validity) BETWEEN 2000 AND 2099 THEN NEW.insurance_validity ELSE insurance_expiry END,
            permit_type = COALESCE(NEW.permit_type, permit_type),
            permit_expiry = CASE WHEN EXTRACT(YEAR FROM NEW.permit_validity) BETWEEN 2000 AND 2099 THEN NEW.permit_validity ELSE permit_expiry END,
            fitness_expiry = CASE WHEN EXTRACT(YEAR FROM NEW.fitness_validity) BETWEEN 2000 AND 2099 THEN NEW.fitness_validity ELSE fitness_expiry END,
            puc_expiry = CASE WHEN EXTRACT(YEAR FROM NEW.pollution_validity) BETWEEN 2000 AND 2099 THEN NEW.pollution_validity ELSE puc_expiry END,
            last_synced_at = NOW()
        WHERE vehicle_reg_number = v_veh_num;
    END IF;

    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS trg_sync_vehicle_onboarding_to_app ON public.core_vehicle_onboarding;
CREATE TRIGGER trg_sync_vehicle_onboarding_to_app
AFTER INSERT OR UPDATE ON public.core_vehicle_onboarding
FOR EACH ROW EXECUTE FUNCTION public.fn_trg_sync_vehicle_onboarding_to_app();


-- 3.5 TRIGGER FUNCTION: Sync hisaab_vehicle_weekly to app_hisaabs & app_drivers
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

DROP TRIGGER IF EXISTS trg_sync_hisaab_vehicle_to_app ON public.hisaab_vehicle_weekly;
CREATE TRIGGER trg_sync_hisaab_vehicle_to_app
AFTER INSERT OR UPDATE OR DELETE ON public.hisaab_vehicle_weekly
FOR EACH ROW EXECUTE FUNCTION public.fn_trg_sync_hisaab_vehicle_to_app();

-- ==============================================================================
-- END OF APP TABLES SCHEMA, STORED PROCEDURES & TRIGGERS
-- ==============================================================================
