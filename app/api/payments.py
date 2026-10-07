import os
import hmac
import hashlib
import base64
import json
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import Optional
import uuid

from app.database import get_db
from app.models.app_models import AppPayments, AppDrivers, AppHisaabs, AppOperators, AppNotifications
from app.schemas.app_schemas import InitiatePaymentRequest, PaymentResponse, CreateOrderRequest, CreateOrderResponse
from app.services.helpers import clean_phone_number, resolve_driver, resolve_operator

import requests
from app.config import settings

router = APIRouter(prefix="/payments", tags=["Payments & Cashfree"])


def get_active_week_number(db: Session) -> int:
    """Dynamically look up current active unlocked settlement week."""
    active_h = db.query(AppHisaabs.week_number).filter(
        AppHisaabs.is_locked == False
    ).order_by(AppHisaabs.week_number.desc()).first()
    if active_h:
        return active_h[0]
    max_w = db.query(func.max(AppHisaabs.week_number)).scalar()
    return max_w or 41


def verify_cashfree_signature(timestamp: str, raw_body: bytes, signature: str, secret_key: str) -> bool:
    """Verify Cashfree HMAC-SHA256 signature."""
    if not signature or not secret_key:
        return False
    body_str = raw_body.decode('utf-8') if isinstance(raw_body, bytes) else str(raw_body)
    data = (timestamp + body_str) if timestamp else body_str
    expected_b64 = base64.b64encode(
        hmac.new(secret_key.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).digest()
    ).decode('utf-8')
    if hmac.compare_digest(signature, expected_b64):
        return True
    expected_hex = hmac.new(secret_key.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_hex)


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPER — called after Cashfree confirms payment SUCCESS
# Updates: app_hisaabs, app_drivers/app_operators, app_notifications
# ─────────────────────────────────────────────────────────────────────────────
def _apply_payment_success(payment: AppPayments, db: Session) -> dict:
    """
    After a real Cashfree payment is confirmed SUCCESS, cascade the update to:
      1. app_hisaabs  → paid_amount, current_period_os, to_collect, payment_status, status
      2. app_drivers  → lw_status, cw_to_collect, cw_os, deposit_paid, deposit_pending (driver payers)
      3. app_operators → cw_to_collect, cw_to_pay, deposit_paid, deposit_pending, lw_status (operator payers)
      4. app_notifications → fire a payment receipt notification

    Returns a summary dict of what was updated.
    """
    updated = {"hisaab": None, "driver": None, "operator": None, "notification": None}
    paid_amount = round(float(payment.amount or 0), 2)

    # ── 1. Update app_hisaabs ────────────────────────────────────────────────
    hisaab = None
    if payment.app_hisaab_id:
        hisaab = db.query(AppHisaabs).filter(AppHisaabs.app_hisaab_id == payment.app_hisaab_id).first()
    elif payment.payer_type == "driver" and payment.payer_id:
        # Fallback: look up the driver's most recent uncollected hisaab
        hisaab = db.query(AppHisaabs).filter(
            AppHisaabs.app_driver_id == payment.payer_id,
            AppHisaabs.to_collect > 0,
            AppHisaabs.payment_status != "settled"
        ).order_by(AppHisaabs.week_number.desc()).first()
        if hisaab:
            payment.app_hisaab_id = hisaab.app_hisaab_id

    # ── 2. Update app_drivers & hisaabs (if payer is driver) ──────────────────
    if payment.payer_type == "driver" and payment.payer_id:
        driver = db.query(AppDrivers).filter(
            (AppDrivers.app_driver_id == payment.payer_id) | (AppDrivers.driver_id == payment.payer_id)
        ).first()
        if not driver:
            driver = resolve_driver(str(payment.payer_id), db)
        if driver:
            rem_cash = paid_amount

            active_week_num = get_active_week_number(db)

            # Tier 1: Pay target hisaab (or active week debt)
            target_hisaab = hisaab
            if not target_hisaab:
                target_hisaab = db.query(AppHisaabs).filter(
                    AppHisaabs.app_driver_id == driver.app_driver_id,
                    AppHisaabs.to_collect > 0,
                    AppHisaabs.payment_status != "settled"
                ).order_by(AppHisaabs.week_number.desc()).first()
                if not target_hisaab:
                    target_hisaab = db.query(AppHisaabs).filter(
                        AppHisaabs.app_driver_id == driver.app_driver_id,
                        AppHisaabs.week_number == active_week_num
                    ).first()

            if target_hisaab:
                t_prev_paid = round(float(target_hisaab.paid_amount or 0), 2)
                t_orig = round(float(target_hisaab.to_collect or 0) + t_prev_paid, 2)
                t_rem_due = round(max(0.0, t_orig - t_prev_paid), 2)
                t_pay = round(min(t_rem_due, rem_cash), 2)

                if t_pay > 0:
                    target_hisaab.paid_amount = round(t_prev_paid + t_pay, 2)
                    new_rem = round(max(0.0, t_orig - target_hisaab.paid_amount), 2)
                    target_hisaab.current_period_os = new_rem
                    target_hisaab.to_collect = new_rem

                    if target_hisaab.paid_amount >= t_orig and t_orig > 0:
                        target_hisaab.payment_status = "settled"
                        target_hisaab.status = "settled"
                        target_hisaab.current_period_os = 0.0
                        target_hisaab.to_collect = 0.0
                    elif target_hisaab.paid_amount > 0:
                        target_hisaab.payment_status = "partial"

                    # Deduct from driver's cw_to_collect or lw_os
                    if target_hisaab.week_number >= active_week_num or not target_hisaab.is_locked:
                        driver.cw_to_collect = round(max(0.0, float(driver.cw_to_collect or 0) - t_pay), 2)
                        driver.cw_os = round(max(0.0, float(driver.cw_os or 0) - t_pay), 2)
                        driver.cumulative_owed = round(max(0.0, float(driver.cumulative_owed or 0) - t_pay), 2)
                    else:
                        driver.lw_os = round(max(0.0, float(driver.lw_os or 0) - t_pay), 2)
                        driver.cumulative_owed = round(max(0.0, float(driver.cumulative_owed or 0) - t_pay), 2)
                        if driver.lw_os <= 0:
                            driver.lw_status = "paid"
                        else:
                            driver.lw_status = "partial"

                    rem_cash = round(max(0.0, rem_cash - t_pay), 2)
                updated["hisaab"] = {
                    "app_hisaab_id": target_hisaab.app_hisaab_id,
                    "paid_amount": target_hisaab.paid_amount,
                    "current_period_os": target_hisaab.current_period_os,
                    "to_collect": target_hisaab.to_collect,
                    "payment_status": target_hisaab.payment_status,
                }

            # Tier 2: Pay any other unpaid/prior hisaabs for this driver BEFORE deposit
            if rem_cash > 0:
                other_unpaid_hisaabs = db.query(AppHisaabs).filter(
                    AppHisaabs.app_driver_id == driver.app_driver_id,
                    AppHisaabs.to_collect > 0,
                    AppHisaabs.payment_status != "settled"
                ).order_by(AppHisaabs.week_number.asc()).all()

                for oh in other_unpaid_hisaabs:
                    if rem_cash <= 0:
                        break
                    if target_hisaab and oh.app_hisaab_id == target_hisaab.app_hisaab_id:
                        continue
                    oh_prev_paid = round(float(oh.paid_amount or 0), 2)
                    oh_orig = round(float(oh.to_collect or 0) + oh_prev_paid, 2)
                    oh_rem_due = round(max(0.0, oh_orig - oh_prev_paid), 2)
                    oh_pay = round(min(oh_rem_due, rem_cash), 2)

                    oh.paid_amount = round(oh_prev_paid + oh_pay, 2)
                    oh_new_rem = round(max(0.0, oh_orig - oh.paid_amount), 2)
                    oh.current_period_os = oh_new_rem
                    oh.to_collect = oh_new_rem

                    if oh.paid_amount >= oh_orig and oh_orig > 0:
                        oh.payment_status = "settled"
                        oh.status = "settled"
                        oh.current_period_os = 0.0
                        oh.to_collect = 0.0
                    elif oh.paid_amount > 0:
                        oh.payment_status = "partial"

                    # Update driver lw_os or cw_os
                    driver.cumulative_owed = round(max(0.0, float(driver.cumulative_owed or 0) - oh_pay), 2)
                    if oh.week_number < active_week_num or oh.is_locked:
                        driver.lw_os = round(max(0.0, float(driver.lw_os or 0) - oh_pay), 2)
                        if driver.lw_os <= 0:
                            driver.lw_status = "paid"
                        else:
                            driver.lw_status = "partial"
                    else:
                        driver.cw_to_collect = round(max(0.0, float(driver.cw_to_collect or 0) - oh_pay), 2)
                        driver.cw_os = round(max(0.0, float(driver.cw_os or 0) - oh_pay), 2)

                    rem_cash = round(max(0.0, rem_cash - oh_pay), 2)

            # Tier 3: Pay pending security deposit
            if rem_cash > 0:
                dep_pending = round(float(driver.deposit_pending or 0), 2)
                total_req = round(float(driver.deposit_total_req or 6000.0), 2)
                dep_credit = round(min(dep_pending, rem_cash), 2)
                driver.deposit_paid = round(min(total_req, float(driver.deposit_paid or 0) + dep_credit), 2)
                driver.deposit_pending = round(max(0.0, total_req - float(driver.deposit_paid)), 2)
                rem_cash = round(max(0.0, rem_cash - dep_credit), 2)

            # Tier 4: Any remaining surplus becomes driver advance credit
            if rem_cash > 0:
                driver.cw_to_collect = 0.0
                driver.cw_os = round(-rem_cash, 2)
                driver.cw_to_pay = round(rem_cash, 2)
                # Also reflect in active week hisaab as payout credit
                cw_h = db.query(AppHisaabs).filter(
                    AppHisaabs.app_driver_id == driver.app_driver_id,
                    AppHisaabs.week_number == active_week_num
                ).first()
                if cw_h:
                    cw_h.current_period_os = round(-rem_cash, 2)
                    cw_h.to_pay = round(rem_cash, 2)
                    cw_h.to_collect = 0.0

            updated["driver"] = {
                "app_driver_id": driver.app_driver_id,
                "full_name": driver.full_name,
                "lw_status": driver.lw_status,
                "lw_os": driver.lw_os,
                "cw_to_collect": driver.cw_to_collect,
                "cw_os": driver.cw_os,
                "deposit_paid": driver.deposit_paid,
                "deposit_pending": driver.deposit_pending,
            }

    # ── 3. Update app_operators & fleet drivers (if payer is operator) ───────
    if payment.payer_type == "operator" and payment.payer_id:
        op = db.query(AppOperators).filter(
            (AppOperators.app_operator_id == payment.payer_id) | (AppOperators.operator_id == payment.payer_id)
        ).first()
        if not op:
            op = resolve_operator(str(payment.payer_id), db)
        if op:
            # Tier 1: Pay down operator fleet driver debts (e.g. Sushant who owes ₹1,850)
            op_filter = (AppDrivers.operator_id == op.app_operator_id)
            if op.operator_id:
                op_filter = op_filter | (AppDrivers.operator_id == op.operator_id)

            fleet_drivers_with_debt = db.query(AppDrivers).filter(
                op_filter,
                AppDrivers.cw_to_collect > 0
            ).order_by(AppDrivers.app_driver_id).all()

            rem_for_debt = paid_amount
            for d in fleet_drivers_with_debt:
                if rem_for_debt <= 0:
                    break
                d_due = round(float(d.cw_to_collect or 0), 2)
                d_paid = round(min(d_due, rem_for_debt), 2)
                d.cw_to_collect = round(max(0.0, d_due - d_paid), 2)
                d.cw_os = round(max(0.0, float(d.cw_os or 0) - d_paid), 2)
                if d.cw_to_collect <= 0:
                    d.lw_status = "paid"
                else:
                    d.lw_status = "partial"

                # Also update that driver's weekly hisaab record(s)
                d_hisaabs = db.query(AppHisaabs).filter(
                    AppHisaabs.app_driver_id == d.app_driver_id
                ).order_by(AppHisaabs.week_number.asc()).all()
                rem_h_paid = d_paid
                for dh in d_hisaabs:
                    if rem_h_paid <= 0:
                        break
                    cur_paid = round(float(dh.paid_amount or 0), 2)
                    dh_orig = round(float(dh.to_collect or 0) + cur_paid, 2)
                    dh_rem = round(max(0.0, dh_orig - cur_paid), 2)
                    if dh_rem > 0 and dh.payment_status != "settled":
                        h_pay = round(min(dh_rem, rem_h_paid), 2)
                        dh.paid_amount = round(cur_paid + h_pay, 2)
                        dh_new_rem = round(max(0.0, dh_orig - dh.paid_amount), 2)
                        dh.current_period_os = dh_new_rem
                        dh.to_collect = dh_new_rem
                        if dh.paid_amount >= dh_orig and dh_orig > 0:
                            dh.payment_status = "settled"
                            dh.status = "settled"
                            dh.current_period_os = 0.0
                            dh.to_collect = 0.0
                        elif dh.paid_amount > 0:
                            dh.payment_status = "partial"
                        rem_h_paid = round(max(0.0, rem_h_paid - h_pay), 2)

                rem_for_debt = round(max(0.0, rem_for_debt - d_paid), 2)

            # If rem_for_debt > 0, also settle any operator vehicle hisaabs not covered by driver records
            if rem_for_debt > 0:
                op_ids = [op.app_operator_id]
                if op.operator_id:
                    op_ids.append(op.operator_id)
                op_unpaid_hisaabs = db.query(AppHisaabs).filter(
                    AppHisaabs.app_operator_id.in_(op_ids),
                    AppHisaabs.to_collect > 0,
                    AppHisaabs.payment_status != "settled"
                ).order_by(AppHisaabs.week_number.asc()).all()
                for oh in op_unpaid_hisaabs:
                    if rem_for_debt <= 0:
                        break
                    cur_paid = round(float(oh.paid_amount or 0), 2)
                    oh_orig = round(float(oh.to_collect or 0) + cur_paid, 2)
                    oh_rem = round(max(0.0, oh_orig - cur_paid), 2)
                    if oh_rem > 0:
                        h_pay = round(min(oh_rem, rem_for_debt), 2)
                        oh.paid_amount = round(cur_paid + h_pay, 2)
                        oh_new_rem = round(max(0.0, oh_orig - oh.paid_amount), 2)
                        oh.current_period_os = oh_new_rem
                        oh.to_collect = oh_new_rem
                        if oh.paid_amount >= oh_orig and oh_orig > 0:
                            oh.payment_status = "settled"
                            oh.status = "settled"
                            oh.current_period_os = 0.0
                            oh.to_collect = 0.0
                        elif oh.paid_amount > 0:
                            oh.payment_status = "partial"
                        rem_for_debt = round(max(0.0, rem_for_debt - h_pay), 2)

            # Operator total fleet debt remaining
            all_op_drivers = db.query(AppDrivers).filter(op_filter).all()
            driver_debt = sum(float(d.cw_to_collect or 0) for d in all_op_drivers)
            op_ids = [op.app_operator_id]
            if op.operator_id:
                op_ids.append(op.operator_id)
            active_wk = get_active_week_number(db)
            latest_op_h = db.query(AppHisaabs).filter(
                AppHisaabs.app_operator_id.in_(op_ids),
                AppHisaabs.week_number == active_wk
            ).all()
            hisaab_debt = sum(float(h.to_collect or 0) for h in latest_op_h)
            op.cw_to_collect = round(max(driver_debt, hisaab_debt), 2)
            if op.cw_to_collect <= 0:
                op.lw_status = "paid"
            else:
                op.lw_status = "partial"

            excess_after_debt = round(max(0.0, rem_for_debt), 2)

            # Tier 2: Pay down operator pending security deposit
            dep_pending = round(float(op.deposit_pending or 0), 2)
            dep_payment = round(min(dep_pending, excess_after_debt), 2)
            total_dep_req = round(float(op.deposit_total_req or 25000.0), 2)
            op.deposit_paid = round(min(total_dep_req, float(op.deposit_paid or 0) + dep_payment), 2)
            op.deposit_pending = round(max(0.0, total_dep_req - float(op.deposit_paid)), 2)

            # Tier 3: Any leftover surplus beyond debt & deposit increases operator payout credit
            excess_after_deposit = round(max(0.0, excess_after_debt - dep_payment), 2)
            if excess_after_deposit > 0:
                op.cw_to_pay = round(float(op.cw_to_pay or 0) + excess_after_deposit, 2)

            updated["operator"] = {
                "app_operator_id": op.app_operator_id,
                "company_name": op.company_name,
                "lw_status": op.lw_status,
                "cw_to_collect": op.cw_to_collect,
                "cw_to_pay": op.cw_to_pay,
                "deposit_paid": op.deposit_paid,
                "deposit_pending": op.deposit_pending,
            }

    # ── 4. Fire payment notification ──────────────────────────────────────────
    if payment.payer_id and payment.payer_type in ("driver", "operator"):
        hisaab_ref = hisaab.hisaab_number if hisaab else "your account"
        notif = AppNotifications(
            target_type=payment.payer_type,
            target_id=payment.payer_id,
            notif_type="payment",
            severity="success",
            icon="Wallet",
            title="Payment Received ✅",
            message=f"Your payment of ₹{paid_amount:,.0f} for {hisaab_ref} has been received. "
                    f"Your balance is now updated.",
            deep_link="/settle",
            is_read=False,
        )
        db.add(notif)
        updated["notification"] = f"Payment receipt notification sent to {payment.payer_type} {payment.payer_id}"

    db.commit()
    return updated


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT: Initiate a simple payment record (no Cashfree order yet)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/initiate", response_model=PaymentResponse)
def initiate_payment(req: InitiatePaymentRequest, db: Session = Depends(get_db)):
    amt = round(float(req.amount or 0), 2)
    if amt <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount must be greater than zero"
        )

    # If payer is a driver, verify they are not under an operator
    if req.payer_type == "driver" and req.payer_id:
        driver = db.query(AppDrivers).filter(AppDrivers.app_driver_id == req.payer_id).first()
        if driver and driver.operator_id and driver.operator_id > 0:
            op = db.query(AppOperators).filter(
                (AppOperators.app_operator_id == driver.operator_id) | (AppOperators.operator_id == driver.operator_id)
            ).first()
            if op:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Driver is managed by fleet operator '{op.company_name or op.contact_person_name}'. Individual payments are disabled; payments must be made by the fleet operator."
                )

    if req.app_hisaab_id:
        h = db.query(AppHisaabs).filter(AppHisaabs.app_hisaab_id == req.app_hisaab_id).first()
        if not h:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hisaab ID {req.app_hisaab_id} not found")

    cf_order_id = f"ORDER_LR_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)

    payment = AppPayments(
        payment_type="collection",
        payer_type=req.payer_type,
        payer_id=req.payer_id,
        payee_type="letzryd",
        app_hisaab_id=req.app_hisaab_id,
        amount=amt,
        payment_mode=req.payment_mode,
        status="INITIATED",
        cf_order_id=cf_order_id,
        initiated_at=now
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return PaymentResponse(
        app_payment_id=payment.app_payment_id,
        amount=float(payment.amount),
        payment_mode=payment.payment_mode,
        status=payment.status,
        cf_order_id=payment.cf_order_id
    )


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT: Create a real Cashfree PG order → returns payment_session_id
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/create-order", response_model=CreateOrderResponse)
def create_cashfree_order(req: CreateOrderRequest, db: Session = Depends(get_db)):
    """Creates a real Cashfree PG order and returns live session ID with fallback."""
    try:
        amt = round(float(req.amount), 2)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount must be a valid number"
        )

    if amt <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount must be greater than zero"
        )

    order_id = f"ORDER_LR_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)

    # Determine payer_type (operator vs driver)
    payer_type = req.payer_type or "driver"
    payer_id = int(req.driverId) if (req.driverId and str(req.driverId).isdigit()) else 1
    if req.operator_id:
        payer_type = "operator"
        payer_id = req.operator_id

    # Resolve driver ID if possible (fail-safe)
    db_accessible = True
    clean_phone = clean_phone_number(req.driverPhone or "")
    if clean_phone and not req.operator_id:
        try:
            driver = resolve_driver(clean_phone, db)
            if driver:
                payer_id = driver.app_driver_id
        except Exception as e:
            db_accessible = False
            print(f"[WARN] DB driver resolution skipped (database unreachable): {e}")

    # Check if driver is managed by a fleet operator
    if payer_type == "driver" and db_accessible:
        driver = db.query(AppDrivers).filter(AppDrivers.app_driver_id == payer_id).first()
        if not driver and clean_phone:
            driver = resolve_driver(clean_phone, db)
        if driver and driver.operator_id and driver.operator_id > 0:
            op = db.query(AppOperators).filter(
                (AppOperators.app_operator_id == driver.operator_id) | (AppOperators.operator_id == driver.operator_id)
            ).first()
            if op:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Driver is managed by fleet operator '{op.company_name or op.contact_person_name}'. Individual payments are disabled; payments must be made by the fleet operator."
                )

    # Call Real Cashfree PG Orders API
    cf_headers = {
        "x-client-id": settings.CASHFREE_APP_ID,
        "x-client-secret": settings.CASHFREE_SECRET_KEY,
        "x-api-version": settings.CASHFREE_API_VERSION,
        "Content-Type": "application/json"
    }

    # Configure proper return_url to redirect back to LetzRyd Driver Portal upon payment completion
    return_url = req.return_url
    if not return_url:
        default_frontend = os.getenv("FRONTEND_URL", "http://localhost:3002")
        return_url = f"{default_frontend.rstrip('/')}/?order_id={{order_id}}"
    elif "{order_id}" not in return_url:
        return_url = f"{return_url.rstrip('/')}/?order_id={{order_id}}"

    cf_payload = {
        "order_id": order_id,
        "order_amount": max(1.0, amt),
        "order_currency": "INR",
        "customer_details": {
            "customer_id": f"CUST_{payer_id}_{uuid.uuid4().hex[:6]}",
            "customer_phone": clean_phone or "9999999999",
            "customer_name": req.driverName or "LetzRyd Partner"
        },
        "order_meta": {
            "return_url": return_url
        }
    }

    session_id = None
    cf_ord_id = order_id

    # If Cashfree credentials configured, attempt real Cashfree API call
    is_live_config = bool(
        settings.CASHFREE_APP_ID and 
        settings.CASHFREE_SECRET_KEY and 
        not settings.CASHFREE_APP_ID.startswith("YOUR_") and
        not settings.CASHFREE_APP_ID.startswith("CF_APP_LETZRYD_TEST")
    )

    if is_live_config:
        try:
            cf_res = requests.post(f"{settings.CASHFREE_BASE_URL}/orders", json=cf_payload, headers=cf_headers, timeout=10)
            cf_data = cf_res.json()
            if cf_res.status_code == 200 and cf_data.get("payment_session_id"):
                session_id = cf_data["payment_session_id"]
                cf_ord_id = cf_data.get("order_id", order_id)
            else:
                err_msg = cf_data.get("message") or cf_data.get("error") or str(cf_data)
                print(f"[WARN] Cashfree Payment Gateway order error ({cf_res.status_code}): {err_msg}. Using fallback session.")
                session_id = f"session_lr_{uuid.uuid4().hex}"
        except Exception as e:
            print(f"[WARN] Cashfree connection error: {e}. Using fallback session.")
            session_id = f"session_lr_{uuid.uuid4().hex}"
    else:
        # Development / Test fallback session
        session_id = f"session_lr_{uuid.uuid4().hex}"

    # Auto-resolve hisaab_id if not explicitly provided and save record
    hisaab_id_to_use = req.app_hisaab_id
    if db_accessible:
        try:
            if not hisaab_id_to_use and payer_type == "driver" and payer_id:
                active_week_num = get_active_week_number(db)
                h_unpaid = db.query(AppHisaabs).filter(
                    AppHisaabs.app_driver_id == payer_id,
                    AppHisaabs.to_collect > 0,
                    AppHisaabs.payment_status != "settled"
                ).order_by(AppHisaabs.week_number.desc()).first()
                if h_unpaid:
                    hisaab_id_to_use = h_unpaid.app_hisaab_id
                else:
                    h_active = db.query(AppHisaabs).filter(
                        AppHisaabs.app_driver_id == payer_id,
                        AppHisaabs.week_number == active_week_num
                    ).first()
                    if h_active:
                        hisaab_id_to_use = h_active.app_hisaab_id

            # Store payment record with hisaab linkage
            payment = AppPayments(
                payment_type="collection",
                payer_type=payer_type,
                payer_id=payer_id,
                payee_type="letzryd",
                app_hisaab_id=hisaab_id_to_use,
                amount=amt,
                payment_mode="cashfree_checkout",
                status="INITIATED",
                cf_order_id=cf_ord_id,
                raw_response={
                    "weekRange": req.weekRange,
                    "driverName": req.driverName,
                    "driverPhone": req.driverPhone,
                    "app_hisaab_id": hisaab_id_to_use,
                    "payer_type": payer_type,
                },
                initiated_at=now
            )
            db.add(payment)
            db.commit()
        except Exception as e:
            try:
                db.rollback()
            except Exception:
                pass
            print(f"[WARN] Failed to persist payment record in DB: {e}")

    return CreateOrderResponse(
        payment_session_id=session_id or f"session_lr_{uuid.uuid4().hex}",
        order_id=cf_ord_id,
        order_amount=amt,
        order_currency="INR",
        order_status="ACTIVE"
    )


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT: Direct Cashfree session payment (Seamless API)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/pay-session")
def pay_cashfree_session(request_data: dict):
    """Executes Seamless / Direct Cashfree payment session and returns direct gateway URL."""
    session_id = request_data.get("payment_session_id")
    payment_method = request_data.get("payment_method")

    cf_headers = {
        "x-client-id": settings.CASHFREE_APP_ID,
        "x-client-secret": settings.CASHFREE_SECRET_KEY,
        "x-api-version": settings.CASHFREE_API_VERSION,
        "Content-Type": "application/json"
    }

    payload = {
        "payment_session_id": session_id,
        "payment_method": payment_method
    }

    try:
        cf_res = requests.post(f"{settings.CASHFREE_BASE_URL}/orders/sessions", json=payload, headers=cf_headers, timeout=15)
        return cf_res.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT: Verify a Cashfree order — THE CRITICAL CASCADE UPDATE POINT
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/verify/{order_id}")
def verify_cashfree_order(order_id: str, db: Session = Depends(get_db)):
    """
    Queries Cashfree API to verify payment status.
    On SUCCESS → updates app_payments + app_hisaabs + app_drivers/operators + fires notification.
    """
    payment = db.query(AppPayments).filter(AppPayments.cf_order_id == order_id).first()

    is_success = False
    payment_mode = "Cashfree Gateway"
    cf_payment_id = None
    payments_data = []
    paid_amount = float(payment.amount) if (payment and payment.amount) else 0.0
    payer_id = payment.payer_id if (payment and payment.payer_id) else 1
    payer_type = payment.payer_type if (payment and payment.payer_type) else "driver"
    customer_phone = ""

    cf_headers = {
        "x-client-id": settings.CASHFREE_APP_ID,
        "x-client-secret": settings.CASHFREE_SECRET_KEY,
        "x-api-version": settings.CASHFREE_API_VERSION,
    }

    is_live_config = bool(
        settings.CASHFREE_APP_ID and 
        settings.CASHFREE_SECRET_KEY and 
        not settings.CASHFREE_APP_ID.startswith("YOUR_") and
        not settings.CASHFREE_APP_ID.startswith("CF_APP_LETZRYD_TEST")
    )

    if is_live_config:
        try:
            ord_res = requests.get(f"{settings.CASHFREE_BASE_URL}/orders/{order_id}", headers=cf_headers, timeout=10)
            if ord_res.status_code == 200:
                ord_data = ord_res.json()
                if ord_data.get("order_status") == "PAID":
                    is_success = True
                if ord_data.get("order_amount"):
                    paid_amount = float(ord_data.get("order_amount"))
                cust = ord_data.get("customer_details") or {}
                customer_phone = clean_phone_number(cust.get("customer_phone") or "")
                c_id = str(cust.get("customer_id") or "")
                if "CUST_" in c_id:
                    parts = c_id.replace("CUST_", "").split("_")
                    if parts and parts[0].isdigit():
                        payer_id = int(parts[0])
        except Exception as e:
            print(f"[ERROR] Verifying order from Cashfree: {e}")

        try:
            cf_res = requests.get(f"{settings.CASHFREE_BASE_URL}/orders/{order_id}/payments", headers=cf_headers, timeout=10)
            if cf_res.status_code == 200:
                payments_data = cf_res.json()
        except Exception as e:
            print(f"[ERROR] Verifying payments with Cashfree API: {e}")

        if isinstance(payments_data, list):
            for p in payments_data:
                if p.get("payment_status") == "SUCCESS":
                    is_success = True
                    payment_mode = p.get("payment_group", "Cashfree")
                    cf_payment_id = str(p.get("cf_payment_id", ""))
                    if p.get("payment_amount"):
                        paid_amount = float(p.get("payment_amount"))
                    break

    # If DB record already marked SUCCESS, preserve success state
    if payment and payment.status == "SUCCESS":
        is_success = True

    cascade_result = {}

    try:
        if not payment and is_success and paid_amount > 0:
            if customer_phone:
                d_match = resolve_driver(customer_phone, db)
                if d_match:
                    payer_id = d_match.app_driver_id
            payment = AppPayments(
                payment_type="collection",
                payer_type=payer_type,
                payer_id=payer_id,
                payee_type="letzryd",
                amount=paid_amount,
                payment_mode=payment_mode,
                status="INITIATED",
                cf_order_id=order_id,
                cf_payment_id=cf_payment_id,
                initiated_at=datetime.now(timezone.utc)
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)

        if payment and is_success and payment.status != "SUCCESS":
            payment.status = "SUCCESS"
            payment.cf_payment_id = cf_payment_id or f"cf_pay_{uuid.uuid4().hex[:8]}"
            payment.completed_at = datetime.now(timezone.utc)
            payment.payment_mode = payment_mode
            cascade_result = _apply_payment_success(payment, db)
            db.commit()
        elif payment and payment.status == "SUCCESS":
            cascade_result = {"note": "Already processed previously"}
        elif payment and not is_success:
            terminal_statuses = ["FAILED", "CANCELLED", "USER_DROPPED"]
            if any(p.get("payment_status") in terminal_statuses for p in payments_data):
                payment.status = "FAILED"
                db.commit()
    except Exception as e:
        db.rollback()
        print(f"[WARN] DB update during verify skipped: {e}")

    return {
        "order_id": order_id,
        "is_success": is_success,
        "status": "SUCCESS" if is_success else ("FAILED" if (payment and payment.status == "FAILED") else "PENDING"),
        "payment_mode": payment_mode,
        "cf_payment_id": cf_payment_id or (payment.cf_payment_id if payment else None),
        "amount": paid_amount,
        "paid_amount": paid_amount,
        "data": payments_data,
        "cascade_updates": cascade_result,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT: Payment history query
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/history")
def get_payment_history(payer_id: Optional[int] = None, payer_type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(AppPayments)
    if payer_id is not None:
        query = query.filter(AppPayments.payer_id == payer_id)
    if payer_type is not None:
        query = query.filter(AppPayments.payer_type == payer_type)

    payments = query.order_by(AppPayments.initiated_at.desc()).all()
    return {"count": len(payments), "data": payments}


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT: Cashfree Webhook (server-side, fires on real transactions)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/webhook/cashfree")
async def cashfree_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receives server-side webhook from Cashfree on payment events.
    Verifies cryptographic signature using Cashfree secret key (HMAC-SHA256).
    Applies cascade update on verified transactions.
    """
    signature = request.headers.get("x-webhook-signature")
    timestamp = request.headers.get("x-webhook-timestamp", "")
    body_bytes = await request.body()

    if not signature or not verify_cashfree_signature(timestamp, body_bytes, signature, settings.CASHFREE_SECRET_KEY):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")

    try:
        payload = json.loads(body_bytes.decode('utf-8'))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")

    data_dict = payload.get("data", payload)
    order_data = data_dict.get("order") or payload.get("order") or {}
    payment_data = data_dict.get("payment") or payload.get("payment") or {}

    order_id = order_data.get("order_id")
    payment_status = payment_data.get("payment_status", "")
    if payload.get("type") == "PAYMENT_SUCCESS_WEBHOOK":
        payment_status = "SUCCESS"

    if order_id and payment_status == "SUCCESS":
        payment = db.query(AppPayments).filter(AppPayments.cf_order_id == order_id).with_for_update().first()
        if payment and payment.status != "SUCCESS":
            payment.status = "SUCCESS"
            payment.completed_at = datetime.now(timezone.utc)
            payment.raw_response = payload
            cf_payment_id = str(payment_data.get("cf_payment_id", ""))
            if cf_payment_id:
                payment.cf_payment_id = cf_payment_id
            payment_mode = payment_data.get("payment_group", "Cashfree")
            payment.payment_mode = payment_mode
            if payment_data.get("payment_amount"):
                payment.amount = float(payment_data.get("payment_amount"))
            # Cascade update
            _apply_payment_success(payment, db)

    return {"status": "OK"}
