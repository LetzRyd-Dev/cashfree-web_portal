import { User, HisaabWeek, Ticket, Notification, Vehicle, RentalPlan } from './types';

const envBackend = import.meta.env.VITE_BACKEND_URL;
export const BACKEND_URL = (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'))
  ? (envBackend || 'http://127.0.0.1:8000')
  : (envBackend && !envBackend.includes('cashfree-web-portal-925756819101')
      ? envBackend 
      : 'https://letzryd-portal-925756819101.asia-south1.run.app');

async function apiCall<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
  });

  if (response.status === 404) {
    return null as any;
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || `API request failed: ${response.statusText}`);
  }

  return response.json();
}

export function mapDriverToUser(d: any): User {
  return {
    id: d.driver_code || `LR-DRV-${d.app_driver_id}`,
    app_driver_id: d.app_driver_id ? Number(d.app_driver_id) : undefined,
    app_operator_id: d.app_operator_id ? Number(d.app_operator_id) : (d.operator_id ? Number(d.operator_id) : undefined),
    name: d.full_name || 'Driver',
    operatorCode: d.driver_code || '',
    phone: d.phone || '',
    joined: d.joined_date || '',
    initials: d.initials || (d.full_name ? d.full_name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase() : 'D'),
    aadhar: d.aadhar_number || '',
    dlNumber: d.dl_number || '',
    dlExpiry: d.dl_expiry || '',
    emergencyContact: d.emergency_name ? `${d.emergency_name}${d.emergency_relation ? ` (${d.emergency_relation})` : ''}${d.emergency_phone ? ` - ${d.emergency_phone}` : ''}` : '',
    emergencyName: d.emergency_name || '',
    emergencyRelation: d.emergency_relation || '',
    emergencyPhone: d.emergency_phone || '',
    address: d.address || 'LetzRyd Operations Hub, Bengaluru',
    bloodGroup: d.blood_group || '',
    dob: d.dob || '',
    operatorType: d.operator_name ? `Fleet: ${d.operator_name}` : 'LetzRyd Partner',
    assignedManagerName: d.assigned_manager_name || 'LetzRyd Operations Desk',
    assignedManagerPhone: d.assigned_manager_phone || '080-4568-1234',
    depositAmount: d.deposit_total_req || 0,
    depositTotalRequired: d.deposit_total_req || 0,
    depositPaidSoFar: d.deposit_paid || 0,
    depositPending: d.deposit_pending || 0,
    depositNextDueDate: d.deposit_next_due || '',
    cumulativeOwed: Number(d.cumulative_owed ?? d.cw_to_collect ?? (d.cw_os && d.cw_os > 0 ? d.cw_os : 0)),
    weeklyIncentiveTargetTrips: d.incentive_trips_target || 260,
    completedTripsThisWeek: d.cw_incentive_trips_done || 0,
    weeklyIncentiveReward: d.incentive_reward_amt || 1500,
    operatorName: d.operator_name || undefined,
    isFleetDriver: Boolean(d.is_fleet_driver || (d.operator_id && d.operator_id > 0)),
    isFleetManaged: Boolean(d.is_fleet_driver || (d.operator_id && d.operator_id > 0)),
  };
}

export function mapOperatorToUser(op: any): User {
  return {
    id: op.operator_code || `LR-OPR-${op.app_operator_id}`,
    app_operator_id: op.app_operator_id ? Number(op.app_operator_id) : undefined,
    name: op.company_name || op.contact_person_name || 'Fleet Operator',
    operatorCode: op.operator_code || '',
    phone: op.phone || '',
    joined: '',
    initials: op.initials || (op.company_name ? op.company_name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase() : 'OP'),
    aadhar: '',
    dlNumber: '',
    dlExpiry: '',
    emergencyContact: op.assigned_manager_phone ? `${op.assigned_manager_name || 'LetzRyd Operations Desk'} - ${op.assigned_manager_phone}` : '',
    emergencyName: op.assigned_manager_name || 'LetzRyd Operations Desk',
    emergencyRelation: 'Account Manager',
    emergencyPhone: op.assigned_manager_phone || '080-4568-1234',
    address: op.address || 'LetzRyd Operations Hub, Bengaluru',
    bloodGroup: '',
    dob: '',
    operatorType: 'Fleet Owner',
    assignedManagerName: op.assigned_manager_name || 'LetzRyd Operations Desk',
    assignedManagerPhone: op.assigned_manager_phone || '080-4568-1234',
    depositAmount: op.deposit_total_req || 0,
    depositTotalRequired: op.deposit_total_req || 0,
    depositPaidSoFar: op.deposit_paid || 0,
    depositPending: op.deposit_pending || 0,
    depositNextDueDate: '',
    cumulativeOwed: op.cw_to_collect || 0,
    weeklyIncentiveTargetTrips: 0,
    completedTripsThisWeek: 0,
    weeklyIncentiveReward: 0,
    operatorName: op.company_name || 'Fleet Operator',
    isFleetDriver: false,
    isFleetManaged: false,
  };
}

export function mapDriverToVehicle(d: any): Vehicle {
  const regNumber = (d.vehicle_reg_number || '').trim();
  const hasVehicle = Boolean(regNumber && regNumber !== 'Unassigned' && regNumber !== 'None');
  return {
    number: hasVehicle ? regNumber : 'Unassigned',
    make: hasVehicle ? (d.vehicle_make || 'Maruti') : '',
    model: hasVehicle ? (d.vehicle_model || 'Dzire CNG') : '',
    variant: hasVehicle ? (d.vehicle_variant || 'VXi') : '',
    year: hasVehicle ? (d.vehicle_year || 2021) : 0,
    color: hasVehicle ? (d.vehicle_color || 'White') : '',
    fuelType: hasVehicle ? (d.vehicle_fuel_type || 'CNG') : '',
    odometer: hasVehicle ? (d.vehicle_odometer_km || 0) : 0,
    fitnessExpiry: hasVehicle ? (d.fitness_expiry || '') : '',
    insuranceExpiry: hasVehicle ? (d.insurance_expiry || '') : '',
    rcExpiry: hasVehicle ? (d.rc_expiry || '') : '',
    permitType: hasVehicle ? (d.permit_type || '') : '',
    permitExpiry: hasVehicle ? (d.permit_expiry || '') : '',
    pucExpiry: hasVehicle ? (d.puc_expiry || '') : '',
    lastUpdatedOn: d.doc_last_updated || '',
    platforms: {
      uber: { status: 'active', rating: 4.87, trips: d.cw_trips || 0 },
      ola: { status: 'active', rating: 4.75, trips: 0 },
      rapido: { status: 'active', rating: 4.90, trips: 0 },
    },
    allocationStart: d.vehicle_allocated_from || d.joined_date || '',
  };
}

export function mapDriverToRentalPlan(d: any): RentalPlan {
  const dailyRate = d.vehicle_daily_rate || 1000;
  const planName = `${d.vehicle_make || ''} ${d.vehicle_model || ''}`.trim();
  return {
    name: planName ? `${planName} - Commercial Rental Plan` : 'Commercial Rental Plan',
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
    const currentWeekOs = Number(h.current_period_os) || 0;
    const toCollect = (h.to_collect !== undefined && h.to_collect !== null)
      ? Number(h.to_collect)
      : (currentWeekOs > 0 ? currentWeekOs : 0);
    const toPay = (h.to_pay !== undefined && h.to_pay !== null)
      ? Number(h.to_pay)
      : (currentWeekOs < 0 ? Math.abs(currentWeekOs) : 0);
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
      currentWeekOs,
      pendingDue: toCollect,
      totalOs: currentWeekOs,
      toCollect,
      toPay,
      letzrydEarning: h.letzryd_earning || 0,
      notes: h.notes || '',
    // Payment tracking from DB
    paidAmount: h.paid_amount || 0,
    paymentStatus: (h.payment_status as any) || 'unpaid',
    app_hisaab_id: h.app_hisaab_id || undefined,
    isFleetManaged: Boolean(h.is_fleet_managed || (h.app_operator_id && h.app_operator_id > 0)),
    grossEarnings: Number(h.total_gross_earnings || ((h.uber_revenue || 0) + (h.ola_revenue || 0) + (h.rapido_revenue || 0) + (h.uber_toll || 0) + (h.ola_toll || 0) + (h.rapido_toll || 0) + (h.uber_incentive || 0) + (h.ola_incentive || 0) + (h.rapido_incentive || 0))),
    cashCollected: Math.abs(Number(h.uber_cash || 0)) + Math.abs(Number(h.ola_cash || 0)) + Math.abs(Number(h.rapido_cash || 0)),
    totalKm: Number(h.total_km || (h.gps_total_km || 0) || ((h.uber_km || 0) + (h.ola_km || 0) + (h.rapido_km || 0))),
    completedTrips: Number(h.completed_trips || ((h.uber_trips || 0) + (h.ola_trips || 0) + (h.rapido_trips || 0))),
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

export async function getDriverHisaabs(driverId: number): Promise<any[]> {
  const res: any = await apiCall(`/api/hisaabs/driver/${driverId}`);
  if (Array.isArray(res)) return res;
  if (res && Array.isArray(res.data)) return res.data;
  return [];
}

export async function getOperatorHisaabs(operatorId: number | string): Promise<any[]> {
  const res: any = await apiCall(`/api/hisaabs/operator/${operatorId}`);
  if (Array.isArray(res)) return res;
  if (res && Array.isArray(res.data)) return res.data;
  return [];
}

export async function getVehicleHisaabs(vehicleNumber: string): Promise<any[]> {
  const clean = vehicleNumber.replace(/\s+/g, '');
  const res: any = await apiCall(`/api/hisaabs/vehicle/${clean}`);
  if (Array.isArray(res)) return res;
  if (res && Array.isArray(res.data)) return res.data;
  return [];
}

export async function getNotifications(targetId: number, targetType?: string): Promise<any> {
  const typeParam = targetType ? `&target_type=${targetType}` : '';
  return apiCall(`/api/notifications?target_id=${targetId}${typeParam}`);
}

export async function markNotificationRead(notifId: number | string): Promise<any> {
  const cleanId = String(notifId).replace(/^NOTIF-/, '');
  return apiCall(`/api/notifications/${cleanId}/read`, { method: 'PUT' });
}

export async function getTickets(creatorId: number, creatorType?: string): Promise<any> {
  const typeParam = creatorType ? `&creator_type=${creatorType}` : '';
  const res: any = await apiCall(`/api/tickets?creator_id=${creatorId}${typeParam}`);
  return res.data || res;
}

export async function updateTicketStatus(
  ticketId: number | string,
  status: string,
  resolutionNote?: string
): Promise<Ticket> {
  const cleanId = String(ticketId).replace(/^TKT-/, '');
  const res = await apiCall(`/api/tickets/${cleanId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status, resolution_note: resolutionNote }),
  });
  return mapTicket(res);
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

