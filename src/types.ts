/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export type Language = 'en' | 'hi' | 'mr' | 'te' | 'kn';

export interface User {
  id: string;
  name: string;
  operatorCode: string;
  phone: string;
  joined: string;
  initials: string;
  aadhar: string;
  dlNumber: string;
  dlExpiry: string;
  emergencyContact: string;
  emergencyName?: string;
  emergencyRelation?: string;
  emergencyPhone?: string;
  address: string;
  bloodGroup: string;
  dob: string;
  operatorType?: string;
  assignedManagerName: string;
  assignedManagerPhone: string;
  depositAmount: number;
  depositTotalRequired?: number;
  depositPaidSoFar?: number;
  depositPending?: number;
  depositNextDueDate?: string;
  cumulativeOwed: number;
  weeklyIncentiveTargetTrips: number;
  completedTripsThisWeek: number;
  weeklyIncentiveReward: number;
  referralCode?: string;
}

export interface PlatformStatus {
  status: 'active' | 'inactive';
  rating: number;
  trips: number;
}

export interface Vehicle {
  number: string;
  make: string;
  model: string;
  variant: string;
  year: number;
  color: string;
  fuelType: string;
  odometer: number;
  fitnessExpiry: string;
  insuranceExpiry: string;
  rcExpiry: string;
  permitType: string;
  permitExpiry: string;
  pucExpiry: string;
  lastUpdatedOn: string;
  platforms: {
    uber: PlatformStatus;
    ola: PlatformStatus;
    rapido: PlatformStatus;
  };
  allocationStart: string;
}

export interface RentalPlan {
  name: string;
  dailyRate: number;
  planStart: string;
  activeMonths: number;
  note: string;
}

export interface PlatformEarnings {
  trips: number;
  revenue: number;
  cashCollection: number;
  toll: number;
  incentive: number;
  subscription: number;
  km: number;
}

export interface GpsData {
  totalGpsKm: number;
  idealGpsKm: number;
  deadMile: number;
  deadMilePct: number;
  deadKmPenalty: number;
  allowedFreeDeadKmPct: number;
  penaltyRatePerKm: number;
}

export interface HisaabWeek {
  weekNumber: number;
  hisaabNumber: string;
  weekStart: string;
  weekEnd: string;
  status: 'in_progress' | 'to_collect' | 'settled_pay';
  isLocked: boolean;
  activeDays: number;
  growthPct: number;
  platforms: {
    uber: PlatformEarnings;
    ola: PlatformEarnings;
    rapido: PlatformEarnings;
  };
  rent: {
    dailyRate: number;
    netWeeklyRent: number;
  };
  dailyMaintenance: number;
  previousAdjustments: number;
  tds: number;
  challan: number;
  accident: number;
  adjustment: number;
  paidDeposit: number;
  pendingDeposit: number;
  joiningFeePaid: number;
  pendingJoiningFee: number;
  previousOutstanding: number;
  pendingSinceDate: string;
  gps: GpsData;
  lastRefreshedTime: string;
  currentWeekOs: number;
  pendingDue: number;
  totalOs: number;
  toCollect: number;
  toPay: number;
  letzrydEarning: number;
  notes: string;
}

export interface FleetVehicle {
  number: string;
  make: string;
  model: string;
  driverName: string;
  plan: {
    name: string;
    dailyRate: number;
  };
  currentWeekOs: number;
  status: 'active' | 'idle';
  hisaabWeeks: HisaabWeek[];
}

export interface Fleet {
  operatorCode: string;
  operatorName: string;
  depositTotalRequired?: number;
  depositPaidSoFar?: number;
  depositPending?: number;
  vehicles: FleetVehicle[];
}

export interface Ticket {
  id: string;
  category: string;
  subject: string;
  description: string;
  status: 'open' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high';
  date: string;
  response: string | null;
}

export interface Notification {
  id: string;
  icon: string;
  title: string;
  message: string;
  time: string;
  read: boolean;
}

export interface Announcement {
  id: string;
  title: string;
  message: string;
  severity: 'urgent' | 'warning' | 'info';
  date: string;
}
