"""
helpers.py — Shared normalization, alias resolution, and lookups
"""
import re
from typing import Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.app_models import AppDrivers, AppOperators

DRIVER_PHONE_ALIASES = {
    "9876543210": "9901484683",  # Demo Driver 1 (Vivek)
    "9876543211": "9140631755",  # Demo Driver 2 (Sushant)
    "9876543212": "9930420065",  # Demo Driver 3 (Aayush)
}

OPERATOR_PHONE_ALIASES = {
    "9876543222": "9691938866",  # Demo Operator 1 (Anurag & RK Fleet)
    "9876543223": "9848012345",  # Demo Operator 2 (Saleem Fleet)
}

def clean_phone_number(raw_phone: str) -> str:
    """Strip country codes (+91, 0091, 91), leading zeroes, spaces, dashes and non-numeric chars."""
    if not raw_phone:
        return ""
    digits = re.sub(r"[^\d]", "", str(raw_phone))
    if not digits:
        return ""
    # Strip leading 00 (international call prefix) e.g. 0091...
    if digits.startswith("00"):
        digits = digits.lstrip("0")
    # If starts with 91 and total length >= 12, strip country code 91
    if digits.startswith("91") and len(digits) >= 12:
        digits = digits[2:]
    # Strip any leading trunk 0 (e.g. 09876543210 or leftover after 91)
    digits = digits.lstrip("0")
    # If at least 10 digits remain and starts with standard Indian mobile prefix (6-9), keep last 10 digits
    if len(digits) > 10 and digits[-10] in "6789":
        digits = digits[-10:]
    return digits

LEGACY_DRIVER_ID_MAP = {
    157: 1,  # Vivek
    202: 2,  # Sushant
    312: 3,  # Aayush
    41: 4,   # Anurag Driver
    418: 5,  # Mohammed Ali
    501: 6,  # Anil Verma
}

def resolve_driver(phone_or_id: str, db: Session) -> Optional[AppDrivers]:
    """Find AppDrivers by clean phone, alias phone, driver_code, ID, or prefix-stripped ID."""
    if not phone_or_id:
        return None
    raw = str(phone_or_id).strip()
    if not raw:
        return None

    # 1. Driver code lookup (case-insensitive) - e.g. LETZBLR..., DRV-AL-..., LR-DRV-0418
    driver = db.query(AppDrivers).filter(func.lower(AppDrivers.driver_code) == raw.lower()).first()
    if driver:
        return driver

    clean = clean_phone_number(raw)
    
    if clean:
        # 2. Alias phone match (e.g. 9876543210 -> Vivek 9901484683)
        if clean in DRIVER_PHONE_ALIASES:
            aliased_phone = DRIVER_PHONE_ALIASES[clean]
            driver = db.query(AppDrivers).filter(AppDrivers.phone == aliased_phone).first()
            if driver:
                return driver
                
        # 3. Direct phone match (10 digits)
        if len(clean) == 10:
            driver = db.query(AppDrivers).filter(
                (AppDrivers.phone == clean) |
                (func.right(func.regexp_replace(AppDrivers.phone, '[^0-9]', '', 'g'), 10) == clean)
            ).first()
            if driver:
                return driver

    # 4. Numeric ID match or Prefix Stripping (e.g. LR-DRV-123 -> ID 123)
    num_id = None
    if raw.isdigit() and len(clean) != 10:
        num_id = int(raw)
    else:
        # Match prefixes like LR-DRV-123, DRV-123, LR-123, DRIVER-123
        m = re.match(r'^(?:LR[-_]?)?(?:DRV|DRIVER)[-_]?(\d+)$', raw, flags=re.IGNORECASE)
        if not m:
            m = re.match(r'^LR[-_](\d+)$', raw, flags=re.IGNORECASE)
        if m:
            num_id = int(m.group(1))

    if num_id is not None:
        if num_id in LEGACY_DRIVER_ID_MAP:
            driver = db.query(AppDrivers).filter(AppDrivers.app_driver_id == LEGACY_DRIVER_ID_MAP[num_id]).first()
            if driver:
                return driver
        if num_id > 0:
            driver = db.query(AppDrivers).filter(AppDrivers.app_driver_id == num_id).first()
            if driver:
                return driver
            driver = db.query(AppDrivers).filter(AppDrivers.driver_id == num_id).first()
            if driver:
                return driver

    # 5. Fallback phone match if phone number was not 10 digits
    if clean and len(clean) >= 7:
        driver = db.query(AppDrivers).filter(AppDrivers.phone == clean).first()
        if driver:
            return driver

    # 6. Zero-Delay Auto-Provisioning Fallback from core_partner_onboarding
    if clean and len(clean) == 10:
        try:
            from sqlalchemy import text
            res = db.execute(text("""
                SELECT id, driver_name, phone_number, security_deposit, partner_id
                FROM public.core_partner_onboarding
                WHERE RIGHT(REGEXP_REPLACE(COALESCE(phone_number, ''), '[^0-9]', '', 'g'), 10) = :phone
                  AND (onboarding_type IS NULL OR onboarding_type NOT ILIKE '%operator%')
                  AND (is_deleted IS NULL OR is_deleted = FALSE)
                ORDER BY id DESC LIMIT 1
            """), {"phone": clean}).fetchone()
            if res:
                p_id, p_name, p_phone, p_dep, p_code = res
                req_dep = float(p_dep) if p_dep else 5000.0
                new_driver = AppDrivers(
                    driver_id=p_id,
                    operator_id=0,
                    full_name=p_name or "Driver",
                    phone=clean,
                    initials=(p_name[:2].upper() if p_name else "DR"),
                    driver_code=p_code or f"DRV-{p_id}",
                    deposit_total_req=req_dep,
                    deposit_paid=0.0,
                    deposit_pending=req_dep,
                    upi_id=f"{clean}@upi",
                    is_active=True
                )
                db.add(new_driver)
                db.commit()
                db.refresh(new_driver)
                return new_driver
        except Exception as e:
            print(f"[WARN] Auto-provisioning from core_partner_onboarding skipped: {e}")
            db.rollback()

    return None

def resolve_operator(phone_or_id: str, db: Session) -> Optional[AppOperators]:
    """Find AppOperators by clean phone, alias phone, operator_code, ID, or prefix-stripped ID."""
    if not phone_or_id:
        return None
    raw = str(phone_or_id).strip()
    if not raw:
        return None

    # 1. Operator code lookup (case-insensitive) - e.g. OP-501, OPR-HYD-001, LETZBLR...
    op = db.query(AppOperators).filter(func.lower(AppOperators.operator_code) == raw.lower()).first()
    if op:
        return op

    clean = clean_phone_number(raw)

    if clean:
        # 2. Alias phone match (e.g. 9876543222 -> Anurag 9691938866)
        if clean in OPERATOR_PHONE_ALIASES:
            aliased_phone = OPERATOR_PHONE_ALIASES[clean]
            op = db.query(AppOperators).filter(AppOperators.phone == aliased_phone).first()
            if op:
                return op

        # 3. Direct phone match (10 digits)
        if len(clean) == 10:
            op = db.query(AppOperators).filter(
                (AppOperators.phone == clean) |
                (func.right(func.regexp_replace(AppOperators.phone, '[^0-9]', '', 'g'), 10) == clean)
            ).first()
            if op:
                return op

    # 4. Numeric ID match or Prefix Stripping (e.g. LR-OP-123, OP-123, OPR-123, LR-OPR-123)
    num_id = None
    if raw.isdigit() and len(clean) != 10:
        num_id = int(raw)
    else:
        m = re.match(r'^(?:LR[-_]?)?(?:OP|OPR|OPERATOR)[-_]?(\d+)$', raw, flags=re.IGNORECASE)
        if not m:
            m = re.match(r'^LR[-_](\d+)$', raw, flags=re.IGNORECASE)
        if m:
            num_id = int(m.group(1))

    if num_id is not None and num_id >= 0:
        op = db.query(AppOperators).filter(AppOperators.app_operator_id == num_id).first()
        if op:
            return op
        op = db.query(AppOperators).filter(AppOperators.operator_id == num_id).first()
        if op:
            return op

    # 5. Fallback phone match if phone number was not 10 digits
    if clean and len(clean) >= 7:
        op = db.query(AppOperators).filter(AppOperators.phone == clean).first()
        if op:
            return op

    # 6. Zero-Delay Auto-Provisioning Fallback from core_partner_onboarding for Operators
    if clean and len(clean) == 10:
        try:
            from sqlalchemy import text
            res = db.execute(text("""
                SELECT id, driver_name, phone_number, security_deposit, partner_id
                FROM public.core_partner_onboarding
                WHERE RIGHT(REGEXP_REPLACE(COALESCE(phone_number, ''), '[^0-9]', '', 'g'), 10) = :phone
                  AND (onboarding_type ILIKE '%operator%' OR partner_id ILIKE '%OP%' OR partner_id ILIKE '%IP%')
                  AND (is_deleted IS NULL OR is_deleted = FALSE)
                ORDER BY id DESC LIMIT 1
            """), {"phone": clean}).fetchone()
            if res:
                p_id, p_name, p_phone, p_dep, p_code = res
                req_dep = float(p_dep) if p_dep else 10000.0
                comp_name = p_name or "Fleet Operator"
                new_op = AppOperators(
                    operator_id=p_id,
                    operator_code=p_code or f"OPR-{p_id}",
                    phone=clean,
                    company_name=comp_name,
                    contact_person_name=p_name or comp_name,
                    initials=(comp_name[:2].upper() if comp_name else "OP"),
                    deposit_total_req=req_dep,
                    deposit_paid=0.0,
                    deposit_pending=req_dep,
                    upi_id=f"{clean}@upi",
                    is_active=True
                )
                db.add(new_op)
                db.commit()
                db.refresh(new_op)
                return new_op
        except Exception as e:
            print(f"[WARN] Operator auto-provisioning from core_partner_onboarding skipped: {e}")
            db.rollback()

    return None
