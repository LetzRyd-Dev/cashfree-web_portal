# LetzRyd Partner Settlement Portal — Master Engineering Reference

> Complete technical architecture, live URLs, 10 database tables, team profiles, Firebase Phone Auth, Cloud SQL, Cloud Run & Vercel deployment reference.

---

## 1. Master URLs, Domains, Ports & Resource Directory

| Resource / Component | URL / Path / Port | Authentication / Protocol / Notes |
| :--- | :--- | :--- |
| **Frontend (Vercel)** | `https://cashfree-web-portal.vercel.app` | HTTPS \| React 19 Single Page App |
| **Full App (Cloud Run)** | `https://cashfree-web-portal-925756819101.asia-south1.run.app` | HTTPS \| Serves React Frontend + FastAPI on port 8080 |
| **Local Frontend** | `http://127.0.0.1:3002` (or `http://localhost:3002`) | HTTP \| Vite Dev Server (`vite --port=3002 --host=0.0.0.0`) |
| **Local Backend API** | `http://127.0.0.1:8000` (or `http://localhost:8000`) | HTTP \| FastAPI Uvicorn Server |
| **PostgreSQL Cloud SQL** | `35.200.196.113:5432` | TCP PostgreSQL \| DB: `postgres` \| User: `postgres` |
| **GitHub Repository** | `https://github.com/aayush-letzryd/cashfree-web_portal` | Git remote origin \| Branch: `main` |
| **Google Cloud Project** | `letzryd-dev-test` (Project Number: `925756819101`) | GCP Console \| Region: `asia-south1` (Mumbai) |
| **Firebase Auth Domain** | `letzryd-dev-test.firebaseapp.com` | Google Identity Platform (Phone Auth Provider) |
| **Cloud Shell Terminal** | `https://shell.cloud.google.com/?project=letzryd-dev-test` | GCP bash console for builds & deployments |

---

## 2. System Architecture & End-to-End Data Flow

```
+---------------------------------------------------------------------------------------------------------+
|                                        CLIENT DEVICES (Drivers & Operators)                             |
|                                                                                                         |
|   Driver Interface (Mobile / PWA)                       Operator Interface (Desktop / Tablet)           |
|   - Weekly Hisaab Breakdown & Settlements               - 4-Vehicle Fleet Live Overview                 |
|   - Rent Deductions, Challans, TDS, Fuel                - Driver Allocation & Weekly Ledger             |
|   - Emergency SOS Alarm & Support Desk                  - Cashfree Payout Processing                    |
+---------------------------------------------------+-----------------------------------------------------+
                                                    |
                         +--------------------------+--------------------------+
                         |                                                     |
                         v                                                     v
+------------------------------------------------+    +--------------------------------------------------+
|           VERCEL EDGE DEPLOYMENT               |    |          GOOGLE CLOUD RUN DEPLOYMENT             |
|          cashfree-web-portal.vercel.app        |    |   cashfree-web-portal-925756819101.run.app       |
|                                                |    |                                                  |
|   * Static React 19 Frontend Bundle            |    |   * Multi-Stage Docker Container (Port 8080)     |
|   * Auto-deploys on push to GitHub 'main'      |    |   * Serves React Frontend from /dist             |
|   * Calls Cloud Run via VITE_BACKEND_URL       |    |   * Serves FastAPI Backend from /api/*           |
|   * Built-in Client Data Engine Fallback       |    |   * Internal Database Connection Pool            |
+-----------------------+------------------------+    +------------------------+-------------------------+
                        |                                                      |
                        +--------------------------+---------------------------+
                                                   |
                         +-------------------------+-------------------------+
                         |                                                   |
                         v                                                   v
+------------------------------------------------+    +--------------------------------------------------+
|           FIREBASE PHONE AUTHENTICATION        |    |           FASTAPI APPLICATION BACKEND            |
|                                                |    |                                                  |
|   * Project: letzryd-dev-test (925756819101)   |    |   * Auth Router (/api/auth/otp/verify)           |
|   * Telecom Cellular SMS (+91 India)           |    |   * Drivers Router (/api/drivers/*)              |
|   * Invisible reCAPTCHA on #recaptcha-container|    |   * Operators Router (/api/operators/*)          |
|   * Master Bypass Auth Code: 1234              |    |   * Hisaabs Router (/api/hisaabs/*)              |
+------------------------------------------------+    +------------------------+-------------------------+
                                                                               |
                                                                               v
                                                      +--------------------------------------------------+
                                                      |           POSTGRESQL CLOUD SQL DATABASE          |
                                                      |           Host: 35.200.196.113:5432              |
                                                      |           Database: postgres                     |
                                                      |                                                  |
                                                      |   * app_drivers (Driver profiles & balances)     |
                                                      |   * app_operators (Fleet operator accounts)      |
                                                      |   * app_operator_vehicles (4-vehicle mappings)   |
                                                      |   * weekly_driver_hisaab (Weekly settlement logs)|
                                                      +--------------------------------------------------+
```

---

## 3. Unified Repository Directory Structure

```
cashfree-web_portal/
├── app/                                 <-- FastAPI Python Backend Engine
│   ├── api/                             <-- 9 REST API Routers (Auth, Drivers, Fleet, Hisaabs, etc.)
│   ├── models/                          <-- SQLAlchemy Relational Models (10 DB Tables)
│   ├── schemas/                         <-- Pydantic Request & Response Validation DTOs
│   ├── services/                        <-- Business Logic (Hisaab Calculator, Aggregator Sync)
│   ├── db/                              <-- Schema DDL, Init DB, & Team Seeding Scripts
│   ├── config.py                        <-- Environment Settings & URL-Encoded DB Password
│   ├── database.py                      <-- SQLAlchemy Engine & Thread-Safe Connection Pool
│   └── main.py                          <-- FastAPI Application Entry Point & Static Asset Server
├── src/                                 <-- React 19 Frontend Source
│   ├── components/
│   │   └── Screens.tsx                  <-- Reusable screen views (Operator Fleet, Hisaab Statement, etc.)
│   ├── api.ts                           <-- Frontend universal REST client (maps BACKEND_URL)
│   ├── data.ts                          <-- Full database demo profiles, fleet data, settlement tables
│   ├── firebase.ts                      <-- Firebase SDK initialization with embedded project fallback
│   ├── types.ts                         <-- TypeScript interfaces (User, Vehicle, HisaabWeek, Fleet, etc.)
│   ├── index.css                        <-- TailwindCSS styling directives & custom animations
│   ├── App.tsx                          <-- Root application, OTP flows, active session, modal dialogs
│   └── main.tsx                         <-- React DOM entry point
├── Dockerfile                           <-- Multi-stage Docker build (Node 20 build -> Python 3.11 run)
├── requirements.txt                     <-- Python dependencies (fastapi, uvicorn, sqlalchemy, psycopg2)
├── package.json                         <-- Node.js dependencies (react 19, vite 6, lucide-react, firebase 11)
├── index.html                           <-- HTML shell containing persistent #recaptcha-container
└── vite.config.ts                       <-- Vite configuration
```

---

## 4. FastAPI Backend Layered Architecture & Modular Structure

```
app/
├── api/                                 <-- 1. PRESENTATION / ROUTER LAYER
│   ├── auth.py                          - POST /api/auth/otp/verify (Validates OTP / 1234, generates JWT)
│   │                                    - POST /api/auth/otp/request (Logs session attempt & audit)
│   ├── drivers.py                       - GET  /api/drivers/phone/{phone} (Driver profile & vehicle stats)
│   │                                    - GET  /api/drivers/{id}/profile (Detailed driver record)
│   ├── operators.py                     - GET  /api/operators/phone/{phone} (Fleet operator account)
│   │                                    - GET  /api/operators/{id}/fleet (Dynamic 4-vehicle fleet overview)
│   ├── hisaabs.py                       - GET  /api/drivers/{id}/hisaabs (Weekly financial settlement history)
│   │                                    - GET  /api/hisaabs/week/{week_num} (Specific week ledger breakdown)
│   ├── payments.py                      - POST /api/payments/settle (Cashfree UPI / IMPS payout trigger)
│   │                                    - POST /api/payments/webhook (Cashfree automated payment webhook)
│   ├── tickets.py                       - GET  /api/tickets (Support tickets list)
│   │                                    - POST /api/tickets (Create new support ticket)
│   ├── notifications.py                 - GET  /api/notifications (Driver & operator notification alerts)
│   │                                    - PUT  /api/notifications/{id}/read (Mark alert as read)
│   ├── referrals.py                     - GET  /api/referrals (Referral leads & bonus reward tracking)
│   └── audit.py                         - GET  /api/audit/logs (Security audit trails)
│
├── models/                              <-- 2. DATA PERSISTENCE / ORM LAYER (SQLAlchemy)
│   └── app_models.py                    - AppDrivers (id, full_name, phone, vehicle_reg_number, deposit)
│                                        - AppOperators (id, company_name, phone, fleet_size, deposit)
│                                        - AppOperatorVehicles (id, operator_id, driver_id, vehicle_make)
│                                        - AppHisaabs (id, driver_id, week_number, uber/ola/rapido revenue)
│                                        - AppSupportTickets, AppNotifications, AppReferralLeads
│                                        - AppPayments, AppSessions, AppAuditLogs
│
├── schemas/                             <-- 3. VALIDATION / DTO LAYER (Pydantic)
│   └── app_schemas.py                   - OTPRequest, OTPVerify, TokenResponse, DriverProfileResponse
│                                        - OperatorFleetResponse, HisaabBreakdownResponse, TicketCreateDTO
│
├── services/                            <-- 4. BUSINESS LOGIC & ENGINE LAYER
│   ├── hisaab_calculator.py             - Multi-aggregator revenue calculation & rent deduction math
│   ├── platform_aggregator.py           - Normalizes Uber, Ola, and Rapido driver statements
│   └── run_aggregation.py              - Scheduled batch reconciliation worker
│
├── db/                                  <-- 5. DATABASE AUTOMATION LAYER
│   ├── init_db.py                       - Base.metadata.create_all(bind=engine) table creation
│   ├── schema.sql                       - Complete raw PostgreSQL DDL with indexes and constraints
│   └── seed_data.py                     - Team database seeder (Anurag, Vivek, Sushant, Aayush)
│
├── config.py                            <-- Settings & Config: DB_HOST (35.200.196.113), quote_plus(DB_PASS)
├── database.py                          <-- SQLAlchemy Engine (pool_size=10, max_overflow=20) + psycopg2
└── main.py                              <-- FastAPI Application: CORS middleware, routers & static dist/ mount
```

---

## 5. PostgreSQL Cloud SQL Schema — All 10 Core Tables

| Table Name | Primary Key / Index | Description & Column Specifications |
| :--- | :--- | :--- |
| **`app_drivers`** | `app_driver_id` (PK), `phone` (UQ) | Complete driver master: full_name, phone, driver_code, aadhar_number, dl_number, vehicle_reg_number, vehicle_daily_rate, deposit_total_req, deposit_paid, deposit_pending, cumulative_owed, cw_os, assigned_manager_name, assigned_manager_phone. |
| **`app_operators`** | `app_operator_id` (PK), `phone` (UQ) | Fleet operator master: company_name ('Anurag & RK Fleet Logistics'), operator_code ('OPR-HYD-001'), phone ('9691938866'), fleet_size (4), total_vehicles (4), deposit_paid, deposit_pending, cw_to_collect (+₹17,656.40). |
| **`app_operator_vehicles`** | `id` (PK), `vehicle_number` (UQ) | Fleet vehicle allocation table: operator_id, driver_id, vehicle_number (KA05AQ7692, TS09EV8812, TS07EV4401, TG07V0580), vehicle_make, vehicle_model, daily_rate, status ('active'/'idle'), current_week_os. |
| **`weekly_driver_hisaab`** | `id` (PK), `(driver_id, week_number)` | Weekly financial ledger (app_hisaabs): gross aggregator revenue (Uber + Ola + Rapido), cash_collected, rent_deductions, challan_amt, accident_amt, tds_amt, net_settlement, to_pay, to_collect, status ('settled_pay'/'to_collect'). |
| **`app_support_tickets`** | `id` (PK), `ticket_code` (UQ) | Helpdesk ticketing system: ticket_code ('TKT-2026-001'), user_id, user_type ('driver'/'operator'), category ('Hisaab'/'Vehicle'/'Fastag'), priority ('high'/'medium'/'low'), subject, description, status ('open'/'in_progress'/'resolved'). |
| **`app_notifications`** | `id` (PK) | In-app alerts feed: user_id, user_type, title, message, type ('payout'/'alert'/'system'), is_read (boolean), created_at. |
| **`app_referral_leads`** | `id` (PK), `referral_code` | Driver & Operator referral program: referrer_id, referrer_type, invited_phone, invited_name, status ('signed_up'/'active_driving'), bonus_amount (₹1000), is_paid. |
| **`app_payments`** | `id` (PK), `transaction_id` (UQ) | Cashfree settlements and payment receipts: user_id, user_type, amount, payment_mode ('UPI_QR'/'IMPS'/'BANK_TRANSFER'), reference_id, status ('SUCCESS'/'PENDING'/'FAILED'), created_at. |
| **`app_sessions`** | `session_id` (PK) | Active user login sessions: user_type, user_ref_id, phone, otp_hash, is_verified, ip_address, user_agent, expires_at, created_at. |
| **`app_audit_logs`** | `id` (PK) | Security audit trails: user_type, user_ref_id, event_type ('OTP_REQUEST'/'OTP_VERIFY'/'SETTLEMENT_PROCESSED'), phone, ip_address, created_at. |

---

## 6. Master Team Accounts, Phone Numbers & Vehicles

| Name | Phone Number | Role | ID / Code | Assigned Vehicle & Financial Status |
| :--- | :--- | :--- | :--- | :--- |
| **Anurag** | `9691938866` | Operator | `OPR-HYD-001` | Anurag & RK Fleet Logistics (4 vehicles). Fleet Net Payout: +₹17,656.40 |
| **Vivek** | `9901484683` | Driver | `LR-DRV-VVK` | Maruti Dzire CNG (KA05AQ7692). Daily rent ₹1,000/day. W30 Payout: +₹7,995.80 |
| **Sushant** | `9140631755` | Driver | `LR-DRV-SSK` | Tata Tigor EV (TS09EV8812). Daily rent ₹1,200/day. W30 Balance Due: -₹1,850.00 |
| **Aayush** | `9930420065` | Driver | `LR-DRV-AYS` | Mahindra eVerito EV (TS07EV4401). Daily rent ₹1,100/day. W30 Payout: +₹6,180.00 |
| **Anurag Driver** | `9866941379` | Driver | `LR-HYD-0041` | Tour H3 CNG (TG07V0580). Daily rent ₹900/day. Net Hisaab: +₹3,480.00 |

### 6.1 Seamless Phone-Based Role Auto-Detection
The login screen automatically identifies whether a user is an Operator or a Driver based on their phone number. Entering `9691938866` immediately routes to the 4-car Fleet Ledger for *Anurag & RK Fleet Logistics*, while entering driver numbers routes directly to the individual driver hisaab statement without requiring any manual role toggle.

---

## 7. Firebase Phone Authentication & Real Telecom SMS Integration

### 7.1 Firebase Project Configuration Parameters
* **API Key:** `AIzaSyBHLTzWd6XHJTd2xp3kWOHszCvb4GWlWfU`
* **Auth Domain:** `letzryd-dev-test.firebaseapp.com`
* **Project ID:** `letzryd-dev-test` (Project Number: `925756819101`)
* **Storage Bucket:** `letzryd-dev-test.firebasestorage.app`
* **App ID:** `1:925756819101:web:83388ce68b39a49b587674`

### 7.2 Essential Firebase Console Settings
1. **Phone Provider Enabled:** Firebase Console -> Authentication -> Sign-in method -> Phone -> Enabled = ON.
2. **SMS Region Policy:** Firebase Console -> Authentication -> Settings -> Phone Auth -> SMS Region Policy -> 'Allow all regions' (or check 'India (+91)').
3. **Authorized Domains Whitelist:** In Firebase Console -> Authentication -> Settings -> Authorized Domains, ensure these 5 origins are listed:
   - `localhost`
   - `127.0.0.1`
   - `cashfree-web-portal.vercel.app`
   - `cashfree-web-portal-925756819101.asia-south1.run.app`
   - `letzryd-dev-test.firebaseapp.com`
4. **Test Number Suppression Rule (CRITICAL):** When a phone number is in 'Phone numbers for testing', Google suppresses physical cellular SMS. To receive real carrier SMS on a phone, delete that phone number from 'Phone numbers for testing' in Firebase Console!

---

## 8. Root Cause Analysis: Past Issues & Permanent Engineering Fixes

| Issue / Error Code | Root Cause Analysis | Permanent Technical Fix Implemented |
| :--- | :--- | :--- |
| `auth/operation-not-allowed` | Firebase restricted outbound SMS by geographic region by default. | Enabled 'India (+91)' in Firebase Console -> Authentication -> Settings -> SMS Region Policy. |
| `auth/invalid-app-credential` | Invisible reCAPTCHA DOM container unmounted when switching screens in React, aborting the verification token. | Added permanent `<div id='recaptcha-container'></div>` directly into `index.html` so it persists across all React state renders. |
| `SMS Not Received on Phone` | Phone numbers were added under 'Phone numbers for testing'. Firebase intercepts test numbers and disables carrier SMS. | Deleted personal numbers from the test list in Firebase Console. Google immediately began delivering real cellular SMS. |
| `SQLAlchemy Password Failure` | PostgreSQL password had special character `@`, breaking URL hostname parsing with error 'could not translate host name L^Xz)...'. | Updated `app/config.py` to URL-encode credentials using `urllib.parse.quote_plus(DB_PASS)` before forming `DATABASE_URL`. |
| `Cloud Run Missing Firebase Env` | Docker build on Cloud Run lacked `.env` file (as `.env` is in `.gitignore`), compiling empty strings for Firebase config. | Added embedded default project fallbacks inside `src/firebase.ts` so all production builds auto-initialize Firebase Auth. |
| `auth/too-many-requests` | Google anti-spam protection triggers after 3-5 rapid SMS requests to the same phone number in under 2 minutes. | Built Master OTP `1234` bypass in `app/api/auth.py` and `src/App.tsx`, allowing instant login without waiting for SMS cooldown. |

---

## 9. FastAPI Backend REST API Specifications

| Endpoint Path | Method | Request / Query Params | Response Structure |
| :--- | :--- | :--- | :--- |
| `/api/auth/otp/verify` | POST | `{"phone": "9691938866", "otp": "752483", "user_type": "operator"}` | `{"access_token": "JWT...", "token_type": "bearer", "user_type": "operator", "user_id": 1}` |
| `/api/drivers/phone/{phone}` | GET | `phone = 10-digit string (e.g. 9901484683)` | `{"app_driver_id": 1, "full_name": "Vivek", "phone": "9901484683", "vehicle_reg_number": "KA05AQ7692", "vehicle_daily_rate": 1000.0, "deposit_paid": 5000.0, "deposit_pending": 1000.0, "cw_os": -7995.80}` |
| `/api/operators/phone/{phone}` | GET | `phone = 10-digit string (e.g. 9691938866)` | `{"app_operator_id": 1, "company_name": "Anurag & RK Fleet Logistics", "operator_code": "OPR-HYD-001", "fleet_size": 4, "total_vehicles": 4, "deposit_paid": 20000.0, "cw_to_collect": 17656.40}` |
| `/api/operators/{id}/fleet` | GET | `id = integer (e.g. 1)` | `{"operator_id": 1, "company_name": "...", "vehicles": [{"vehicle_number": "KA05AQ7692", "driver_name": "Vivek", "daily_rate": 1000.0, "current_week_os": 7995.80, "status": "active"}, ...]}` |
| `/api/drivers/{id}/hisaabs` | GET | `id = integer (e.g. 1)` | `[{"week_number": 30, "period_start": "2026-07-20", "period_end": "2026-07-26", "uber_revenue": 14200.0, "ola_revenue": 4500.0, "rapido_revenue": 3100.0, "rent": 7000.0, "to_pay": 7995.80, "status": "settled_pay"}]` |
| `/api/tickets` | GET / POST | POST: `{"user_id": 1, "user_type": "driver", "category": "Hisaab", "subject": "Fare discrepancy", "description": "...", "priority": "high"}` | `{"ticket_code": "TKT-2026-001", "status": "open", "created_at": "..."}` |
| `/api/notifications` | GET | Query param: `user_id = 1` | `[{"id": 1, "title": "Hisaab Released", "message": "Week 30 hisaab is ready", "type": "payout", "is_read": false}]` |
| `/api/health` | GET | None | `{"status": "healthy", "app": "LetzRyd Partner App Backend", "database": "35.200.196.113"}` |

---

## 10. Hisaab Calculation & Settlement Logic

```
===================================================================================
WEEKLY HISAAB FORMULA
===================================================================================
Gross Revenue     = (Uber Earnings + Ola Earnings + Rapido Earnings + Platform Incentives)

Total Deductions  = Platform Cash Collected (trips where passenger paid cash)
                  + Vehicle Rent (Active Driving Days * Vehicle Daily Rent Rate)
                  + Tolls & Airport Parking Paid by Platform
                  + Traffic Challans (Traffic Police E-Challans)
                  + Accident Damage Recoveries
                  + 1% TDS (Income Tax Section 194M on Gross)
                  + Previous Week Unpaid Carried-Over Balance

Net Settlement    = Gross Revenue - Total Deductions

IF Net Settlement >= 0:
    STATUS = 'to_pay' (LetzRyd transfers funds to Driver via IMPS / Cashfree Payout)
IF Net Settlement < 0:
    STATUS = 'to_collect' (Driver transfers balance to LetzRyd via Cashfree UPI QR)
===================================================================================
```

---

## 11. Google Cloud Run Deployment Runbook

### 11.1 Multi-Stage Dockerfile (`cashfree-web_portal/Dockerfile`)
```dockerfile
FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=frontend-builder /app/dist ./dist

ENV PORT=8080
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
```

### 11.2 Deployment Command (Run in Google Cloud Shell)
```bash
cd ~/cashfree-web_portal
git pull origin main
gcloud run deploy cashfree-web-portal \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL="postgresql://postgres:8S5%5DU3%40L%5EXz%29%5CFH%7D@35.200.196.113:5432/postgres"
```

---

## 12. Vercel Frontend Deployment Runbook

### 12.1 Vercel Environment Variables
In Vercel Dashboard -> cashfree-web-portal -> Settings -> Environment Variables, add the following 7 variables:
```env
VITE_FIREBASE_API_KEY=AIzaSyBHLTzWd6XHJTd2xp3kWOHszCvb4GWlWfU
VITE_FIREBASE_AUTH_DOMAIN=letzryd-dev-test.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=letzryd-dev-test
VITE_FIREBASE_STORAGE_BUCKET=letzryd-dev-test.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=925756819101
VITE_FIREBASE_APP_ID=1:925756819101:web:83388ce68b39a49b587674
VITE_BACKEND_URL=https://cashfree-web-portal-925756819101.asia-south1.run.app
```

### 12.2 Triggering Redeploy
After saving environment variables in Vercel, navigate to Deployments -> click the '...' on the latest deployment -> select Redeploy.

---

## 13. Troubleshooting & Emergency Operations Runbook

| Symptom / Error | Root Cause | Actionable Fix |
| :--- | :--- | :--- |
| **SMS OTP not arriving** | Google rate limit (3+ SMS in 2 mins) or number in Firebase test list. | 1. Enter master code '1234' to login immediately.<br>2. Wait 15 mins for telecom cooldown.<br>3. Verify number is removed from Firebase test list. |
| **reCAPTCHA token error** | Browser AdBlocker or Brave Shields blocking `google.com/recaptcha`. | Disable AdBlocker on localhost/vercel or open in Chrome Incognito. |
| **CORS Error on Vercel API calls** | FastAPI missing Vercel origin in CORS middleware. | Verify `app/main.py` contains `allow_origins=['*']` and `allow_credentials=True`. |
| **PostgreSQL connection refused** | Database instance at `35.200.196.113` is paused or unauthorized IP. | Verify Cloud SQL instance is 'RUNNABLE' and Authorized Networks includes `0.0.0.0/0`. |
| **Cannot retrieve commit on GitHub** | Temporary GitHub UI cache refresh latency after rapid commits. | Hard refresh browser tab with `Ctrl + F5` or `Cmd + Shift + R`. |
