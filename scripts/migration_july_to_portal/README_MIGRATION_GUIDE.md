# LetzRyd Database Migration: `july_*` to `portal_*` Runbook

## 1. Executive Summary & Context
In earlier milestones, internal staff forms, user authentication, and intake workflows were prefixed with `july_` (e.g. `july_form_onboarding`, `july_vehicle_dropoffs`, `july_portal_users`). As LetzRyd scales, these tables are officially designated as the **Portal Layer** (`portal_*`).

This directory contains the production-ready migration scripts to rename all 55 physical tables and 2 views while guaranteeing **zero downtime** across all active fleet ingestion pipelines, Cloud Run services, and 18 `pg_cron` jobs.

---

## 2. Directory Structure & Script Index

| Script File | Purpose | Execution Timing |
| :--- | :--- | :--- |
| [`01_rename_tables_and_create_bridge_views.sql`](./01_rename_tables_and_create_bridge_views.sql) | Idempotently renames 55 base tables to `portal_*` and immediately creates 55 updatable `july_*` bridge views. | **Step 1 (First)** |
| [`02_update_views_and_routines.sql`](./02_update_views_and_routines.sql) | Re-creates 4 database views, 18 stored procedures/functions, and re-attaches triggers to point directly to `portal_*`. | **Step 2 (Immediate Follow-up)** |
| [`03_verify_migration.sql`](./03_verify_migration.sql) | Runs automated data parity, trigger attachment, and scheduler health validation checks. | **Step 3 (Post-Migration Verification)** |
| [`04_cleanup_drop_bridge_views.sql`](./04_cleanup_drop_bridge_views.sql) | Drops the temporary `july_*` compatibility views once all backend repos are deployed. | **Step 4 (1–2 weeks later)** |

---

## 3. Deep-Dive: How the Zero-Downtime Migration Works

### A. The "Bridge View" Pattern
When you execute `ALTER TABLE july_form_onboarding RENAME TO portal_form_onboarding;`, the physical table changes immediately. If any external script or background process queries `july_form_onboarding`, PostgreSQL normally throws:
```text
ERROR: relation "july_form_onboarding" does not exist (SQLSTATE 42P01)
```
To eliminate this risk, Script 01 immediately executes:
```sql
CREATE OR REPLACE VIEW public.july_form_onboarding AS 
SELECT * FROM public.portal_form_onboarding;
```
In PostgreSQL, simple views that map 1:1 to a base table are **automatically updatable**. This means:
- `SELECT` queries continue to read real-time data from `portal_form_onboarding`.
- `INSERT`, `UPDATE`, and `DELETE` queries executed by older scripts or un-restarted workers continue to succeed through the view.

### B. Foreign Keys & Indexes
- **Foreign Keys**: In PostgreSQL, foreign keys track relation OIDs, not names. When `july_roles` is renamed to `portal_roles`, foreign keys pointing to it (e.g. from `july_employees`) **automatically follow the rename** without breaking.
- **Primary Key Sequences**: Bigserial/serial sequences attached to table default values continue to increment seamlessly.

### C. Why PL/pgSQL Procedures Must Be Updated (Script 02)
Unlike foreign keys, PostgreSQL stores procedural code (`FUNCTION` and `PROCEDURE` bodies) as **unparsed text**. 
When a table is renamed, the text inside `refresh_core_partner_onboarding()` still says:
```sql
SELECT ... FROM public.july_form_onboarding;
```
While the bridge view allows the query to run, Script 02 updates the routine bodies to query `portal_*` directly, updates trigger function definitions (`fn_sync_portal_*`), and attaches fresh triggers on `portal_*`.

---

## 4. Execution Guide: Step-by-Step

### Phase 1: DEV Database Validation (Mandatory Step 1)
Target Instance: `34.93.205.164:5432/letzryd_dev`

```bash
# 1. Connect and execute Script 01 (Rename & Bridge Views)
psql "postgresql://letzryd_dev_user:<DEV_PASSWORD>@34.93.205.164:5432/letzryd_dev" -f 01_rename_tables_and_create_bridge_views.sql

# 2. Execute Script 02 (Procedures, Views & Triggers)
psql "postgresql://letzryd_dev_user:<DEV_PASSWORD>@34.93.205.164:5432/letzryd_dev" -f 02_update_views_and_routines.sql

# 3. Run Verification Suite
psql "postgresql://letzryd_dev_user:<DEV_PASSWORD>@34.93.205.164:5432/letzryd_dev" -f 03_verify_migration.sql
```

**What to verify in DEV:**
1. Script 03 reports `PASS (Exact Match)` for row counts between base tables and bridge views.
2. Manually test stored procedures:
   ```sql
   CALL public.refresh_core_partner_onboarding();
   CALL public.refresh_core_dropoffs();
   CALL public.refresh_core_adjustments();
   ```
3. Check `cron.job_run_details` to verify that `pg_cron` jobs execute with status `succeeded`.

---

### Phase 2: PROD Database Execution
Target Instance: `35.200.196.113:5432/postgres`

```bash
# 1. Execute Script 01
psql "postgresql://postgres:<PROD_PASSWORD>@35.200.196.113:5432/postgres" -f 01_rename_tables_and_create_bridge_views.sql

# 2. Execute Script 02
psql "postgresql://postgres:<PROD_PASSWORD>@35.200.196.113:5432/postgres" -f 02_update_views_and_routines.sql

# 3. Run Verification Suite
psql "postgresql://postgres:<PROD_PASSWORD>@35.200.196.113:5432/postgres" -f 03_verify_migration.sql
```

---

## 5. GitHub Repositories Update Checklist

Once the database migration is applied (with bridge views keeping everything running), update the application code across the repositories:

### Repo 1: `cashfree-web_portal`
- [ ] `api.py`:
  - Update `_ENSURE_TABLES_SQL` (`july_ola_raw` $\to$ `portal_ola_raw`, `july_driver_users` $\to$ `portal_driver_users`, etc.).
  - Update table names in queries in `/api/ola/summary`, `/api/driver/profile`, `/api/operator/profile`, `/api/hisaab/calculated`.
- [ ] `ola-sync/`:
  - `load_to_postgres.py`, `parse_ola_statement.py`, `fetch_ola_statement.py`.

### Repo 2: `backend` (`backend_repo/`)
- [ ] `Partner Onboarding Final Table/schema.sql` & `automation_script.py`
- [ ] `Vehicle Dropoff Final Table/schema.sql` & `automation_script.py`
- [ ] `Walkin Final Table/schema.sql` & `automation_script.py`
- [ ] `Adjustments Final Table/schema.sql` & `automation_script.py`
- [ ] `Maintenance Final Table/schema.sql` & `automation_script.py`
- [ ] `Vehicle Allocation Final Table/schema.sql` & `automation_script.py`
- [ ] `Vehicle Onboarding Final Table/schema.sql` & `automation_script.py`
- [ ] `Accidents Google Sheet/schema.sql` & `automation_script.py`

### Repo 3: Staff Web Portal Backend (`letzryd-portal` on Cloud Run)
- [ ] Update ORM models / SQL queries for form submissions.
- [ ] Deploy new revision to Cloud Run (`letzryd-portal-925756819101.asia-south1.run.app`).

---

## 6. Phase 4 Cleanup (Post-Deployment)
Once all services, pipelines, and webhooks have been updated to query `portal_*` and monitoring shows zero hits on `july_*` for 7–14 days:
```bash
psql "<CONNECTION_URI>" -f 04_cleanup_drop_bridge_views.sql
```
