import { User, HisaabWeek, Ticket, Notification, Vehicle, RentalPlan } from './types';

export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL 
  || (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
      ? 'http://127.0.0.1:8000' 
      : 'https://letzryd-portal-925756819101.asia-south1.run.app');

async function apiCall<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || `API request failed: ${response.statusText}`);
  }

  return response.json();
}

export function mapDriverToUser(d: any): User {
  return {
    id: d.driver_code || `LR-DRV-${d.app_driver_id}`,
    name: d.full_name || 'Driver',
    operatorCode: d.driver_code || '',
    phone: d.phone || '',
    joined: d.joined_date || '',
    initials: d.initials || (d.full_name ? d.full_name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase() : 'D'),
    aadhar: d.aadhar_number || '',
    dlNumber: d.dl_number || '',
    dlExpiry: d.dl_expiry || '',
    emergencyContact: d.emergency_name ? `${d.emergency_name} (${d.emergency_relation}) - ${d.emergency_phone}` : '',
    emergencyName: d.emergency_name || '',
    emergencyRelation: d.emergency_relation || '',
    emergencyPhone: d.emergency_phone || '',
    address: d.address || '',
    bloodGroup: d.blood_group || '',
    dob: d.dob || '',
    operatorType: 'LetzRyd Partner',
    assignedManagerName: d.assigned_manager_name || '',
    assignedManagerPhone: d.assigned_manager_phone || '',
    depositAmount: d.deposit_total_req || 0,
    depositTotalRequired: d.deposit_total_req || 0,
    depositPaidSoFar: d.deposit_paid || 0,
    depositPending: d.deposit_pending || 0,
    depositNextDueDate: d.deposit_next_due || '',
    cumulativeOwed: Math.abs(d.cw_os || 0),
    weeklyIncentiveTargetTrips: d.incentive_trips_target || 260,
    completedTripsThisWeek: d.cw_incentive_trips_done || 0,
    weeklyIncentiveReward: d.incentive_reward_amt || 1500,
  };
}

export function mapDriverToVehicle(d: any): Vehicle {
  return {
    number: d.vehicle_reg_number || 'KA05AQ7692',
    make: d.vehicle_make || 'Maruti',
    model: d.vehicle_model || 'Dzire CNG',
    variant: d.vehicle_variant || 'VXi',
    year: d.vehicle_year || 2021,
    color: d.vehicle_color || 'White',
    fuelType: d.vehicle_fuel_type || 'CNG',
    odometer: d.vehicle_odometer_km || 124380,
    fitnessExpiry: d.fitness_expiry || '2026-10-12',
    insuranceExpiry: d.insurance_expiry || '2027-03-20',
    rcExpiry: d.rc_expiry || '2036-05-01',
    permitType: d.permit_type || 'Tourist Permit',
    permitExpiry: d.permit_expiry || '2026-12-31',
    pucExpiry: d.puc_expiry || '2026-08-15',
    lastUpdatedOn: d.doc_last_updated || '2026-07-25',
    platforms: {
      uber: { status: 'active', rating: 4.87, trips: d.cw_trips || 233 },
      ola: { status: 'active', rating: 4.75, trips: 65 },
      rapido: { status: 'active', rating: 4.90, trips: 48 },
    },
    allocationStart: d.vehicle_allocated_from || d.joined_date || '2024-10-15',
  };
}

export function mapDriverToRentalPlan(d: any): RentalPlan {
  const dailyRate = d.vehicle_daily_rate || 1000;
  return {
    name: `${d.vehicle_make || ''} ${d.vehicle_model || ''} - Commercial Rental Plan`.trim(),
    dailyRate,
    planStart: d.vehicle_allocated_from || d.joined_date || '2024-10-15',
    activeMonths: 21,
    note: `Standard daily vehicle rental rate of ₹${dailyRate}/day billed on active driving days.`,
  };
}

export function mapHisaabToWeek(h: any): HisaabWeek {
  const status = h.status === 'in_progress' ? 'in_progress'
    : h.status === 'to_collect' ? 'to_collect'
    : 'settled_pay';
  const lastRefreshed = h.last_refreshed_at
    ? new Date(h.last_refreshed_at).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' } as any)
    : '';
  return {
    weekNumber: h.week_number,
    hisaabNumber: h.hisaab_number,
    weekStart: h.period_start,
    weekEnd: h.period_end,
    status,
    isLocked: h.is_locked || false,
    activeDays: h.days_count || 0,
    growthPct: h.growth_pct || 0,
    platforms: {
      uber: { trips: h.uber_trips, revenue: h.uber_revenue, cashCollection: -Math.abs(h.uber_cash), toll: h.uber_toll, incentive: h.uber_incentive, subscription: -Math.abs(h.uber_subscription), km: h.uber_km },
      ola: { trips: h.ola_trips, revenue: h.ola_revenue, cashCollection: -Math.abs(h.ola_cash), toll: h.ola_toll, incentive: h.ola_incentive, subscription: -Math.abs(h.ola_subscription), km: h.ola_km },
      rapido: { trips: h.rapido_trips, revenue: h.rapido_revenue, cashCollection: -Math.abs(h.rapido_cash), toll: h.rapido_toll, incentive: h.rapido_incentive, subscription: -Math.abs(h.rapido_subscription), km: h.rapido_km },
    },
    rent: { dailyRate: h.vehicle_daily_rate || 1000, netWeeklyRent: h.vehicle_rent || 0 },
    dailyMaintenance: h.maintenance_charge || 0,
    previousAdjustments: h.other_adjustment || 0,
    tds: h.tds_amount || 0,
    challan: h.challan_amount || 0,
    accident: h.accident_charge || 0,
    adjustment: h.other_adjustment || 0,
    paidDeposit: 0,
    pendingDeposit: 0,
    joiningFeePaid: 0,
    pendingJoiningFee: 0,
    previousOutstanding: h.previous_outstanding || 0,
    pendingSinceDate: h.period_start || '',
    gps: {
      totalGpsKm: h.gps_total_km || 0,
      idealGpsKm: h.gps_ideal_km || 0,
      deadMile: h.gps_dead_km || 0,
      deadMilePct: h.gps_dead_pct || 0,
      deadKmPenalty: h.gps_dead_penalty || 0,
      allowedFreeDeadKmPct: h.gps_free_dead_pct || 20,
      penaltyRatePerKm: h.gps_penalty_rate || 5,
    },
    lastRefreshedTime: lastRefreshed,
    currentWeekOs: h.current_period_os || 0,
    pendingDue: h.to_collect || 0,
    totalOs: h.current_period_os || 0,
    toCollect: h.to_collect || 0,
    toPay: h.to_pay || 0,
    letzrydEarning: h.letzryd_earning || 0,
    notes: h.notes || '',
  };
}

export function mapNotification(n: any): Notification {
  const timeStr = n.created_at
    ? new Date(n.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })
    : '';
  return {
    id: `NOTIF-${n.app_notif_id}`,
    icon: n.icon || (n.notif_type === 'hisaab' ? 'ReceiptIndianRupee' : n.notif_type === 'payment' ? 'Wallet' : 'Bell'),
    title: n.title || '',
    message: n.message || '',
    time: timeStr,
    read: n.is_read || false,
  };
}

export function mapTicket(t: any): Ticket {
  const status = t.status === 'resolved' ? 'resolved' : t.status === 'closed' ? 'closed' : 'open';
  const priority = t.priority === 'high' ? 'high' : t.priority === 'low' ? 'low' : 'medium';
  return {
    id: t.ticket_number || `TKT-${t.app_ticket_id}`,
    category: t.category || '',
    subject: t.subject || '',
    description: t.description || '',
    status,
    priority,
    date: t.created_at ? t.created_at.split('T')[0] : new Date().toISOString().split('T')[0],
    response: t.resolution_note || null,
  };
}

export async function verifyOTPBackend(phone: string, otp: string, userType: string): Promise<any> {
  return apiCall('/api/auth/otp/verify', {
    method: 'POST',
    body: JSON.stringify({ phone, otp, user_type: userType }),
  });
}

export async function getDriverByPhone(phone: string): Promise<any> {
  return apiCall(`/api/drivers/by-phone/${phone}`);
}

export async function getOperatorFleet(operatorId: number): Promise<any> {
  return apiCall(`/api/operators/${operatorId}/fleet-summary`);
}

export async function getOperatorByPhone(phone: string): Promise<any> {
  return apiCall(`/api/operators/by-phone/${phone}`);
}

export async function getDriverHisaabs(driverId: number): Promise<any> {
  const res: any = await apiCall(`/api/hisaabs/driver/${driverId}`);
  return res.data || res;
}

export async function getNotifications(targetId: number): Promise<any> {
  return apiCall(`/api/notifications?target_id=${targetId}`);
}

export async function getTickets(creatorId: number): Promise<any> {
  const res: any = await apiCall(`/api/tickets?creator_id=${creatorId}`);
  return res.data || res;
}

export async function createTicket(
  creatorType: string,
  creatorId: number,
  category: string,
  subject: string,
  description: string,
  priority: string
): Promise<Ticket> {
  const res = await apiCall(`/api/tickets`, {
    method: 'POST',
    body: JSON.stringify({
      creator_type: creatorType,
      creator_id: creatorId,
      category,
      subject,
      description,
      priority,
    }),
  });
  return mapTicket(res);
}

export async function submitReferral(
  referredByType: string,
  referredById: number,
  leadName: string,
  leadPhone: string,
  referralCode?: string
): Promise<any> {
  return apiCall(`/api/referrals`, {
    method: 'POST',
    body: JSON.stringify({
      referred_by_type: referredByType,
      referred_by_id: referredById,
      lead_name: leadName,
      lead_phone: leadPhone,
      referral_code_used: referralCode,
    }),
  });
}
