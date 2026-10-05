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
from app.services.helpers import clean_phone_number, resolve_driver

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
    expected_sig = base64.b64encode(
        hmac.new(secret_key.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).digest()
    ).decode('utf-8')
    return hmac.compare_digest(signature, expected_sig)


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPER — called after Cashfree confirms payment SUCCESS
# Updates: app_hisaabs, app_drivers/app_operators, app_notifications
# ─────────────────────────────────────────────────────────────────────────────
def _apply_payment_success(payment: AppPayments, db: Session) -> dict:
    """
    After a real Cashfree payment is confirmed SUCCESS, cascade the update to:
      1. app_hisaabs  → paid_amount, payment_status, status, is_locked
      2. app_drivers  → lw_status, cw_to_collect, cw_os  (driver payers)
      3. app_operators → lw_status (operator payers)
      4. app_notifications → fire a payment receipt notification

    Returns a summary dict of what was updated.
    """
    updated = {"hisaab": None, "driver": None, "operator": None, "notification": None}
    paid_amount = float(payment.amount or 0)

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
        driver = db.query(AppDrivers).filter(AppDrivers.app_driver_id == payment.payer_id).first()
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
                t_due = float(target_hisaab.to_collect or 0)
                t_prev_paid = float(target_hisaab.paid_amount or 0)
                t_rem_due = max(0.0, t_due - t_prev_paid)
                t_pay = min(t_rem_due, rem_cash) if t_rem_due > 0 else rem_cash

                target_hisaab.paid_amount = t_prev_paid + t_pay
                if target_hisaab.paid_amount >= t_due and t_due > 0:
                    target_hisaab.payment_status = "settled"
                    target_hisaab.status = "settled"
                    target_hisaab.current_period_os = 0.0
                elif target_hisaab.paid_amount > 0:
                    target_hisaab.payment_status = "partial"
                    target_hisaab.current_period_os = max(0.0, t_due - target_hisaab.paid_amount)

                # Deduct from driver's cw_to_collect or lw_os
                if target_hisaab.week_number >= active_week_num or not target_hisaab.is_locked:
                    driver.cw_to_collect = max(0.0, float(driver.cw_to_collect or 0) - t_pay)
                    driver.cw_os = max(0.0, float(driver.cw_os or 0) - t_pay)
                else:
                    driver.lw_os = max(0.0, float(driver.lw_os or 0) - t_pay)
                    if driver.lw_os <= 0:
                        driver.lw_status = "paid"
                    else:
                        driver.lw_status = "partial"

                rem_cash = max(0.0, rem_cash - t_pay)

            # Tier 2: Pay pending security deposit
            if rem_cash > 0:
                dep_pending = float(driver.deposit_pending or 0)
                total_req = float(driver.deposit_total_req or 6000.0)
                dep_credit = min(dep_pending, rem_cash)
                driver.deposit_paid = min(total_req, float(driver.deposit_paid or 0) + dep_credit)
                driver.deposit_pending = max(0.0, total_req - driver.deposit_paid)
                rem_cash = max(0.0, rem_cash - dep_credit)

            # Tier 3: Pay any other unpaid/prior hisaabs for this driver
            if rem_cash > 0:
                other_unpaid_hisaabs = db.query(AppHisaabs).filter(
                    AppHisaabs.app_driver_id == driver.app_driver_id,
                    AppHisaabs.to_collect > 0,
                    AppHisaabs.payment_status != "settled"
                ).order_by(AppHisaabs.week_number.desc()).all()

                for oh in other_unpaid_hisaabs:
                    if rem_cash <= 0:
                        break
                    if target_hisaab and oh.app_hisaab_id == target_hisaab.app_hisaab_id:
                        continue
                    oh_due = float(oh.to_collect or 0)
                    oh_prev_paid = float(oh.paid_amount or 0)
                    oh_rem_due = max(0.0, oh_due - oh_prev_paid)
                    oh_pay = min(oh_rem_due, rem_cash)

                    oh.paid_amount = oh_prev_paid + oh_pay
                    if oh.paid_amount >= oh_due:
                        oh.payment_status = "settled"
                        oh.status = "settled"
                        oh.current_period_os = 0.0
                    elif oh.paid_amount > 0:
                        oh.payment_status = "partial"
                        oh.current_period_os = max(0.0, oh_due - oh.paid_amount)

                    # Update driver lw_os if prior week
                    if oh.week_number < active_week_num or oh.is_locked:
                        driver.lw_os = max(0.0, float(driver.lw_os or 0) - oh_pay)
                        if driver.lw_os <= 0:
                            driver.lw_status = "paid"
                        else:
                            driver.lw_status = "partial"
                    else:
                        driver.cw_to_collect = max(0.0, float(driver.cw_to_collect or 0) - oh_pay)

                    rem_cash = max(0.0, rem_cash - oh_pay)

            # Tier 4: Any remaining surplus becomes driver advance credit
            if rem_cash > 0:
                driver.cw_to_collect = 0.0
                driver.cw_os = -rem_cash
                driver.cw_to_pay = rem_cash
                # Also reflect in active week hisaab as payout credit
                cw_h = db.query(AppHisaabs).filter(
                    AppHisaabs.app_driver_id == driver.app_driver_id,
                    AppHisaabs.week_number == active_week_num
                ).first()
                if cw_h:
                    cw_h.current_period_os = -rem_cash
                    cw_h.to_pay = rem_cash

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
        op = db.query(AppOperators).filter(AppOperators.app_operator_id == payment.payer_id).first()
        if op:
            # Tier 1: Pay down operator fleet driver debts (e.g. Sushant who owes ₹1,850)
            fleet_drivers_with_debt = db.query(AppDrivers).filter(
                AppDrivers.operator_id == op.app_operator_id,
                AppDrivers.cw_to_collect > 0
            ).order_by(AppDrivers.app_driver_id).all()

            rem_for_debt = paid_amount
            for d in fleet_drivers_with_debt:
                if rem_for_debt <= 0:
                    break
                d_due = float(d.cw_to_collect or 0)
                d_paid = min(d_due, rem_for_debt)
                d.cw_to_collect = max(0.0, d_due - d_paid)
                d.cw_os = max(0.0, float(d.cw_os or 0) - d_paid)
                if d.cw_to_collect <= 0:
                    d.lw_status = "paid"
                else:
                    d.lw_status = "partial"

                # Also update that driver's weekly hisaab record(s)
                d_hisaabs = db.query(AppHisaabs).filter(
                    AppHisaabs.app_driver_id == d.app_driver_id
                ).order_by(AppHisaabs.week_number.desc()).all()
                rem_h_paid = d_paid
                for dh in d_hisaabs:
                    if rem_h_paid <= 0:
                        break
                    dh_due = float(dh.to_collect or 0)
                    if dh_due > 0 and dh.payment_status != "settled":
                        cur_paid = float(dh.paid_amount or 0)
                        h_pay = min(max(0.0, dh_due - cur_paid), rem_h_paid)
                        dh.paid_amount = cur_paid + h_pay
                        if dh.paid_amount >= dh_due:
                            dh.payment_status = "settled"
                            dh.status = "settled"
                        elif dh.paid_amount > 0:
                            dh.payment_status = "partial"
                        rem_h_paid -= h_pay

                rem_for_debt -= d_paid

            # Operator total fleet debt remaining
            all_op_drivers = db.query(AppDrivers).filter(AppDrivers.operator_id == op.app_operator_id).all()
            op.cw_to_collect = sum(float(d.cw_to_collect or 0) for d in all_op_drivers)
            if op.cw_to_collect <= 0:
                op.lw_status = "paid"
            else:
                op.lw_status = "partial"

            excess_after_debt = max(0.0, rem_for_debt)

            # Tier 2: Pay down operator pending security deposit
            dep_pending = float(op.deposit_pending or 0)
            dep_payment = min(dep_pending, excess_after_debt)
            total_dep_req = float(op.deposit_total_req or 25000.0)
            op.deposit_paid = min(total_dep_req, float(op.deposit_paid or 0) + dep_payment)
            op.deposit_pending = max(0.0, total_dep_req - float(op.deposit_paid))

            # Tier 3: Any leftover surplus beyond debt & deposit increases operator payout credit
            excess_after_deposit = max(0.0, excess_after_debt - dep_payment)
            if excess_after_deposit > 0:
                op.cw_to_pay = float(op.cw_to_pay or 0) + excess_after_deposit

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
    cf_order_id = f"ORDER_LR_{uuid.uuid4().hex[:10].upper()}"
    now = datetime.now(timezone.utc)

    payment = AppPayments(
        payment_type="collection",
        payer_type=req.payer_type,
        payer_id=req.payer_id,
        payee_type="letzryd",
        app_hisaab_id=req.app_hisaab_id,
        amount=req.amount,
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
    """Creates a real Cashfree PG order and returns live session ID."""
    try:
        amt = float(req.amount)
    except (ValueError, TypeError):
        amt = 1.0

    order_id = f"ORDER_LR_{uuid.uuid4().hex[:10].upper()}"
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

    try:
        cf_res = requests.post(f"{settings.CASHFREE_BASE_URL}/orders", json=cf_payload, headers=cf_headers, timeout=10)
        cf_data = cf_res.json()
        if cf_res.status_code == 200 and cf_data.get("payment_session_id"):
            session_id = cf_data["payment_session_id"]
            cf_ord_id = cf_data.get("order_id", order_id)
        else:
            err_msg = cf_data.get("message") or cf_data.get("error") or str(cf_data)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Cashfree Payment Gateway Error: {err_msg}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to Cashfree Payment Gateway: {str(e)}"
        )

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
    cf_headers = {
        "x-client-id": settings.CASHFREE_APP_ID,
        "x-client-secret": settings.CASHFREE_SECRET_KEY,
        "x-api-version": settings.CASHFREE_API_VERSION,
    }

    is_success = False
    payment_mode = "Cashfree Gateway"
    cf_payment_id = None
    payments_data = []

    try:
        cf_res = requests.get(f"{settings.CASHFREE_BASE_URL}/orders/{order_id}/payments", headers=cf_headers, timeout=10)
        if cf_res.status_code == 200:
            payments_data = cf_res.json()
    except Exception as e:
        print(f"[ERROR] Verifying with Cashfree API: {e}")

    paid_amount = 0.0
    payer_id = 1
    payer_type = "driver"
    customer_phone = ""

    # 1. Query Cashfree Order endpoint to check order_status
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

    # 2. Query Cashfree Payments list endpoint
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

    cascade_result = {}

    # 3. Update or synthesize DB record and cascade to hisaab/driver/operator
    payment = None
    try:
        payment = db.query(AppPayments).filter(AppPayments.cf_order_id == order_id).first()
        if not payment and is_success and paid_amount > 0:
            # If DB record was omitted during create-order (e.g. timeout), resolve driver & synthesize now
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
            payment.cf_payment_id = cf_payment_id
            payment.completed_at = datetime.now(timezone.utc)
            payment.payment_mode = payment_mode
            # Cascade update to all related records
            cascade_result = _apply_payment_success(payment, db)
        elif payment and (is_success or payment.status == "SUCCESS"):
            # Already processed — return current state
            is_success = True
            cascade_result = {"note": "Already processed previously"}
    except Exception as e:
        print(f"[WARN] DB update during verify skipped: {e}")

    return {
        "order_id": order_id,
        "is_success": is_success,
        "status": "SUCCESS" if is_success else "PENDING",
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

    order_id = payload.get("order", {}).get("order_id")
    payment_status = payload.get("payment", {}).get("payment_status", "")

    if order_id and payment_status == "SUCCESS":
        payment = db.query(AppPayments).filter(AppPayments.cf_order_id == order_id).first()
        if payment and payment.status != "SUCCESS":
            payment.status = "SUCCESS"
            payment.completed_at = datetime.now(timezone.utc)
            payment.raw_response = payload
            cf_payment_id = str(payload.get("payment", {}).get("cf_payment_id", ""))
            if cf_payment_id:
                payment.cf_payment_id = cf_payment_id
            payment_mode = payload.get("payment", {}).get("payment_group", "Cashfree")
            payment.payment_mode = payment_mode
            # Cascade update
            _apply_payment_success(payment, db)

    return {"status": "OK"}
