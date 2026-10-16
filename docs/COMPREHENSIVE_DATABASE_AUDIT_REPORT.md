# Comprehensive PostgreSQL Settlement & Mathematical Consistency Audit Report

**Audit Date**: October 6, 2026  
**Target Environment**: PostgreSQL Cloud Database (`35.200.196.113:5432/postgres`)  
**Scope**: All 309 Operators (`app_operators`), All 2,457 Drivers (`app_drivers`), 11,038 Hisaabs (`app_hisaabs`), Allocations (`app_driver_allocations`), and Payments (`app_payments`).

---

## Executive Summary

A comprehensive automated audit was conducted across the PostgreSQL database and the core API endpoints (`/api/hisaabs/operator/{id}` and `/api/operators/{id}/fleet-summary`). 

### Core Audit Metrics:
1. **Operator Audit**:
   - **Total Operators Evaluated**: 309 operators.
   - **Active Operators (with Fleet/Hisaabs)**: 199 operators.
   - **Mathematical Parity Rate**: 256 operators (82.8%) match.
   - **Operators Flagged with Discrepancies**: **53 operators** (17.2%) exhibit mathematical mismatches between `/api/hisaabs/operator/{id}` and `/api/operators/{id}/fleet-summary`.
2. **Driver Audit**:
   - **Total Drivers Evaluated**: 2,457 drivers across Bengaluru (1,638), Hyderabad (405), and Mumbai (211).
   - **Driver Snapshot Alignment**: For drivers with active Week 40 hisaabs, **95.9% (418 of 436)** have `cw_os`, `cw_to_collect`, and `cw_to_pay` perfectly matching `app_hisaabs`.
   - **Gross Earnings Breakdown**: 3,154 of 3,658 hisaabs in Weeks 39 & 40 confirm that `total_gross_earnings = Fare Revenue + Platform Incentives`.
3. **Critical Edge Cases Identified**:
   - **155 vehicle-weeks** have multiple drivers sharing a vehicle in the same settlement week.
   - **237 idle vehicles** were billed rent in Week 40 (totaling **₹12,13,675.00**), whereas **449 idle vehicles** had rent waived.
   - **Week 40 Exposure**: ₹57,48,801.38 is owed to LetzRyd (1,272 vehicles), while ₹2,78,408.57 is payable by LetzRyd to drivers/operators (139 vehicles).

---

## 1. Task 1: Audit Across All Operators

### 1.1 Specific Test on Named Operators

| Operator Identifier | Operator Name | Week | Direct DB `app_hisaabs` (Sum to_collect - to_pay) | `/api/hisaabs/operator/{id}` | `/api/operators/{id}/fleet-summary` | Match Status | Root Cause / Notes |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **9691938866** (Op ID 1) | Anurag & RK Fleet Logistics | W40 | ₹13,197.00 - ₹19,200.00 = **-₹6,003.00** | ₹13,197.00 / ₹19,200.00 | **₹0.00** (to_col: 0, to_pay: 0) | ❌ **MISMATCH** (Diff: ₹6,003.00) | Endpoint bug: hisaab prefix is `HIS-` instead of `HSB-`; hardcoded check fails in `fleet-summary`. |
| **9691938866** (Op ID 1) | Anurag & RK Fleet Logistics | W39 | ₹1,800.00 - ₹19,200.00 = **-₹17,400.00** | ₹1,800.00 / ₹19,200.00 | N/A (historical) | ✅ DB Valid | Same prefix bug prevents display in fleet summary. |
| **9036461336** (Op ID 501) | NISAMUDEEN K P | W40 | ₹1,17,002.77 - ₹0.00 = **₹1,17,002.77** | ₹1,17,002.77 / ₹0.00 | **₹1,17,002.77** (to_col: ₹1,17,002.77, to_pay: ₹0) | ✅ **PERFECT MATCH** | 22 hisaabs, 14 vehicles assigned under dummy operator driver 3490. |
| **9036461336** (Op ID 501) | NISAMUDEEN K P | W39 | ₹90,019.59 - ₹0.00 = **₹90,019.59** | ₹90,019.59 / ₹0.00 | N/A (historical) | ✅ DB Valid | Clean historical parity. |
| **9848012345** (Op ID 2) | Samvreeddhi Mobility Fleet | W40 | ₹0.00 - ₹0.00 = **₹0.00** | ₹0.00 / ₹0.00 | **₹0.00** | ✅ **MATCH** | Operator has 2 demo drivers, no W39/40 hisaabs generated. |

---

### 1.2 Breakdown of the 53 Mismatched Operators

Analysis of the 53 flagged operators revealed 4 distinct technical and operational root causes:

```
+----------------------------------------------------------------------------------------------------+
| Discrepancy Category                                     | Operator Count | Key Technical Cause     |
+----------------------------------------------------------------------------------------------------+
| 1. Vehicle Overwrite / Count Mismatch in Fleet Summary    | 34 operators   | Dictionary key collision|
| 2. Hardcoded Prefix Check Failure (`HIS-` vs `HSB-`)     | 2 operators    | Code checks parts[0]=='HSB'|
| 3. Historical Driver OS without Week 40 Hisaab            | 8 operators    | Driver has W39/W38 OS   |
| 4. Multi-Driver Vehicle Netting Mismatch                 | 9 operators    | Partial days / overlaps |
+----------------------------------------------------------------------------------------------------+
```

#### Detailed Explanation of Root Causes:
1. **The `parts[0] == 'HSB'` Prefix Filter Bug**:
   - Location: `app/api/operators.py` (lines 138-141).
   - Code:
     ```python
     parts = h.hisaab_number.split('-') if h.hisaab_number else []
     if len(parts) >= 3 and parts[0] == 'HSB':
         v_num = parts[2].upper()
         week_hisaabs_by_v[v_num] = h
     ```
   - Consequence: Operators whose hisaabs were generated with prefix `HIS-2026-040-...` (e.g. Op 1 `9691938866`, Op 45247) fail this condition. Their vehicles are marked idle with `current_week_os = 0.00`, causing a 100% discrepancy with `/api/hisaabs/operator/{id}`.

2. **The Vehicle Dictionary Key Collision Bug**:
   - When multiple drivers operated the same vehicle in Week 40 (155 occurrences in DB), `week_hisaabs_by_v[v_num] = h` overwrites earlier drivers' hisaabs with the last one processed.
   - Example (Op 504): Vehicle `KA05AQ3836` had 2 hisaabs (driver 3496: ₹930.90 to collect, driver 2210: ₹1,387.24 to collect). Fleet summary only counts ₹1,387.24, dropping ₹930.90. But SQL `SUM()` in `/api/hisaabs/operator/504` includes both, producing a ₹930.90 mismatch!

3. **Driver `operator_id` Mapping Inconsistency**:
   - Some operators have `app_operators.operator_id` (core id) differing from `app_operators.app_operator_id`.
   - In `app/api/operators.py` line 36:
     ```python
     drivers = db.query(AppDrivers).filter(AppDrivers.operator_id == op.app_operator_id)...
     ```
     This queries strictly on `op.app_operator_id`. If `app_drivers.operator_id` stores `core_operator_id`, zero drivers are returned.

---

### 1.3 Sample of Top Discrepancies (Week 40)

| Operator ID | Code | Phone | Operator Name | Sum(Veh OS) | Fleet to_col | Fleet to_pay | Hisaab to_col | Hisaab to_pay | Net Hisaab | Discrepancy | Vehs vs Hisaabs |
| :---: | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | `OPR-LETZ-SYS` | `0000000001` | LetzRyd Internal Fleet | ₹7,60,348.70 | ₹7,84,234.59 | ₹23,885.89 | ₹8,22,883.36 | ₹32,885.89 | ₹7,89,997.47 | **-₹29,648.77** | 604 vs 610 |
| **1** | `OPR-HYD-001` | `9691938866` | Anurag & RK Fleet Logistics | ₹0.00 | ₹0.00 | ₹0.00 | ₹13,197.00 | ₹19,200.00 | -₹6,003.00 | **+₹6,003.00** | 3 vs 4 |
| **742** | `LETZBLRIP9656907001` | `9656907001` | MOHAMMED NOUFAL K | ₹5,68,970.68 | ₹6,00,904.59 | ₹31,933.91 | ₹6,34,630.99 | ₹31,933.91 | ₹6,02,697.08 | **-₹33,726.41** | 222 vs 209 |
| **14712**| `LETZHYDIP8305908538` | `8305908538` | PRAMOD SAHU | ₹1,550.00 | ₹1,550.00 | ₹0.00 | ₹9,218.46 | ₹0.00 | ₹9,218.46 | **-₹7,668.46** | 2 vs 4 |
| **822** | `LETZBLRIP9847381899` | `9847381899` | SHARAFUDHEEN THOPPEKKATTU| ₹31,213.91 | ₹31,213.91 | ₹0.00 | ₹38,276.88 | ₹0.00 | ₹38,276.88 | **-₹7,062.97** | 8 vs 9 |
| **323** | `LETZBLRIP8157925885` | `8157925885` | GOKUL NATH R | ₹7,582.64 | ₹7,582.64 | ₹0.00 | ₹13,997.40 | ₹0.00 | ₹13,997.40 | **-₹6,414.76** | 2 vs 4 |
| **63** | `LETZBLRIP7012422318` | `7012422318` | JITHIN ROMIO | ₹4,113.00 | ₹4,113.00 | ₹0.00 | ₹10,375.00 | ₹0.00 | ₹10,375.00 | **-₹6,262.00** | 2 vs 2 |
| **462** | `LETZBLRIP8943018896` | `8943018896` | AJMAL V K | ₹9,150.00 | ₹9,150.00 | ₹0.00 | ₹15,190.65 | ₹0.00 | ₹15,190.65 | **-₹6,040.65** | 3 vs 5 |
| **651** | `LETZBLRIP9526100355` | `9526100355` | MUHAMMED SUHAIL | ₹56,220.00 | ₹56,220.00 | ₹0.00 | ₹62,177.39 | ₹0.00 | ₹62,177.39 | **-₹5,957.39** | 13 vs 13 |
| **497** | `LETZHYDIP9032600868` | `9032600868` | D ANIL KUMAR | ₹38,124.00 | ₹38,124.00 | ₹0.00 | ₹43,878.00 | ₹0.00 | ₹43,878.00 | **-₹5,754.00** | 10 vs 10 |

---

## 2. Task 2: Driver Level Audit

### 2.1 Driver Earnings Formula Verification
- **Audit Question**: Does driver gross earnings match `uber_revenue + ola_revenue + rapido_revenue`?
- **Finding**:
  - In `app_hisaabs`, **3,154 of 3,658 hisaabs** (86.2%) prove that:
    $$\text{Total Gross Earnings} = \text{Fare Revenues} + \text{Platform Incentives}$$
  - In Week 40, an ingestion discrepancy occurred: raw Uber incentives were added to `total_gross_earnings`, but `uber_incentive` was left as ₹0.00 on the hisaab row.
  - In `app_drivers`: 584 of 717 drivers with earnings match direct revenues, while 133 drivers reflect the addition of incentive bonuses or platform adjustments.

### 2.2 Driver Snapshot vs Latest Hisaab Parity
- For drivers whose latest hisaab is in Week 40:
  - **Total Drivers Audited**: 436 drivers.
  - **Perfect Match Rate**: **418 drivers (95.9%)** have `cw_os`, `cw_to_collect`, and `cw_to_pay` matching `app_hisaabs` to the exact paisa.
  - **Mismatches**: Only 18 drivers differed, caused by post-generation payments or test record injections.

### 2.3 Driver Rent vs Rental Plans
- **Audit Question**: Does driver rent match rental plans (`daily_rate * days`)?
- **Finding**:
  - In `app_drivers`, `vehicle_daily_rate` is populated with a flat default of ₹1,000.00.
  - In reality, rent in `app_hisaabs` and `daily_rent_log` is calculated dynamically based on:
    1. **Billable Days (`onroad_days`)**: Days when the vehicle was actively on road / checked in (e.g., 2, 4, or 5 days rather than 7 days).
    2. **Model Tier Rates**: Daily rates vary from ₹850.00 (Maruti WagonR) to ₹1,150.00 (Sedan/EV).
    3. **Indemnity / Maintenance Surcharge**: Some rental plans bundle daily maintenance charges (₹30–₹50/day).

---

## 3. Task 3: Edge Cases Analysis

### 3.1 Edge Case 1: Multiple Drivers Assigned to One Vehicle
- **Prevalence**: **155 vehicle-weeks** across Weeks 39 & 40 have multiple drivers assigned to the same vehicle.
- **Top Examples**:
  - `KA51AL1792` (Week 40): Driven by Drivers 17, 101, and 1223 across 3 hisaabs (`4112, 50322, 221703`), totaling ₹10,789.29 to collect.
  - `KA05AP7516` (Week 40): Driven by Drivers 917, 1719, and 2131 across 3 hisaabs (`4453, 221779, 9142`), totaling ₹7,845.31 to collect.
- **Impact**: In `app/api/operators.py`, vehicle registration numbers are used as dictionary keys, causing silent overwriting and underreporting of fleet debt.

### 3.2 Edge Case 2: Idle Vehicles — Rent Charged vs Waived
- **Week 40**:
  - Total Idle Vehicles (0 trips, ₹0 gross earnings): **686 vehicles**.
  - **Rent Charged**: **237 vehicles** were charged rent, totaling **₹12,13,675.00**!
  - **Rent Waived**: **449 vehicles** had ₹0 rent charged.
- **Week 39**:
  - Total Idle Vehicles: **647 vehicles**.
  - **Rent Charged**: **232 vehicles** were charged rent, totaling **₹12,63,866.00**!
  - **Rent Waived**: **415 vehicles** had ₹0 rent charged.
- **Discrepancy**: There is no explicit rule tag distinguishing why 35% of idle vehicles were billed full rent while 65% had rent completely waived.

### 3.3 Edge Case 3: Positive OS (Debt to LetzRyd) vs Negative OS (Payout Owed)
- **Week 40 Breakdown**:
  - **Positive OS (Debt owed to LetzRyd)**: 1,272 vehicles totaling **₹57,48,801.38** (Average debt: ₹4,519.50/vehicle).
  - **Negative OS (Payout owed by LetzRyd to Driver/Operator)**: 139 vehicles totaling **₹2,78,408.57** (Average payout: ₹2,002.94/vehicle).
  - **Zero OS**: 442 vehicles.
- **Week 39 Breakdown**:
  - **Positive OS**: 1,186 vehicles totaling **₹51,85,955.59**.
  - **Negative OS**: 206 vehicles totaling **₹4,83,023.53**.
  - **Zero OS**: 413 vehicles.

### 3.4 Edge Case 4: Payments and Collections Recorded
- **In `app_hisaabs`**:
  - 19 hisaabs marked `settled` (₹21,333.19 recorded paid).
  - 4 hisaabs marked `partial` (₹9,419.81 recorded paid).
  - 2 hisaabs marked `paid` (₹17,540.00 recorded paid).
  - 11,013 hisaabs have no payment record (`NULL` or `unpaid`).
- **In `app_payments`**:
  - 23 successful collections via Cashfree (₹12,706.00).
  - 45 initiated/abandoned transactions (₹9,26,431.46).
- **In `cashfree_payouts`**:
  - Only 1 disbursement recorded.

---

## 4. Task 4: Compilation of Discrepancies & Business Clarifications Needed

### 4.1 System & Technical Discrepancies to Fix
1. **Fix `parts[0] == 'HSB'` Filter in `app/api/operators.py`**:
   - The regex / split logic must support all hisaab prefixes (`HSB-`, `HIS-`, `HS-`).
2. **Handle Multi-Driver Vehicle Aggregation in `get_operator_fleet_summary`**:
   - Instead of overwriting `week_hisaabs_by_v[v_num] = h`, aggregate all hisaabs for a vehicle (or display them as shift entries), so `sum(vehicles current_week_os)` always equals SQL `to_collect - to_pay`.
3. **Harmonize `operator_id` (Core ID vs App ID) in Driver Queries**:
   - Ensure `AppDrivers.operator_id IN (op.app_operator_id, op.operator_id)` in `operators.py` line 36.

### 4.2 Key Business & Operational Clarifications Required

1. **Idle Vehicle Rent Policy**:
   - *Question for Fleet Operations*: Under what exact contractual conditions is rent charged on an idle vehicle? In Week 40, ₹12.13 Lakhs was billed to 237 idle vehicles, while 449 idle vehicles were billed ₹0. Is rent waiver based on formal leave, workshop maintenance status, or manager discretion?
2. **Fleet Netting Policy**:
   - *Question for Finance / Settlement*: When an operator has vehicles with positive OS (debt owed to LetzRyd) and other vehicles with negative OS (payout owed by LetzRyd), is settlement strictly netted at the operator level (one net transfer), or are payouts and collections handled on separate rails?
3. **Multi-Driver Shift Allocation**:
   - *Question for Operations*: When two drivers operate the same vehicle in one week, who is primarily liable for the vehicle rent? Is the daily rent split proportionately by active days driven, or charged individually per driver?
4. **Platform Incentive Allocation**:
   - *Question for Product / Accounting*: When an operator fleet driver earns a platform incentive on Uber/Ola, does that incentive belong 100% to the driver to offset deductions, or does the operator retain a percentage cut?
