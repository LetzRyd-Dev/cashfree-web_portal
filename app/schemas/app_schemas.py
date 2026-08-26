from pydantic import BaseModel
from typing import Optional, List, Any, Union
from datetime import date, datetime

class BaseSchema(BaseModel):
    class Config:
        from_attributes = True

# Auth Schemas
class OTPRequest(BaseSchema):
    phone: str
    user_type: str = "driver"

class OTPVerify(BaseSchema):
    phone: str
    otp: str
    user_type: str = "driver"
    fcm_token: Optional[str] = None

class PasswordLogin(BaseSchema):
    phone: str
    password: str
    user_type: str = "driver"

class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    user_type: str
    user_id: int
    name: str

# Driver Schemas
class DriverProfileResponse(BaseSchema):
    app_driver_id: int
    driver_code: str
    phone: str
    full_name: str
    initials: Optional[str] = None
    operator_id: int = 0
    vehicle_reg_number: Optional[str] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_variant: Optional[str] = None
    vehicle_year: Optional[int] = None
    vehicle_color: Optional[str] = None
    vehicle_fuel_type: Optional[str] = None
    vehicle_daily_rate: float = 1000.0
    vehicle_allocated_from: Optional[str] = None
    aadhar_number: Optional[str] = None
    blood_group: Optional[str] = None
    dob: Optional[str] = None
    address: Optional[str] = None
    joined_date: Optional[str] = None
    emergency_name: Optional[str] = None
    emergency_relation: Optional[str] = None
    emergency_phone: Optional[str] = None
    dl_number: Optional[str] = None
    dl_expiry: Optional[str] = None
    rc_number: Optional[str] = None
    rc_expiry: Optional[str] = None
    insurance_number: Optional[str] = None
    insurance_expiry: Optional[str] = None
    permit_type: Optional[str] = None
    permit_number: Optional[str] = None
    permit_expiry: Optional[str] = None
    fitness_number: Optional[str] = None
    fitness_expiry: Optional[str] = None
    puc_expiry: Optional[str] = None
    assigned_manager_name: Optional[str] = None
    assigned_manager_phone: Optional[str] = None
    deposit_total_req: float = 0.0
    deposit_paid: float = 0.0
    deposit_pending: float = 0.0
    referral_code: Optional[str] = None
    referral_reward_amt: float = 1000.0
    incentive_trips_target: int = 260
    incentive_reward_amt: float = 1500.0
    cw_trips: int = 0
    cw_gross_earnings: float = 0.0
    cw_total_km: float = 0.0
    cw_os: float = 0.0
    cw_to_pay: float = 0.0
    cw_to_collect: float = 0.0
    cw_active_days: int = 0
    cw_incentive_trips_done: int = 0
    lw_trips: int = 0
    lw_gross_earnings: float = 0.0
    lw_os: float = 0.0
    lw_week_number: int = 0
    lw_hisaab_number: str = ""
    lw_status: str = "unpaid"
    growth_pct: float = 0.0
    vehicle_odometer_km: Optional[int] = 0
    doc_last_updated: Optional[str] = None
    deposit_next_due: Optional[str] = None
    upi_id: Optional[str] = None
    bank_account_last4: Optional[str] = None

# Operator Schemas
class OperatorProfileResponse(BaseSchema):
    app_operator_id: int
    operator_code: str
    company_name: str
    contact_person_name: Optional[str] = None
    phone: str
    initials: Optional[str] = None
    address: Optional[str] = None
    assigned_manager_name: Optional[str] = None
    assigned_manager_phone: Optional[str] = None
    total_vehicles: int = 0
    active_vehicles: int = 0
    idle_vehicles: int = 0
    total_drivers: int = 0
    deposit_total_req: float = 0.0
    deposit_paid: float = 0.0
    deposit_pending: float = 0.0
    referral_code: Optional[str] = None
    referral_reward_amt: float = 2000.0
    upi_id: Optional[str] = None
    bank_account_last4: Optional[str] = None
    cw_fleet_trips: int = 0
    cw_fleet_gross_earnings: float = 0.0
    cw_to_collect: float = 0.0
    cw_to_pay: float = 0.0
    lw_fleet_trips: int = 0
    lw_fleet_gross_earnings: float = 0.0
    lw_status: str = "unpaid"

class FleetVehicleResponse(BaseSchema):
    vehicle_number: str
    vehicle_make: str
    vehicle_model: str
    driver_name: str
    driver_id: int
    driver_phone: str
    daily_rate: float = 1000.0
    current_week_os: float = 0.0
    status: str = "active"
    hisaab_count: int = 0

class OperatorFleetResponse(OperatorProfileResponse):
    vehicles: List[FleetVehicleResponse] = []

# Hisaab Schemas
class HisaabBreakdownResponse(BaseSchema):
    app_hisaab_id: int
    app_driver_id: int = 0
    hisaab_number: str
    week_number: int
    period_start: Optional[Any] = None
    period_end: Optional[Any] = None
    days_count: int = 7
    status: Optional[str] = "in_progress"
    is_locked: bool = False
    growth_pct: float = 0.0
    uber_trips: int = 0
    uber_revenue: float = 0.0
    uber_cash: float = 0.0
    uber_toll: float = 0.0
    uber_incentive: float = 0.0
    uber_subscription: float = 0.0
    uber_km: float = 0.0
    ola_trips: int = 0
    ola_revenue: float = 0.0
    ola_cash: float = 0.0
    ola_toll: float = 0.0
    ola_incentive: float = 0.0
    ola_subscription: float = 0.0
    ola_km: float = 0.0
    rapido_trips: int = 0
    rapido_revenue: float = 0.0
    rapido_cash: float = 0.0
    rapido_toll: float = 0.0
    rapido_incentive: float = 0.0
    rapido_subscription: float = 0.0
    rapido_km: float = 0.0
    vehicle_daily_rate: float = 1000.0
    vehicle_rent: float = 0.0
    maintenance_charge: float = 0.0
    tds_amount: float = 0.0
    challan_amount: float = 0.0
    accident_charge: float = 0.0
    other_adjustment: float = 0.0
    previous_outstanding: float = 0.0
    gps_total_km: float = 0.0
    gps_ideal_km: float = 0.0
    gps_dead_km: float = 0.0
    gps_dead_pct: float = 0.0
    gps_dead_penalty: float = 0.0
    gps_free_dead_pct: float = 20.0
    gps_penalty_rate: float = 5.0
    completed_trips: int = 0
    total_km: float = 0.0
    total_gross_earnings: float = 0.0
    total_deductions: float = 0.0
    total_penalties: float = 0.0
    current_period_os: float = 0.0
    to_collect: float = 0.0
    to_pay: float = 0.0
    letzryd_earning: float = 0.0
    notes: str = ""
    last_refreshed_at: Optional[str] = None

# Payment Schemas
class InitiatePaymentRequest(BaseSchema):
    amount: float
    payment_mode: str = "cashfree_upi"
    app_hisaab_id: Optional[int] = None
    payer_type: str = "driver"
    payer_id: int

class PaymentResponse(BaseSchema):
    app_payment_id: int
    amount: float
    payment_mode: str
    status: str
    cf_order_id: Optional[str] = None

class CreateOrderRequest(BaseSchema):
    amount: Union[float, str]
    driverName: Optional[str] = "Driver"
    driverPhone: Optional[str] = "9999999999"
    driverId: Optional[Union[str, int]] = "driver_001"
    weekRange: Optional[str] = ""

class CreateOrderResponse(BaseSchema):
    payment_session_id: str
    order_id: str
    order_amount: float
    order_currency: str = "INR"
    order_status: str = "ACTIVE"
    error: Optional[str] = None

# Support Ticket Schemas
class CreateTicketRequest(BaseSchema):
    creator_type: str = "driver"
    creator_id: int
    category: str
    subject: str
    description: str
    priority: str = "medium"

class TicketResponse(BaseSchema):
    app_ticket_id: int
    ticket_number: str
    category: str
    subject: str
    description: Optional[str] = None
    status: str = "open"
    priority: Optional[str] = "medium"
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None

# Notification Schemas
class NotificationResponse(BaseSchema):
    app_notif_id: int
    title: str
    message: str
    notif_type: str
    severity: Optional[str] = "info"
    icon: Optional[str] = None
    is_read: Optional[bool] = False
    created_at: Optional[datetime] = None

# Referral Schemas
class SubmitReferralRequest(BaseSchema):
    referred_by_type: str = "driver"
    referred_by_id: int
    lead_name: str
    lead_phone: str
    referral_code_used: Optional[str] = None

class ReferralResponse(BaseSchema):
    app_referral_id: int
    lead_name: str
    lead_phone: str
    status: str
    reward_amount: float = 1000.0
    reward_credited: bool = False
