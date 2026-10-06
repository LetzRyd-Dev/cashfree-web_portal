import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  X,
  Send,
  CheckCircle,
  XCircle,
  Clock,
  Bell,
  ReceiptIndianRupee,
  FileWarning,
  Award,
  Shield,
  ShieldCheck,
  Landmark,
  CheckCircle2,
  AlertCircle,
  Info,
  AlertTriangle,
  Car,
  FileText,
  BadgeCheck,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  TrendingUp,
  TrendingDown,
  Coins,
  Activity,
  Calculator,
  Compass,
  MapPin,
  CreditCard,
  PhoneCall,
  MessageSquare,
  Ticket as TicketIcon,
  Plus,
  Calendar,
  CheckSquare,
  ArrowLeft,
  User as UserIcon,
  LogOut,
  Edit2,
  Check,
  Heart,
  Building,
  Search,
  AlertOctagon,
  Navigation,
  Copy,
  Smartphone,
  Wallet,
  QrCode,
  Loader2,
  Lock,
  Share2,
  Target,
  Sparkles,
  ShieldAlert,
  ArrowUpRight,
  ArrowRight,
  Users
} from 'lucide-react';

import { User as UserType, Vehicle, HisaabWeek, Fleet, Ticket, Notification, RentalPlan, FleetVehicle, FleetDriverItem, Announcement, Language } from '../types';
import { USER_DATA, VEHICLE_DATA, LETZRYD_UPI_ID, ANNOUNCEMENTS_DATA } from '../data';
import { BACKEND_URL } from '../api';

declare const Cashfree: (config: { mode: string }) => {
  checkout: (options: {
    paymentSessionId: string;
    redirectTarget?: string | HTMLElement | null;
    returnUrl?: string;
  }) => Promise<{
    error?: any;
    redirect?: boolean;
    paymentDetails?: any;
  }>;
};

export const OFFICIAL_MOBILE_HELPLINE = '9988770011';
export const OFFICIAL_LANDLINE_HELPLINE = '080-4568-1234';

export const isLandline = (phoneStr?: string): boolean => {
  if (!phoneStr) return false;
  const str = phoneStr.trim();
  if (str.startsWith('080') || str.startsWith('040') || str.startsWith('022') || str.startsWith('011') || str.startsWith('0800') || str.startsWith('1800')) {
    return true;
  }
  const digits = str.replace(/\D/g, '');
  if (digits.startsWith('080') || digits.startsWith('0800') || digits.startsWith('1800') || digits.startsWith('804568')) {
    return true;
  }
  return false;
};

export const getCleanMobileForWhatsApp = (phoneStr?: string): string => {
  if (!phoneStr || isLandline(phoneStr)) {
    return OFFICIAL_MOBILE_HELPLINE;
  }
  const digits = phoneStr.replace(/\D/g, '');
  const mobile = digits.length === 12 && digits.startsWith('91') 
    ? digits.slice(2) 
    : digits.slice(-10);
  if (/^[6-9]\d{9}$/.test(mobile)) {
    return mobile;
  }
  return OFFICIAL_MOBILE_HELPLINE;
};

/* =========================================================================
   1. REFERRAL SCREEN
   ========================================================================= */
interface ReferralScreenProps {
  driverCode: string;
  onCopy: () => void;
  onBack: () => void;
  t: (key: string, fallback: string) => string;
}

export const ReferralScreen: React.FC<ReferralScreenProps> = ({ driverCode, onCopy, onBack, t }) => {
  const [leadName, setLeadName] = useState('');
  const [leadPhone, setLeadPhone] = useState('');
  const [submittedLead, setSubmittedLead] = useState<string | null>(null);

  const handleSubmitLead = (e: React.FormEvent) => {
    e.preventDefault();
    if (!leadName.trim() || !leadPhone.trim()) return;
    setSubmittedLead(leadName.trim());
    setLeadName('');
    setLeadPhone('');
    setTimeout(() => setSubmittedLead(null), 4000);
  };

  return (
    <div className="space-y-4 text-left font-sans pb-4">
      <div className="flex items-center gap-3 border-b border-border/60 pb-3">
        <button
          onClick={onBack}
          className="w-8 h-8 rounded-xl border border-border bg-surface flex items-center justify-center text-text-muted hover:text-text cursor-pointer transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div>
          <h2 className="font-sans text-base font-extrabold text-text">
            {t('refer.title', 'Refer Driver & Earn ₹1,000')}
          </h2>
          <p className="font-sans text-xs text-text-muted">
            {t('refer.subtitle', 'Invite EV drivers to LetzRyd and get ₹1,000 credited to your weekly Hisaab.')}
          </p>
        </div>
      </div>

      <div className="bg-gradient-to-r from-primary to-primary-hover text-white rounded-2xl p-4 shadow-sm space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-white/80">{t('refer.programReward', 'PROGRAM REWARD')}</span>
          <span className="bg-white/20 text-white font-mono font-extrabold text-xs px-2.5 py-0.5 rounded-full backdrop-blur-xs">
            ₹1,000 / {t('refer.perDriver', 'Driver')}
          </span>
        </div>
        <p className="font-sans text-xs font-medium leading-relaxed text-white/90">
          {t('refer.rewardInfo', 'Receive ₹1,000 credit directly in your next weekly Hisaab when your referred driver completes 50 rides.')}
        </p>
      </div>

      {submittedLead && (
        <div className="bg-green-light border border-green/30 text-green rounded-xl p-3 text-xs font-bold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{t('refer.leadSubmitted', 'Lead submitted successfully! Our team will contact them within 24h.')}</span>
        </div>
      )}

      <div className="bg-surface border border-border/80 rounded-2xl p-4 shadow-xs space-y-2.5">
        <h3 className="font-sans text-[11px] font-bold text-text uppercase tracking-wider text-text-muted">
          {t('refer.yourCode', 'Your Referral Code')}
        </h3>

        <div className="flex items-center justify-between bg-bg/60 border border-border/70 rounded-xl p-3">
          <div>
            <span className="font-mono text-base font-black text-primary tracking-wide">{driverCode}</span>
          </div>

          <button
            onClick={onCopy}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold cursor-pointer shadow-xs transition-all active:scale-95"
          >
            <Copy className="w-3.5 h-3.5" />
            {t('refer.copyCode', 'Copy Code')}
          </button>
        </div>
      </div>

      <div className="bg-surface border border-border/80 rounded-2xl p-4 shadow-xs space-y-3">
        <h3 className="font-sans text-[11px] font-bold text-text uppercase tracking-wider text-text-muted">
          {t('refer.submitLeadTitle', 'Direct Lead Referral')}
        </h3>

        <form onSubmit={handleSubmitLead} className="space-y-3 font-sans text-xs">
          <div>
            <label className="text-text-muted font-medium block mb-1">
              {t('refer.leadName', 'Driver Name')}
            </label>

            <input
              type="text"
              required
              value={leadName}
              onChange={(e) => setLeadName(e.target.value)}
              placeholder={t('refer.namePlaceholder', 'e.g. Ramesh Verma')}
              className="w-full h-9.5 rounded-xl border border-border bg-bg px-3 font-bold text-text text-xs outline-none focus:border-primary transition-colors"
            />
          </div>

          <div>
            <label className="text-text-muted font-medium block mb-1">
              {t('refer.leadPhone', 'Mobile Number')}
            </label>

            <input
              type="tel"
              required
              value={leadPhone}
              onChange={(e) => setLeadPhone(e.target.value)}
              placeholder={t('refer.phonePlaceholder', '10-digit Mobile No.')}
              className="w-full h-9.5 rounded-xl border border-border bg-bg px-3 font-bold text-text text-xs outline-none focus:border-primary font-mono transition-colors"
            />
          </div>

          <button
            type="submit"
            className="w-full h-10 mt-1 rounded-xl bg-green hover:bg-green-hover text-white font-sans text-xs font-extrabold cursor-pointer shadow-xs transition-all flex items-center justify-center gap-2 active:scale-98"
          >
            <Send className="w-4 h-4" />
            {t('refer.submitBtn', 'Submit Lead & Earn ₹1,000')}
          </button>
        </form>
      </div>

      <div className="bg-surface border border-border/80 rounded-2xl p-4 shadow-xs space-y-3">
        <h3 className="font-sans text-[11px] font-bold text-text uppercase tracking-wider text-text-muted">
          {t('refer.referredDriversTitle', 'Your Referred Drivers')}
        </h3>

        <div className="divide-y divide-border/50 font-sans text-xs">
          <div className="py-2 flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/10 text-primary font-bold text-xs flex items-center justify-center shrink-0 border border-primary/20">
                SK
              </div>
              <div>
                <p className="font-sans font-bold text-text">Suresh Kumar</p>
                <p className="font-mono text-[11px] text-text-muted">+91 9876543212</p>
              </div>
            </div>

            <span className="font-sans text-[10px] font-bold text-green-700 bg-green-50 border border-green-200 px-2.5 py-1 rounded-full flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-green-600" />
              {t('refer.referredBadge', 'Referred')}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

/* =========================================================================
   2. VEHICLE SCREEN
   ========================================================================= */
interface VehicleScreenProps {
  vehicle: Vehicle;
  onOpenDoc?: (doc: 'rc' | 'insurance' | 'permit' | 'aadhar' | 'dl') => void;
  t: (key: string, fallback: string) => string;
}

export const VehicleScreen: React.FC<VehicleScreenProps> = ({ vehicle, t }) => {
  const isUnassigned = !vehicle?.number || vehicle.number === 'Unassigned' || vehicle.number.toLowerCase() === 'unassigned' || !vehicle.number.trim();

  const formatIndianDate = (dateStr: string) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    const day = String(d.getDate()).padStart(2, '0');
    const month = d.toLocaleString('en-IN', { month: 'short' });
    const year = d.getFullYear();
    return `${day}-${month}-${year}`;
  };

  const maskLastFour = (str: string) => {
    if (!str) return '•••• ----';
    const clean = str.replace(/\s+/g, '');
    const lastFour = clean.slice(-4);
    return `•••• ${lastFour}`;
  };

  const getDocStatusBadge = (expiryDateStr: string) => {
    if (!expiryDateStr) {
      return (
        <span className="bg-gray-100 text-gray-600 border border-gray-200 text-[10px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-1 shrink-0">
          Unknown
        </span>
      );
    }
    const expiry = new Date(expiryDateStr);
    if (isNaN(expiry.getTime())) return null;
    const now = new Date();
    const diffDays = Math.ceil((expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return (
        <span className="bg-red-50 text-red-700 border border-red-200 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 shrink-0">
          <AlertTriangle className="w-2.5 h-2.5 text-red-600" />
          Expired
        </span>
      );
    } else if (diffDays <= 30) {
      return (
        <span className="bg-amber-50 text-amber-700 border border-amber-200 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 shrink-0">
          <Clock className="w-2.5 h-2.5 text-amber-600" />
          Expiring ({diffDays}d)
        </span>
      );
    } else {
      return (
        <span className="bg-green-light text-green border border-green-200 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 shrink-0">
          <CheckCircle2 className="w-2.5 h-2.5 text-green" />
          Valid
        </span>
      );
    }
  };

  if (isUnassigned) {
    return (
      <div className="space-y-4 text-left font-sans">
        <div className="flex items-center justify-between">
          <h2 className="font-sans text-base font-bold text-text">
            {t('vehicle.title', 'Vehicle Details')}
          </h2>
          <span className="bg-amber-100 text-amber-800 border border-amber-300 text-[10px] font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-amber-600" />
            No Vehicle Assigned
          </span>
        </div>

        <div className="bg-surface border border-border/80 rounded-2xl p-6 text-center shadow-xs space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-600 flex items-center justify-center mx-auto">
            <Car className="w-6 h-6 text-amber-600" />
          </div>
          <div>
            <h3 className="font-sans text-sm font-bold text-text">No Vehicle Assigned</h3>
            <p className="font-sans text-xs text-text-muted max-w-xs mx-auto mt-1 leading-relaxed">
              There is currently no commercial vehicle allocated to your driver profile. Please contact your fleet operator or the LetzRyd operations desk for vehicle allocation.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 text-left font-sans">
      <div className="flex items-center justify-between">
        <h2 className="font-sans text-base font-bold text-text">
          {t('vehicle.title', 'Vehicle Details')}
        </h2>
        <span className="font-mono text-xs font-bold text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded-md">
          {vehicle.number}
        </span>
      </div>

      <div className="bg-surface border border-border rounded-xl p-3.5 shadow-sm text-left font-sans text-xs space-y-2.5">
        <div className="border-b border-border/60 pb-2">
          <h3 className="font-sans text-xs font-bold text-text uppercase tracking-wider">
            {t('vehicle.specifications', 'SPECIFICATIONS')}
          </h3>
        </div>

        <div className="divide-y divide-border/60">
          <div className="py-2 flex items-center justify-between first:pt-0 last:pb-0">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-bg border border-border text-primary flex items-center justify-center shrink-0">
                <Car className="w-3.5 h-3.5" />
              </div>
              <span className="font-sans text-xs font-semibold text-text">{t('home.vehicleNumber', 'Vehicle Number')}</span>
            </div>
            <span className="font-sans text-xs font-bold text-text">
              {vehicle.number}
            </span>
          </div>

          <div className="py-2 flex items-center justify-between first:pt-0 last:pb-0">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-bg border border-border text-primary flex items-center justify-center shrink-0">
                <Award className="w-3.5 h-3.5" />
              </div>
              <span className="font-sans text-xs font-semibold text-text">{t('vehicle.brand', 'Brand')}</span>
            </div>
            <span className="font-sans text-xs font-bold text-text">{vehicle.make}</span>
          </div>

          <div className="py-2 flex items-center justify-between first:pt-0 last:pb-0">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-bg border border-border text-primary flex items-center justify-center shrink-0">
                <Car className="w-3.5 h-3.5" />
              </div>
              <span className="font-sans text-xs font-semibold text-text">{t('vehicle.model', 'Model')}</span>
            </div>
            <span className="font-sans text-xs font-bold text-text">{vehicle.model}</span>
          </div>

          <div className="py-2 flex items-center justify-between first:pt-0 last:pb-0">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-bg border border-border text-primary flex items-center justify-center shrink-0">
                <FileText className="w-3.5 h-3.5" />
              </div>
              <span className="font-sans text-xs font-semibold text-text">{t('vehicle.variant', 'Variant')}</span>
            </div>
            <span className="font-sans text-xs font-bold text-text">{vehicle.variant}</span>
          </div>

          <div className="py-2 flex items-center justify-between first:pt-0 last:pb-0">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-bg border border-border text-primary flex items-center justify-center shrink-0">
                <Calendar className="w-3.5 h-3.5" />
              </div>
              <span className="font-sans text-xs font-semibold text-text">{t('vehicle.regYear', 'Registration Year')}</span>
            </div>
            <span className="font-sans text-xs font-bold text-text">{vehicle.year}</span>
          </div>

          <div className="py-2 flex items-center justify-between first:pt-0 last:pb-0">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-bg border border-border text-primary flex items-center justify-center shrink-0">
                <Activity className="w-3.5 h-3.5" />
              </div>
              <span className="font-sans text-xs font-semibold text-text">Fuel & Color</span>
            </div>
            <span className="font-sans text-xs font-bold text-text">{vehicle.fuelType || 'CNG'} • {vehicle.color || 'White'}</span>
          </div>

          <div className="py-2 flex items-center justify-between first:pt-0 last:pb-0">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-bg border border-border text-primary flex items-center justify-center shrink-0">
                <Navigation className="w-3.5 h-3.5" />
              </div>
              <span className="font-sans text-xs font-semibold text-text">Odometer Reading</span>
            </div>
            <span className="font-mono text-xs font-bold text-text">{vehicle.odometer ? `${vehicle.odometer.toLocaleString('en-IN')} km` : '124,380 km'}</span>
          </div>

          {vehicle.allocationStart && (
            <div className="py-2 flex items-center justify-between first:pt-0 last:pb-0">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-bg border border-border text-primary flex items-center justify-center shrink-0">
                  <Clock className="w-3.5 h-3.5" />
                </div>
                <span className="font-sans text-xs font-semibold text-text">Allocation Date</span>
              </div>
              <span className="font-sans text-xs font-bold text-text">{formatIndianDate(vehicle.allocationStart)}</span>
            </div>
          )}
        </div>
      </div>

      <div className="bg-surface border border-border rounded-xl p-3.5 shadow-sm text-left font-sans text-xs space-y-2.5">
        <div className="flex items-center justify-between border-b border-border/60 pb-2">
          <h3 className="font-sans text-xs font-bold text-text uppercase tracking-wider">
            {t('vehicle.documents', 'DOCUMENTS')}
          </h3>
          <span className="font-sans text-[10px] font-medium text-text-muted">
            {t('vehicle.updated', 'Updated')} {formatIndianDate(vehicle.lastUpdatedOn)}
          </span>
        </div>

        <div className="divide-y divide-border/60">
          {/* RC */}
          <div className="py-2 flex items-center justify-between first:pt-0 last:pb-0">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-bg border border-border text-primary flex items-center justify-center shrink-0">
                <FileText className="w-3.5 h-3.5" />
              </div>
              <div>
                <p className="font-sans text-xs font-semibold text-text">{t('vehicle.rc', 'Registration Certificate (RC)')}</p>
                <p className="font-mono text-[11px] font-bold text-primary mt-0.5">{maskLastFour(vehicle.number || '7692')}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {getDocStatusBadge(vehicle.rcExpiry)}
              <div className="text-right">
                <span className="font-sans text-[9px] text-text-muted uppercase block">{t('vehicle.expires', 'Expires')}</span>
                <p className="font-sans text-[11px] font-bold text-text mt-0.2">{formatIndianDate(vehicle.rcExpiry)}</p>
              </div>
            </div>
          </div>

          {/* Insurance */}
          <div className="py-2 flex items-center justify-between first:pt-0 last:pb-0">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-bg border border-border text-primary flex items-center justify-center shrink-0">
                <Shield className="w-3.5 h-3.5" />
              </div>
              <div>
                <p className="font-sans text-xs font-semibold text-text">{t('vehicle.insurance', 'Insurance')}</p>
                <p className="font-mono text-[11px] font-bold text-primary mt-0.5">{maskLastFour('INS2140')}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {getDocStatusBadge(vehicle.insuranceExpiry)}
              <div className="text-right">
                <span className="font-sans text-[9px] text-text-muted uppercase block">{t('vehicle.expires', 'Expires')}</span>
                <p className="font-sans text-[11px] font-bold text-text mt-0.2">{formatIndianDate(vehicle.insuranceExpiry)}</p>
              </div>
            </div>
          </div>

          {/* Permit */}
          <div className="py-2 flex items-center justify-between first:pt-0 last:pb-0">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-bg border border-border text-primary flex items-center justify-center shrink-0">
                <BadgeCheck className="w-3.5 h-3.5" />
              </div>
              <div>
                <p className="font-sans text-xs font-semibold text-text">{t('vehicle.permit', 'Permit')}</p>
                <p className="font-mono text-[11px] font-bold text-primary mt-0.5">{maskLastFour('PRM8912')}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {getDocStatusBadge(vehicle.permitExpiry)}
              <div className="text-right">
                <span className="font-sans text-[9px] text-text-muted uppercase block">{t('vehicle.expires', 'Expires')}</span>
                <p className="font-sans text-[11px] font-bold text-text mt-0.2">{formatIndianDate(vehicle.permitExpiry)}</p>
              </div>
            </div>
          </div>

          {/* Fitness Certificate (FC) */}
          <div className="py-2 flex items-center justify-between first:pt-0 last:pb-0">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-bg border border-border text-primary flex items-center justify-center shrink-0">
                <CheckCircle2 className="w-3.5 h-3.5 text-green" />
              </div>
              <div>
                <p className="font-sans text-xs font-semibold text-text">{t('vehicle.fc', 'Fitness Certificate (FC)')}</p>
                <p className="font-mono text-[11px] font-bold text-primary mt-0.5">{maskLastFour('FIT4401')}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {getDocStatusBadge(vehicle.fitnessExpiry)}
              <div className="text-right">
                <span className="font-sans text-[9px] text-text-muted uppercase block">{t('vehicle.expires', 'Expires')}</span>
                <p className="font-sans text-[11px] font-bold text-text mt-0.2">{formatIndianDate(vehicle.fitnessExpiry)}</p>
              </div>
            </div>
          </div>

          {/* PUC (Pollution Certificate) */}
          {vehicle.pucExpiry && (
            <div className="py-2 flex items-center justify-between first:pt-0 last:pb-0">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-bg border border-border text-primary flex items-center justify-center shrink-0">
                  <Award className="w-3.5 h-3.5" />
                </div>
                <div>
                  <p className="font-sans text-xs font-semibold text-text">PUC Certificate</p>
                  <p className="font-mono text-[11px] font-bold text-primary mt-0.5">{maskLastFour('PUC8921')}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {getDocStatusBadge(vehicle.pucExpiry)}
                <div className="text-right">
                  <span className="font-sans text-[9px] text-text-muted uppercase block">{t('vehicle.expires', 'Expires')}</span>
                  <p className="font-sans text-[11px] font-bold text-text mt-0.2">{formatIndianDate(vehicle.pucExpiry)}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/* =========================================================================
   3. HISAAB SCREEN
   ========================================================================= */
interface HisaabScreenProps {
  weeks: HisaabWeek[];
  weekIndex: number;
  onPrevWeek: () => void;
  onNextWeek: () => void;
  loginType: 'driver' | 'operator';
  onPayClick: (amount: number) => void;
  t: (key: string, fallback: string) => string;
  olaSyncStatusText?: string;
  fleetVehicles?: FleetVehicle[];
  selectedVehicleNumber?: string | null;
  onSelectVehicle?: (number: string) => void;
  isFleetManaged?: boolean;
  operatorName?: string;
}

export const HisaabScreen: React.FC<HisaabScreenProps> = ({
  weeks,
  weekIndex,
  onPrevWeek,
  onNextWeek,
  loginType,
  onPayClick,
  t,
  olaSyncStatusText,
  fleetVehicles,
  selectedVehicleNumber,
  onSelectVehicle,
  isFleetManaged,
  operatorName
}) => {
  const [uberOpen, setUberOpen] = useState(false);
  const [olaOpen, setOlaOpen] = useState(false);
  const [rapidoOpen, setRapidoOpen] = useState(false);
  const [computationOpen, setComputationOpen] = useState(false);
  const [gpsOpen, setGpsOpen] = useState(false);
  const [depositOpen, setDepositOpen] = useState(false);

  if (weeks.length === 0) {
    if (loginType !== 'operator' && (isFleetManaged || operatorName)) {
      return (
        <div className="space-y-4 font-sans text-left py-4">
          <div className="bg-surface border border-border/80 rounded-2xl p-5 shadow-xs text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center mx-auto">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h3 className="font-extrabold text-sm text-text">Fleet Managed Vehicle</h3>
            <p className="text-xs text-text-muted leading-relaxed">
              Vehicle managed by Operator <strong className="text-text">{operatorName || 'Fleet Operator'}</strong>.<br />
              Settlements handled by your fleet manager.
            </p>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-500/10 text-amber-700 border border-amber-500/20 rounded-full text-[11px] font-semibold">
              <Info className="w-3.5 h-3.5" />
              Payments handled by Fleet Operator
            </div>
          </div>
        </div>
      );
    }
    return (
      <div className="space-y-3 font-sans text-left">
        <div className="py-12 text-center text-text-muted flex flex-col items-center justify-center font-sans">
          <Activity className="w-12 h-12 opacity-35 mb-3" />
          <p className="text-sm font-semibold">{t('hisaab.noData', 'No records found for this vehicle')}</p>
        </div>
      </div>
    );
  }

  const w = weeks[weekIndex] || weeks[0];
  if (!w) return null;

  const formatCurrency = (val: number, decimals: number = 0) => {
    return (val < 0 ? '-' : '') + '₹' + Math.abs(val).toLocaleString('en-IN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
  };

  const renderPlatformSection = (
    platformKey: 'uber' | 'ola' | 'rapido',
    title: string,
    isOpen: boolean,
    setIsOpen: (val: boolean) => void,
    colorClass: string
  ) => {
    const plat = w.platforms[platformKey];
    if (!plat) return null;

    const netAmt = plat.revenue + plat.cashCollection + plat.toll + plat.incentive + plat.subscription;

    return (
      <div className="bg-surface border border-border/80 rounded-2xl overflow-hidden shadow-xs transition-all">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full px-3.5 py-3 bg-surface flex items-center justify-between cursor-pointer text-left focus:outline-none"
        >
          <div className="flex items-center gap-3">
            {platformKey === 'uber' && (
              <div className="w-7 h-7 rounded-xl bg-black text-white flex items-center justify-center shrink-0 font-extrabold text-[10px] font-sans tracking-tighter shadow-2xs">
                Uber
              </div>
            )}
            {platformKey === 'ola' && (
              <div className="w-7 h-7 rounded-xl bg-[#111111] text-[#00E676] border border-[#222222] flex items-center justify-center shrink-0 font-black text-[11px] font-sans tracking-tighter shadow-2xs">
                OLA
              </div>
            )}
            {platformKey === 'rapido' && (
              <div className="w-7 h-7 rounded-xl bg-[#111111] text-[#FFC107] border border-[#222222] flex items-center justify-center shrink-0 font-black text-[7.5px] font-sans uppercase tracking-tighter shadow-2xs leading-none">
                RAPIDO
              </div>
            )}
            <span className="font-sans text-xs font-bold text-text">{t('platform.' + platformKey, title)} {t('hisaab.earnings', 'Earnings')}</span>
          </div>

          <div className="flex items-center gap-3">
            <span className={`font-sans text-xs font-bold ${netAmt >= 0 ? 'text-green' : 'text-red-600'}`}>
              {formatCurrency(netAmt)}
            </span>
            <ChevronDown className={`w-4 h-4 text-text-muted transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
          </div>
        </button>

        {isOpen && (
          <div className="p-3.5 space-y-2.5 border-t border-border/60 text-left font-sans text-xs">
            <div className="flex justify-between items-center">
              <span className="text-text-muted font-medium">{t('hisaab.tripsCompleted', 'Trips Completed')}</span>
              <span className="text-text font-bold font-mono">{plat.trips} rides</span>
            </div>
            <div className="h-px bg-border" />
            <div className="flex justify-between items-center">
              <span className="text-text-muted font-medium">{t('hisaab.digitalEarnings', 'Digital Earnings')}</span>
              <span className="text-green font-bold font-mono">+{formatCurrency(plat.revenue)}</span>
            </div>
            <div className="flex justify-between items-center">
              <div>
                <span className="text-text-muted font-medium">{t('hisaab.cashCollected', 'Cash Collected')}</span>
                <p className="text-[10px] text-text-dim">{t('hisaab.driverHoldsFares', 'Driver holds fares')}</p>
              </div>
              <span className="text-red-600 font-bold font-mono">-{formatCurrency(Math.abs(plat.cashCollection))}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-text-muted font-medium">{t('hisaab.tollPassThrough', 'Toll Refund')}</span>
              <span className="text-green font-bold font-mono">+{formatCurrency(plat.toll)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-text-muted font-medium">{t('hisaab.incentives', 'Platform Incentives')}</span>
              <span className="text-green font-bold font-mono">+{formatCurrency(plat.incentive)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-text-muted font-medium">{t('hisaab.subscriptionDeduction', 'Platform Subscription')}</span>
              <span className="text-red-600 font-bold font-mono">-{formatCurrency(Math.abs(plat.subscription))}</span>
            </div>
          </div>
        )}
      </div>
    );
  };

  const formatIndianDate = (dateStr: string) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    const day = String(d.getDate()).padStart(2, '0');
    const month = d.toLocaleString('en-IN', { month: 'short' });
    const year = d.getFullYear();
    return `${day}-${month}-${year}`;
  };

  const formatTimestamp = (tsStr?: string) => {
    if (!tsStr) return '28-Jul-2026, 02:15 PM';
    const parts = tsStr.trim().split(' ');
    if (parts.length >= 2 && parts[0].includes('-')) {
      const [datePart, ...timeParts] = parts;
      const d = new Date(datePart + 'T00:00:00');
      if (!isNaN(d.getTime())) {
        const day = String(d.getDate()).padStart(2, '0');
        const month = d.toLocaleString('en-IN', { month: 'short' });
        const year = d.getFullYear();
        return `${day}-${month}-${year}, ${timeParts.join(' ')}`;
      }
    }
    return tsStr;
  };

  return (
    <div className="space-y-3.5 text-left font-sans pb-4">
      {/* FLEET OPERATOR INFORMATIONAL TAG */}
      {loginType !== 'operator' && (isFleetManaged || w.isFleetManaged) && (
        <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-2xl flex items-center justify-between gap-2 font-sans text-xs">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-amber-600 shrink-0" />
            <div className="min-w-0">
              <span className="font-bold text-amber-800 text-[11px] block leading-tight">
                Payments handled by Fleet Operator
              </span>
              <span className="text-[10px] text-text-muted block leading-none mt-0.5">
                {operatorName ? `Managed by ${operatorName}` : 'Settlements billed to your fleet operator account'}
              </span>
            </div>
          </div>
          <span className="font-bold text-[10px] text-amber-700 bg-amber-100/60 px-2 py-0.5 rounded-full shrink-0 border border-amber-300/40">
            Auto-Billed
          </span>
        </div>
      )}


      {/* 1. WEEK SELECTOR & DATE NAVIGATOR CARD */}
      <div className="bg-surface border border-border/80 rounded-2xl p-3.5 shadow-xs space-y-3 font-sans">
        <div className="border-b border-border/60 pb-2.5 space-y-1">
          <div className="flex justify-between items-center">
            <div className="font-sans text-xs flex items-center gap-2 flex-wrap">
              <span className="font-extrabold text-text text-sm">{t('hisaab.weekLabel', 'Week')} #{w.weekNumber}</span>
              <span className="text-[10px] font-bold text-text-muted font-mono bg-bg px-2 py-0.5 rounded-md border border-border/50">
                {w.hisaabNumber}
              </span>
            </div>

            <div className="text-right flex items-center">
              {w.paymentStatus === 'settled' || w.status === 'settled_pay' ? (
                <span className="flex items-center gap-1.5 font-sans text-[10px] font-bold text-green bg-green-light border border-green-200/50 px-2.5 py-1 rounded-full">
                  <CheckCircle2 className="w-3 h-3 text-green" />
                  Settled
                </span>
              ) : w.paymentStatus === 'partial' ? (
                <span className="flex items-center gap-1.5 font-sans text-[10px] font-bold text-amber-700 bg-amber-50 border border-amber-200/80 px-2.5 py-1 rounded-full">
                  <Clock className="w-3 h-3 text-amber-600" />
                  Partial Paid
                </span>
              ) : w.weekNumber < 30 || w.isLocked ? (
                <span className="flex items-center gap-1.5 font-sans text-[10px] font-bold text-red-700 bg-red-50 border border-red-200/80 px-2.5 py-1 rounded-full">
                  <AlertCircle className="w-3 h-3 text-red-600" />
                  Payment Due
                </span>
              ) : (
                <span className="flex items-center gap-1.5 font-sans text-[10px] font-bold text-blue-700 bg-blue-50 border border-blue-200/80 px-2.5 py-1 rounded-full">
                  <Clock className="w-3 h-3 text-blue-600 animate-spin" style={{ animationDuration: '4s' }} />
                  {t('hisaab.inProgress', 'In Progress')}
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between text-[10px] font-medium text-text-muted pt-0.5">
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3 text-text-muted shrink-0" />
              <span>{t('hisaab.lastUpdated', 'Last Updated')}:</span>
              <span className="font-mono text-text font-semibold whitespace-nowrap">{formatTimestamp(w.lastRefreshedTime)}</span>
            </div>
            {olaSyncStatusText && (
              <span className="flex items-center gap-1 font-mono text-[9px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-md">
                <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                {olaSyncStatusText}
              </span>
            )}
          </div>
        </div>

        {/* Date Navigator Bar */}
        <div className="flex items-center gap-2">
          <button
            onClick={onPrevWeek}
            disabled={weekIndex >= weeks.length - 1}
            className="w-8 h-8 rounded-xl border border-border/80 bg-surface flex items-center justify-center text-text-muted hover:text-text hover:bg-bg disabled:opacity-40 cursor-pointer transition-all shadow-2xs shrink-0"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <div className="flex-1 py-1.5 px-3 rounded-xl border border-border/60 bg-bg flex items-center justify-center gap-2 font-sans text-xs font-bold text-text">
            <span>{formatIndianDate(w.weekStart)}</span>
            <span className="text-[9px] font-semibold text-text-muted uppercase tracking-wider px-0.5">{t('hisaab.toDate', 'TO')}</span>
            <span>{formatIndianDate(w.weekEnd)}</span>
          </div>

          <button
            onClick={onNextWeek}
            disabled={weekIndex === 0}
            className="w-8 h-8 rounded-xl border border-border/80 bg-surface flex items-center justify-center text-text-muted hover:text-text hover:bg-bg disabled:opacity-40 cursor-pointer transition-all shadow-2xs shrink-0"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 2. MERGED WEEKLY HISAAB STATEMENT CARD */}
      {(() => {
        const totalRides = (w.platforms.uber?.trips || 0) + (w.platforms.ola?.trips || 0) + (w.platforms.rapido?.trips || 0);
        const uberNet = w.platforms.uber ? (w.platforms.uber.revenue + w.platforms.uber.cashCollection + w.platforms.uber.toll + w.platforms.uber.incentive + w.platforms.uber.subscription) : 0;
        const olaNet = w.platforms.ola ? (w.platforms.ola.revenue + w.platforms.ola.cashCollection + w.platforms.ola.toll + w.platforms.ola.incentive + w.platforms.ola.subscription) : 0;
        const rapidoNet = w.platforms.rapido ? (w.platforms.rapido.revenue + w.platforms.rapido.cashCollection + w.platforms.rapido.toll + w.platforms.rapido.incentive + w.platforms.rapido.subscription) : 0;

        const totalEarnings = uberNet + olaNet + rapidoNet;
        const totalDeductions = (w.rent.netWeeklyRent || 0) + (w.dailyMaintenance || 0) + (w.tds || 0) + (w.accident || 0);
        const totalPenalties = (w.challan || 0) + (w.gps.deadKmPenalty || 0);

        return (
          <div className="bg-surface border border-border/80 rounded-2xl p-4 shadow-xs space-y-3.5 font-sans relative overflow-hidden">
            <div className="border-b border-dashed border-border/80 pb-2.5 space-y-1">
              <div className="flex justify-between items-center">
                <span className="text-[11px] font-black text-text uppercase tracking-wider flex items-center gap-1.5">
                  <ReceiptIndianRupee className="w-4 h-4 text-primary" />
                  {t('hisaab.billTitle', 'WEEKLY HISAAB STATEMENT')}
                </span>
                <span className="text-[10px] font-bold text-text-muted font-mono bg-bg px-2 py-0.5 rounded border border-border/60">
                  {t('hisaab.weekLabel', 'Week')} #{w.weekNumber}
                </span>
              </div>

              <div className="flex items-center gap-1 text-[10px] font-medium text-text-muted whitespace-nowrap pt-0.5">
                <Clock className="w-3 h-3 text-text-muted shrink-0" />
                <span>{t('hisaab.lastUpdated', 'Last Updated')}:</span>
                <span className="font-mono text-text font-semibold whitespace-nowrap">{formatTimestamp(w.lastRefreshedTime)}</span>
              </div>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-text-muted font-medium">{t('hisaab.totalRides', 'Total Rides')}</span>
                <span className="font-mono font-bold text-text">{totalRides} {t('hisaab.ridesUnit', 'Rides')}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-text-muted font-medium">{t('hisaab.totalEarnings', 'Total Earnings')}</span>
                <span className="font-mono font-bold text-green">+{formatCurrency(totalEarnings)}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-text-muted font-medium">{t('hisaab.totalFeesRent', 'Total Fees & Rent')}</span>
                <span className="font-mono font-bold text-red-600">-{formatCurrency(totalDeductions)}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-text-muted font-medium">{t('hisaab.totalPenalties', 'Total Penalties')}</span>
                <span className={`font-mono font-bold ${totalPenalties > 0 ? 'text-red-600' : 'text-green'}`}>
                  {formatCurrency(totalPenalties)}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-text-muted font-medium">{t('hisaab.prevAdjustments', 'Previous Adjustments')}</span>
                <span className="font-mono font-bold text-text">{formatCurrency(w.previousAdjustments)}</span>
              </div>
            </div>

            {(() => {
              const paid = w.paidAmount || 0;
              const remainingDue = (w.toCollect !== undefined && w.toCollect !== null)
                ? w.toCollect
                : Math.max(0, (w.currentWeekOs > 0 ? w.currentWeekOs : 0) - paid);
              const isPayout = w.currentWeekOs < 0;

              return (
                <div className="pt-3 border-t border-dashed border-border/80 flex items-center justify-between">
                  <div>
                    <span className="font-sans text-[10px] font-bold text-text-muted uppercase tracking-wider block">
                      {isPayout ? t('hisaab.netPayout', 'NET DRIVER PAYOUT') : t('hisaab.netDue', 'OUTSTANDING DEBT DUE')}
                    </span>
                    <p className="font-sans text-[11px] text-text-muted mt-0.5">
                      {isPayout ? t('home.payoutToDriver', 'LetzRyd payout to driver') : t('home.dueToLetzryd', 'Due to be paid to LetzRyd')} • <strong className="text-text">{w.activeDays} {t('home.daysActive', 'Days Active')}</strong>
                    </p>
                  </div>
                  <div className={`font-mono text-sm font-black ${isPayout ? 'text-green' : remainingDue === 0 ? 'text-green' : 'text-red-600'}`}>
                    {isPayout
                      ? `+₹${Math.abs(w.currentWeekOs).toLocaleString('en-IN', { minimumFractionDigits: Math.abs(w.currentWeekOs) % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}`
                      : remainingDue === 0
                      ? '₹0'
                      : `-₹${remainingDue.toLocaleString('en-IN', { minimumFractionDigits: remainingDue % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}`}
                  </div>
                </div>
              );
            })()}

            {/* Payment Tracking Row — shows live DB paid amount + status */}
            {(w.paidAmount !== undefined || w.paymentStatus) && (
              <div className="pt-2 border-t border-dashed border-border/60 flex items-center justify-between text-[10px]">
                <div className="flex items-center gap-1.5 font-medium text-text-muted">
                  <span>💳 Payment Received:</span>
                  <span className="font-mono font-bold text-text">₹{(w.paidAmount || 0).toLocaleString('en-IN', { minimumFractionDigits: (w.paidAmount || 0) % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}</span>
                </div>
                {w.paymentStatus === 'settled' && (
                  <span className="flex items-center gap-1 font-bold text-green bg-green-light border border-green-200/50 px-2 py-0.5 rounded-full">
                    <CheckCircle2 className="w-3 h-3" /> Settled
                  </span>
                )}
                {w.paymentStatus === 'partial' && (
                  <span className="flex items-center gap-1 font-bold text-amber-600 bg-amber-50 border border-amber-200/50 px-2 py-0.5 rounded-full">
                    <Clock className="w-3 h-3" /> Partial
                  </span>
                )}
                {(!w.paymentStatus || w.paymentStatus === 'unpaid') && w.currentWeekOs > 0 && (
                  <span className="flex items-center gap-1 font-bold text-red-600 bg-red-50 border border-red-200/50 px-2 py-0.5 rounded-full">
                    Unpaid
                  </span>
                )}
              </div>
            )}
          </div>
        );
      })()}

      {/* 3. HISAAB BREAKDOWN ACCORDIONS */}
      <div className="space-y-2.5">
        <p className="font-sans text-[11px] font-bold text-text uppercase tracking-wider px-0.5">
          {t('hisaab.breakdownTitle', 'HISAAB BREAKDOWN')}
        </p>

        {/* RENT & CHARGES CARD */}
        {(() => {
          const othersNet = - (w.rent.netWeeklyRent + w.dailyMaintenance + w.tds + (w.challan || 0) + (w.accident || 0)) + w.previousAdjustments;
          return (
            <div className="bg-surface border border-border/80 rounded-2xl overflow-hidden shadow-xs transition-all">
              <button
                onClick={() => setComputationOpen(!computationOpen)}
                className="w-full px-3.5 py-3 bg-surface flex items-center justify-between cursor-pointer text-left focus:outline-none"
              >
                <div className="flex items-center gap-3">
                  <div className="w-7 h-7 rounded-xl bg-slate-100 text-slate-700 border border-slate-200 flex items-center justify-center shrink-0 shadow-2xs">
                    <ReceiptIndianRupee className="w-4 h-4" />
                  </div>
                  <span className="font-sans text-xs font-bold text-text">{t('hisaab.rentChargesTitle', 'Rent & Charges')}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`font-sans text-xs font-bold ${othersNet >= 0 ? 'text-green' : 'text-red-600'}`}>
                    {formatCurrency(othersNet)}
                  </span>
                  <ChevronDown className={`w-4 h-4 text-text-muted transition-transform duration-200 ${computationOpen ? 'rotate-180' : ''}`} />
                </div>
              </button>

              {computationOpen && (
                <div className="p-3.5 space-y-2.5 border-t border-border/60 font-sans text-xs">
                  <div className="flex justify-between items-center">
                    <span className="text-text-muted font-medium">{t('hisaab.vehicleRent', 'Vehicle Rent')} ({w.activeDays} {t('hisaab.daysAt', 'days @')} ₹{w.rent.dailyRate})</span>
                    <span className="text-red-600 font-bold font-mono">-{formatCurrency(w.rent.netWeeklyRent)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-text-muted font-medium">
                      {t('hisaab.dailyMaintenance', 'Daily Maintenance Charge')} ({w.activeDays} {t('hisaab.daysAt', 'days @')} ₹{Math.round(w.dailyMaintenance / (w.activeDays || 1))})
                    </span>
                    <span className="text-red-600 font-bold font-mono">-{formatCurrency(w.dailyMaintenance)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-text-muted font-medium">{t('hisaab.tds', 'TDS Deduction (1%)')}</span>
                    <span className="text-red-600 font-bold font-mono">-{formatCurrency(w.tds)}</span>
                  </div>
                  {(w.challan || 0) > 0 && (
                    <div className="flex justify-between items-center">
                      <span className="text-text-muted font-medium">{t('hisaab.challanPenalty', 'Traffic Challan & Penalty')}</span>
                      <span className="text-red-600 font-bold font-mono">-{formatCurrency(w.challan)}</span>
                    </div>
                  )}
                  {(w.accident || 0) > 0 && (
                    <div className="flex justify-between items-center">
                      <span className="text-text-muted font-medium">{t('hisaab.accidentCharges', 'Accident Charges')}</span>
                      <span className="text-red-600 font-bold font-mono">-{formatCurrency(w.accident || 0)}</span>
                    </div>
                  )}
                  <div className="flex justify-between items-center">
                    <span className="text-text-muted font-medium">{t('hisaab.prevAdjustments', 'Previous Adjustments')}</span>
                    <span className="text-text font-bold font-mono">{formatCurrency(w.previousAdjustments)}</span>
                  </div>
                </div>
              )}
            </div>
          );
        })()}

        {renderPlatformSection('uber', 'Uber', uberOpen, setUberOpen, 'bg-slate-900 text-white')}
        {renderPlatformSection('ola', 'Ola', olaOpen, setOlaOpen, 'bg-emerald-700 text-white')}
        {renderPlatformSection('rapido', 'Rapido', rapidoOpen, setRapidoOpen, 'bg-amber-600 text-white')}
      </div>

      {/* 4. GPS DEAD-MILES CARD */}
      <div className="bg-surface border border-border/80 rounded-2xl overflow-hidden shadow-xs transition-all">
        <button
          onClick={() => setGpsOpen(!gpsOpen)}
          className="w-full px-3.5 py-3 bg-surface flex items-center justify-between cursor-pointer text-left focus:outline-none"
        >
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-xl bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center justify-center shrink-0 shadow-2xs">
              <MapPin className="w-3.5 h-3.5" />
            </div>
            <span className="font-sans text-xs font-bold text-text">{t('hisaab.gpsDeadMilesTitle', 'GPS Dead Miles')}</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-sans text-xs font-bold text-green">
              {formatCurrency(w.gps.deadKmPenalty)}
            </span>
            <ChevronDown className={`w-4 h-4 text-text-muted transition-transform duration-200 ${gpsOpen ? 'rotate-180' : ''}`} />
          </div>
        </button>

        {gpsOpen && (
          <div className="p-3.5 space-y-2 border-t border-border/60 font-sans text-xs">
            <div className="flex justify-between items-center">
              <span className="text-text-muted">{t('hisaab.totalGpsTracked', 'Total GPS Tracked KM')}</span>
              <span className="font-bold text-text font-mono">{w.gps.totalGpsKm} KM</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-text-muted">{t('hisaab.idealTripKm', 'Ideal Trip KM')}</span>
              <span className="font-bold text-text font-mono">{w.gps.idealGpsKm} KM</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-text-muted">{t('hisaab.excessDeadMiles', 'Excess Dead Miles')}</span>
              <span className="font-bold text-text font-mono">{w.gps.deadMile} KM ({w.gps.deadMilePct}%)</span>
            </div>
            <div className="flex justify-between items-center pt-1 border-t border-border/60">
              <span className="text-text-muted">{t('hisaab.deadMilePenalty', 'Dead Mile Penalty Due')}</span>
              <span className="font-bold text-green font-mono">₹0.00</span>
            </div>
          </div>
        )}
      </div>

      {/* 5. DEDICATED STANDING ACCOUNT BALANCES CARD */}
      <div className="bg-surface border border-border/80 rounded-2xl p-3.5 shadow-xs space-y-3 font-sans">
        <div className="flex justify-between items-center border-b border-border/60 pb-2">
          <span className="font-sans text-[10px] font-bold text-text-muted uppercase tracking-wider">
            {t('hisaab.standingBalancesTitle', 'STANDING ACCOUNT BALANCES')}
          </span>
          <span className="text-[10px] font-semibold text-text-muted font-mono bg-bg px-2 py-0.5 rounded-md border border-border/50">
            {t('hisaab.contractTerms', 'Contract Terms')}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2.5 text-xs">
          <div className="bg-bg border border-border/60 rounded-xl p-3 space-y-1.5 text-left">
            <div className="font-bold text-text text-[11px]">{t('hisaab.depositTitle', 'Security Deposit')}</div>
            <div className="flex justify-between items-center text-[10px] text-text-muted">
              <span>{t('hisaab.agreed', 'Agreed:')}</span>
              <span className="font-bold text-text font-mono">₹6,000</span>
            </div>
            <div className="flex justify-between items-center text-[10px] text-text-muted">
              <span>{t('hisaab.paid', 'Paid:')}</span>
              <span className="font-bold text-green font-mono">₹{(w.paidDeposit ?? 0).toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-between items-center text-[10px]">
              <span className="text-text-muted">{t('hisaab.pending', 'Pending:')}</span>
              <span className={`font-bold font-mono ${(w.pendingDeposit ?? 0) > 0 ? 'text-amber-700 font-extrabold' : 'text-green'}`}>
                ₹{(w.pendingDeposit ?? 0).toLocaleString('en-IN')}
              </span>
            </div>
          </div>

          <div className="bg-bg border border-border/60 rounded-xl p-3 space-y-1.5 text-left">
            <div className="font-bold text-text text-[11px]">{t('hisaab.joiningFeeTitle', 'Joining Fee')}</div>
            <div className="flex justify-between items-center text-[10px] text-text-muted">
              <span>{t('hisaab.agreed', 'Agreed:')}</span>
              <span className="font-bold text-text font-mono">₹1,000</span>
            </div>
            <div className="flex justify-between items-center text-[10px] text-text-muted">
              <span>{t('hisaab.paid', 'Paid:')}</span>
              <span className="font-bold text-green font-mono">₹{(w.joiningFeePaid || 1000).toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-between items-center text-[10px]">
              <span className="text-text-muted">{t('hisaab.pending', 'Pending:')}</span>
              <span className="font-bold text-green font-mono">₹0</span>
            </div>
          </div>
        </div>
      </div>

      {/* 6. DISPUTE NOTICE BANNER */}
      <div className="flex items-center gap-2.5 p-3 rounded-2xl bg-surface border border-border/80 text-left font-sans text-[11px] text-text-muted shadow-2xs">
        <Info className="w-4 h-4 text-primary shrink-0" />
        <p className="leading-tight">
          {t('hisaab.disputeNotice', 'Hisaab disputes can be raised Mon–Thu. Changes after Thursday apply to next week.')}
        </p>
      </div>
    </div>
  );
};

/* =========================================================================
   4. SETTLE SCREEN
   ========================================================================= */
interface SettleScreenProps {
  amount: number;
  hisaabAmount?: number;
  pendingDeposit?: number;
  challansAmount?: number;
  weekRange: string;
  upiId: string;
  driverName?: string;
  driverPhone?: string;
  driverId?: string;
  hisaabId?: number;        // NEW: links payment to specific hisaab in DB
  payerType?: 'driver' | 'operator';  // NEW: driver vs operator payment
  onCopyUpi: () => void;
  onConfirmPayment: (paidAmt?: number) => void;
  onBack: () => void;
  t: (key: string, fallback: string) => string;
  isFleetManaged?: boolean;
  operatorName?: string;
}

export const SettleScreen: React.FC<SettleScreenProps> = ({
  amount,
  hisaabAmount,
  pendingDeposit = 0,
  challansAmount = 0,
  weekRange,
  upiId,
  driverName,
  driverPhone,
  driverId,
  hisaabId,
  payerType = 'driver',
  onCopyUpi,
  onConfirmPayment,
  onBack,
  t,
  isFleetManaged,
  operatorName
}) => {
  const pastWeekAmount = hisaabAmount !== undefined ? hisaabAmount : amount;
  const totalDueAmount = pastWeekAmount + pendingDeposit + challansAmount;

  const [paymentOption, setPaymentOption] = useState<'full' | 'part' | 'advance'>('full');
  const [customAmount, setCustomAmount] = useState<string>(totalDueAmount.toFixed(2));
  const [payLoading, setPayLoading] = useState(false);
  const [payError, setPayError] = useState<string | null>(null);
  
  // Payment Flow States: 'form' | 'loading' | 'checkout' | 'gateway' | 'simulator' | 'success'
  const [paymentState, setPaymentState] = useState<'form' | 'loading' | 'checkout' | 'gateway' | 'simulator' | 'success'>('form');
  const [paymentMethod, setPaymentMethod] = useState<'netbanking' | 'upi' | 'card' | 'wallet' | 'iframe'>('netbanking');
  const [selectedBank, setSelectedBank] = useState<string>('State Bank of India');
  const [selectedWallet, setSelectedWallet] = useState<string>('Paytm');
  const [directGatewayUrl, setDirectGatewayUrl] = useState<string>('');
  const [otpValue, setOtpValue] = useState<string>('111000');
  const [simulationStatus, setSimulationStatus] = useState<'SUCCESS' | 'PENDING' | 'USER_DROPPED' | 'FAILED'>('SUCCESS');
  const [simSubmitting, setSimSubmitting] = useState<boolean>(false);
  const [simError, setSimError] = useState<string | null>(null);

  const [paymentSessionId, setPaymentSessionId] = useState<string>('');
  const [currentOrderId, setCurrentOrderId] = useState<string>('');
  const [countdown, setCountdown] = useState<number>(3);
  const checkoutContainerRef = useRef<HTMLDivElement>(null);

  // Mount Cashfree's official inline checkout to flush session and avoid stale cache
  useEffect(() => {
    if (paymentState === 'checkout' && paymentSessionId && checkoutContainerRef.current) {
      const initCashfreeCheckout = () => {
        if (typeof (window as any).Cashfree === 'function') {
          try {
            const cashfreeMode = (import.meta.env.VITE_CASHFREE_MODE || 'sandbox').toLowerCase();
            const cashfree = (window as any).Cashfree({ mode: cashfreeMode });
            if (checkoutContainerRef.current) {
              checkoutContainerRef.current.innerHTML = '';
              cashfree.checkout({
                paymentSessionId: paymentSessionId,
                redirectTarget: checkoutContainerRef.current,
                appearance: {
                  width: '100%',
                  height: '520px'
                }
              }).then((result: any) => {
                console.log('[Cashfree] checkout result:', result);
                // result.paymentDetails = success, result.error = user dropped / failed
                // Always call verify — backend will determine actual status from Cashfree API
                if (result && result.paymentDetails) {
                  // Definite success signal
                  handleVerifyOrder();
                } else if (result && result.error) {
                  // User dropped or failed — still verify to pick up any partial success
                  console.warn('[Cashfree] Payment error/drop:', result.error);
                  handleVerifyOrder();
                } else if (result) {
                  // Unknown shape — verify anyway
                  handleVerifyOrder();
                }
              }).catch((err: any) => {
                console.warn('Cashfree inline checkout error, falling back to modal:', err);
                try {
                  cashfree.checkout({
                    paymentSessionId: paymentSessionId,
                    redirectTarget: '_modal'
                  }).then((r: any) => {
                    if (r) handleVerifyOrder();
                  }).catch(() => {});
                } catch (modalErr) {
                  console.error('Cashfree modal checkout error:', modalErr);
                }
              });
            }
            return true;
          } catch (e) {
            console.warn('Cashfree checkout initialization failed:', e);
            return false;
          }
        }
        return false;
      };

      if (!initCashfreeCheckout()) {
        const interval = setInterval(() => {
          if (initCashfreeCheckout()) {
            clearInterval(interval);
          }
        }, 250);
        return () => clearInterval(interval);
      }
    }
  }, [paymentState, paymentSessionId]);


  // Card input states
  const [cardNumber, setCardNumber] = useState('4111 2222 3333 4444');
  const [cardExpiry, setCardExpiry] = useState('12/28');
  const [cardCvv, setCardCvv] = useState('123');
  const [cardHolder, setCardHolder] = useState(driverName || 'Driver');

  const selectPaymentOption = (opt: 'full' | 'part' | 'advance') => {
    setPaymentOption(opt);
    if (opt === 'full') {
      setCustomAmount(totalDueAmount.toFixed(2));
    } else if (opt === 'part') {
      const half = Math.max(100, Math.floor(totalDueAmount / 2));
      setCustomAmount(half.toFixed(2));
    } else if (opt === 'advance') {
      const adv = Math.max(3000, Math.ceil((totalDueAmount + 500) / 500) * 500);
      setCustomAmount(adv.toFixed(2));
    }
  };

  const activePayAmount = parseFloat(customAmount) || 0;
  const isAdvanceInvalid = paymentOption === 'advance' && activePayAmount <= totalDueAmount;
  const isPartInvalid = paymentOption === 'part' && (activePayAmount <= 0 || activePayAmount >= totalDueAmount);

  // Trigger Real Cashfree Order Creation and render checkout inside mobile layout
  const handleCashfreePayment = async () => {
    setPaymentSessionId('');
    setCurrentOrderId('');
    setPayLoading(true);
    setPayError(null);
    setPaymentState('loading');

    const generatedOrderId = `ORDER_LR_${Date.now()}`;

    try {
      const orderPayload = {
        amount: activePayAmount.toFixed(2),
        driverName: driverName || 'Driver Partner',
        driverPhone: driverPhone || '9999999999',
        driverId: driverId || '1',
        weekRange,
        app_hisaab_id: hisaabId || null,   // Link to specific hisaab
        payer_type: payerType || 'driver',  // driver or operator
        return_url: typeof window !== 'undefined' ? `${window.location.origin}/?order_id={order_id}` : undefined,
      };

      // Call backend endpoint with automatic fallback across relative & direct host paths
      const endpointsToTry = [
        `${BACKEND_URL}/api/create-order`,
        '/api/create-order',
        'http://127.0.0.1:8000/api/create-order',
        'http://localhost:8000/api/create-order',
        `${BACKEND_URL}/api/payments/create-order`,
        '/api/payments/create-order',
      ].filter(Boolean);

      let res: Response | null = null;
      let lastNetworkError: any = null;

      for (const endpoint of endpointsToTry) {
        try {
          const attempt = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderPayload)
          });
          if (attempt.ok) {
            res = attempt;
            break;
          } else if (attempt.status !== 404 && attempt.status !== 405) {
            res = attempt;
            break;
          }
        } catch (e) {
          lastNetworkError = e;
        }
      }

      if (!res) {
        throw new Error(lastNetworkError?.message || 'Could not connect to payment backend.');
      }

      if (!res.ok) {
        const errText = await res.text();
        let errorDetail = `Payment server error (${res.status})`;
        try {
          const parsed = JSON.parse(errText);
          errorDetail = parsed?.detail || parsed?.error || errorDetail;
        } catch {}
        throw new Error(errorDetail);
      }

      const sessionData = await res.json();

      if (sessionData && (sessionData.payment_session_id || sessionData.paymentSessionId)) {
        const sessionId = sessionData.payment_session_id || sessionData.paymentSessionId;
        const ordId = sessionData.order_id || sessionData.orderId || generatedOrderId;
        setPaymentSessionId(sessionId);
        setCurrentOrderId(ordId);
        // Keep 100% inside mobile layout
        setPaymentState('checkout');
      } else if (sessionData && sessionData.error) {
        throw new Error(sessionData.error);
      } else {
        throw new Error('Could not create Cashfree session. Please verify backend credentials.');
      }
    } catch (err: any) {
      setPayError(err?.message || t('settle.apiError', 'Could not connect to payment server.'));
      setPaymentState('form');
    } finally {
      setPayLoading(false);
    }
  };

  const handlePaymentSuccess = () => {
    setPaymentState('success');
    setCountdown(3);
  };

  const handleReturnToSettle = () => {
    setPaymentState('form');
    setPaymentSessionId('');
    setCurrentOrderId('');
    onConfirmPayment(activePayAmount);
  };

  // Verify real order with backend (Only triggers success if truly verified by Cashfree)
  const handleVerifyOrder = async (targetOrderId?: string) => {
    const checkId = targetOrderId || currentOrderId;
    if (!checkId) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/payments/verify/${checkId}`);
      if (!res.ok) return;
      const data = await res.json();
      if (data?.is_success || data?.status === 'SUCCESS') {
        const verifiedAmount = data?.amount || data?.paid_amount || activePayAmount;
        onConfirmPayment(verifiedAmount);
        handlePaymentSuccess();
      }
    } catch (e) {
      console.warn('Verification check:', e);
    }
  };

  // Listen for official Cashfree payment completion messages
  useEffect(() => {
    const handleCashfreeMessage = (event: MessageEvent) => {
      try {
        if (event.origin && event.origin.includes('cashfree.com')) {
          if (
            event.data?.status === 'SUCCESS' ||
            event.data?.txStatus === 'SUCCESS' ||
            event.data?.type === 'CASHFREE_PAYMENT_SUCCESS' ||
            event.data?.paymentDetails?.paymentStatus === 'SUCCESS'
          ) {
            handleVerifyOrder();
          }
        }
      } catch (e) {}
    };

    window.addEventListener('message', handleCashfreeMessage);
    return () => window.removeEventListener('message', handleCashfreeMessage);
  }, [currentOrderId]);

  // Automatic countdown redirection on success back to Settle screen
  useEffect(() => {
    if (paymentState === 'success') {
      if (countdown > 0) {
        const timer = setTimeout(() => setCountdown(prev => prev - 1), 1000);
        return () => clearTimeout(timer);
      } else {
        handleReturnToSettle();
      }
    }
  }, [paymentState, countdown]);

  /* =========================================================================
     VIEW 1: PAYMENT SUCCESS SCREEN (Inside phone layout)
     ========================================================================= */
  if (paymentState === 'success') {
    return (
      <div className="space-y-4 text-left font-sans animate-in fade-in zoom-in-95 duration-300">
        <div className="bg-surface border border-emerald-200/80 rounded-3xl p-5 shadow-lg text-center space-y-4">
          <div className="relative mx-auto w-16 h-16 flex items-center justify-center">
            <div className="absolute inset-0 rounded-full bg-emerald-100 animate-ping opacity-50" />
            <div className="w-16 h-16 rounded-full bg-emerald-500 flex items-center justify-center text-white shadow-md relative z-10">
              <CheckCircle2 className="w-9 h-9" />
            </div>
          </div>

          <div>
            <span className="text-[10px] font-extrabold tracking-wider uppercase text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full">
              Cashfree Verified
            </span>
            <h2 className="font-sans text-xl font-black text-text mt-2">
              Payment Successful!
            </h2>
            <p className="font-sans text-xs text-text-muted mt-1">
              Your weekly hisaab dues have been cleared successfully.
            </p>
          </div>

          {/* Receipt Breakdown Card */}
          <div className="bg-bg/80 border border-border/80 rounded-2xl p-3.5 text-left space-y-2.5 text-xs">
            <div className="flex justify-between items-center pb-2 border-b border-border/60">
              <span className="text-text-muted font-medium">Amount Paid:</span>
              <span className="font-sans text-base font-black text-emerald-600">
                ₹{activePayAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="flex justify-between items-center text-[11px]">
              <span className="text-text-muted">Order ID:</span>
              <span className="font-mono font-bold text-text truncate max-w-[170px]">
                {currentOrderId}
              </span>
            </div>
            <div className="flex justify-between items-center text-[11px]">
              <span className="text-text-muted">Payment Mode:</span>
              <span className="font-bold text-text">Cashfree PG Real Gateway</span>
            </div>
            <div className="flex justify-between items-center text-[11px]">
              <span className="text-text-muted">Period:</span>
              <span className="font-medium text-text">{weekRange}</span>
            </div>
            <div className="flex justify-between items-center text-[11px]">
              <span className="text-text-muted">Status:</span>
              <span className="font-bold text-emerald-600 flex items-center gap-1">
                <Check className="w-3.5 h-3.5" /> SUCCESS (VERIFIED)
              </span>
            </div>
          </div>

          {/* Countdown & Instant Return to Settle Button */}
          <div className="space-y-2 pt-1">
            <div className="flex items-center justify-center gap-2 text-xs font-semibold text-text-muted">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
              <span>Redirecting to Settle in <strong className="text-primary">{countdown}s</strong>...</span>
            </div>

            <button
              onClick={handleReturnToSettle}
              className="w-full h-11 rounded-xl bg-primary hover:bg-primary-hover text-white font-sans text-xs font-extrabold flex items-center justify-center gap-2 cursor-pointer shadow-sm hover:shadow transition-all active:scale-[0.99] uppercase tracking-wide"
            >
              <span>Back to Settle Page</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  /* =========================================================================
     VIEW 2: OFFICIAL CASHFREE HOSTED CHECKOUT (Inside mobile layout)
     ========================================================================= */
  if (paymentState === 'checkout') {
    return (
      <div className="flex flex-col h-full space-y-2.5 text-left font-sans animate-in fade-in duration-200">
        {/* Checkout Header Bar inside Phone Frame */}
        <div className="flex items-center justify-between pb-2 border-b border-border/70 shrink-0">
          <button
            onClick={() => {
              setPaymentSessionId('');
              setCurrentOrderId('');
              setPaymentState('form');
            }}
            className="flex items-center gap-1.5 text-xs font-bold text-text-muted hover:text-text cursor-pointer py-1 px-2.5 rounded-lg bg-surface border border-border/60 hover:border-border transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Cancel</span>
          </button>

          <div className="flex items-center gap-1.5 text-xs font-bold text-text">
            <Lock className="w-3.5 h-3.5 text-emerald-600" />
            <span>Cashfree Gateway</span>
          </div>

          <span className="font-mono text-xs font-black text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded-md">
            ₹{activePayAmount.toLocaleString('en-IN', { minimumFractionDigits: activePayAmount % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}
          </span>
        </div>

        {/* Official Cashfree Hosted Checkout Inline Mount Container */}
        <div
          ref={checkoutContainerRef}
          id="cashfree-checkout-container"
          className="flex-1 w-full bg-slate-50 border border-border/80 rounded-2xl overflow-hidden relative min-h-[520px] flex flex-col shadow-inner items-center justify-center"
        >
          <div className="flex flex-col items-center justify-center space-y-2 p-6 text-center">
            <Loader2 className="w-6 h-6 animate-spin text-primary" />
            <span className="text-xs font-semibold text-text-muted">Loading Cashfree checkout for ₹{activePayAmount.toLocaleString('en-IN', { minimumFractionDigits: activePayAmount % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}...</span>
          </div>
        </div>

        {/* Sandbox Test Credentials Reference Strip */}
        <div className="bg-surface border border-border/80 rounded-xl p-2 text-[10px] space-y-1">
          <div className="flex justify-between items-center text-text-muted font-bold uppercase tracking-wider">
            <span>Sandbox Test Details:</span>
            <span className="text-emerald-700 font-extrabold">OTP: 111000</span>
          </div>
          <div className="grid grid-cols-2 gap-1 text-[9.5px] text-text-muted">
            <div>• <strong>Card:</strong> 4706 1312 1121 2123</div>
            <div>• <strong>UPI:</strong> testsuccess@gocash</div>
            <div>• <strong>Exp / CVV:</strong> 03/28 • 123</div>
            <div>• <strong>NetBank:</strong> TEST Bank</div>
          </div>
        </div>

        {/* Confirmation Action */}
        <div className="flex items-center justify-between gap-2 px-1">
          <span className="text-[10px] text-text-muted flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-emerald-600" /> Cashfree Sandbox Active
          </span>
          <button
            onClick={() => handleVerifyOrder()}
            className="text-[10.5px] font-bold text-emerald-700 hover:text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-300 px-3 py-1.5 rounded-lg cursor-pointer transition-all flex items-center gap-1.5 shadow-xs"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Verify Payment Status</span>
          </button>
        </div>
      </div>
    );
  }

  /* =========================================================================
     VIEW 3: LOADING GATEWAY SESSION
     ========================================================================= */
  if (paymentState === 'loading') {
    return (
      <div className="space-y-4 text-left font-sans">
        <div className="flex items-center gap-3 border-b border-border/60 pb-2.5">
          <button
            onClick={() => setPaymentState('form')}
            className="w-9 h-9 rounded-xl border border-border bg-surface flex items-center justify-center text-text-muted hover:text-text cursor-pointer transition-colors shrink-0"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <div className="flex-1 min-w-0">
            <h2 className="font-sans text-base font-extrabold text-text">Connecting Cashfree</h2>
            <p className="font-sans text-xs text-text-muted truncate">Setting up payment gateway...</p>
          </div>
        </div>

        <div className="bg-surface border border-border/80 rounded-2xl p-8 shadow-xs flex flex-col items-center justify-center text-center space-y-3 min-h-[300px]">
          <div className="w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
            <Loader2 className="w-7 h-7 animate-spin" />
          </div>
          <h3 className="font-sans text-sm font-extrabold text-text">
            Initializing Secure Checkout
          </h3>
          <p className="font-sans text-xs text-text-muted max-w-[220px]">
            Creating Cashfree order for ₹{activePayAmount.toLocaleString('en-IN', { minimumFractionDigits: activePayAmount % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}...
          </p>
        </div>
      </div>
    );
  }

  /* =========================================================================
     VIEW 4: DEFAULT SETTLE WEEKLY HISAAB FORM (1st Image)
     ========================================================================= */
  return (
    <div className="space-y-4 text-left font-sans animate-in fade-in duration-200">
      <div className="flex items-center gap-3 border-b border-border/60 pb-2.5">
        {onBack && (
          <button
            onClick={onBack}
            className="w-9 h-9 rounded-xl border border-border bg-surface flex items-center justify-center text-text-muted hover:text-text cursor-pointer transition-colors shrink-0"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        )}
        <div className="flex-1 min-w-0">
          <h2 className="font-sans text-base font-extrabold text-text">
            {t('settle.title', 'Settle Weekly Dues')}
          </h2>
          <p className="font-sans text-xs text-text-muted truncate">
            {t('settle.forWeek', 'Period:')} {weekRange ? weekRange.replace(' to ', ` ${t('settle.toDate', 'to')} `) : ''}
          </p>
        </div>
        <span className="text-[10px] font-bold text-primary bg-primary/10 px-2.5 py-1 rounded-full shrink-0">
          {t('settle.instantPay', 'Instant Pay')}
        </span>
      </div>

      <div className="bg-surface border border-border/80 rounded-2xl p-3.5 shadow-xs space-y-3.5 text-left font-sans text-xs">
        <div className="bg-bg/60 p-3 rounded-xl border border-border/60 flex items-center justify-between">
          <span className="font-sans text-xs font-bold text-text-muted uppercase tracking-wider">
            {t('home.totalOutstandingDue', 'Total Outstanding Due')}
          </span>
          <span className="font-sans text-xl font-black text-red-600">
            ₹{totalDueAmount.toLocaleString('en-IN', {
              minimumFractionDigits: totalDueAmount % 1 !== 0 ? 2 : 0,
              maximumFractionDigits: 2,
            })}
          </span>
        </div>

        <div className="space-y-1.5 px-1 font-sans text-xs border-b border-border/60 pb-3">
          <div className="flex justify-between items-center text-text">
            <span className="text-text-muted font-medium">{t('settle.weeklyHisaabDue', 'Weekly Hisaab Due:')}</span>
            <span className="font-bold text-text">
              ₹{pastWeekAmount.toLocaleString('en-IN', {
                minimumFractionDigits: pastWeekAmount % 1 !== 0 ? 2 : 0,
                maximumFractionDigits: 2,
              })}
            </span>
          </div>
          {challansAmount > 0 && (
            <div className="flex justify-between items-center text-text">
              <span className="text-text-muted font-medium">{t('settle.challansAndPenalties', 'Challans & Penalties:')}</span>
              <span className="font-bold text-red-600">
                ₹{challansAmount.toLocaleString('en-IN', {
                  minimumFractionDigits: challansAmount % 1 !== 0 ? 2 : 0,
                  maximumFractionDigits: 2,
                })}
              </span>
            </div>
          )}
          {pendingDeposit > 0 && (
            <div className="flex justify-between items-center text-text">
              <span className="text-text-muted font-medium">{t('hisaab.pendingDeposit', 'Pending Deposit')}:</span>
              <span className="font-bold text-amber-700">
                ₹{pendingDeposit.toLocaleString('en-IN', {
                  minimumFractionDigits: pendingDeposit % 1 !== 0 ? 2 : 0,
                  maximumFractionDigits: 2,
                })}
              </span>
            </div>
          )}
        </div>

        <div className="space-y-2.5">
          <label className="font-sans text-[11px] font-bold text-text-muted uppercase tracking-wider block">
            {t('settle.selectOption', 'SELECT PAYMENT OPTION')}
          </label>

          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => !isFleetManaged && selectPaymentOption('full')}
              disabled={isFleetManaged}
              className={`h-11 rounded-xl border text-xs font-bold transition-all flex items-center justify-center ${
                isFleetManaged
                  ? 'bg-bg border-border text-text-dim opacity-50 cursor-not-allowed'
                  : paymentOption === 'full'
                  ? 'bg-primary/10 border-primary text-primary shadow-xs cursor-pointer'
                  : 'bg-bg border-border text-text-muted hover:text-text cursor-pointer'
              }`}
            >
              {t('settle.full', 'Full')}
            </button>
            <button
              onClick={() => !isFleetManaged && selectPaymentOption('part')}
              disabled={isFleetManaged}
              className={`h-11 rounded-xl border text-xs font-bold transition-all flex items-center justify-center ${
                isFleetManaged
                  ? 'bg-bg border-border text-text-dim opacity-50 cursor-not-allowed'
                  : paymentOption === 'part'
                  ? 'bg-primary/10 border-primary text-primary shadow-xs cursor-pointer'
                  : 'bg-bg border-border text-text-muted hover:text-text cursor-pointer'
              }`}
            >
              {t('settle.partPay', 'Part Pay')}
            </button>
            <button
              onClick={() => !isFleetManaged && selectPaymentOption('advance')}
              disabled={isFleetManaged}
              className={`h-11 rounded-xl border text-xs font-bold transition-all flex items-center justify-center ${
                isFleetManaged
                  ? 'bg-bg border-border text-text-dim opacity-50 cursor-not-allowed'
                  : paymentOption === 'advance'
                  ? 'bg-primary/10 border-primary text-primary shadow-xs cursor-pointer'
                  : 'bg-bg border-border text-text-muted hover:text-text cursor-pointer'
              }`}
            >
              {t('settle.advance', 'Advance')}
            </button>
          </div>

          <div className="pt-2 bg-primary/5 p-2.5 rounded-xl border border-primary/25 text-center space-y-1">
            <label className="font-sans text-[11px] font-extrabold text-primary uppercase tracking-wider block">
              {t('settle.amountToPay', 'AMOUNT TO PAY (₹)')}
            </label>
            <input
              type="number"
              value={customAmount}
              disabled={isFleetManaged || paymentOption === 'full'}
              readOnly={paymentOption === 'full'}
              onChange={(e) => setCustomAmount(e.target.value)}
              className={`h-10 w-full rounded-lg border px-3 font-mono text-xl font-extrabold text-center outline-none transition-colors shadow-2xs ${
                isFleetManaged
                  ? 'bg-gray-100 border-border text-text-dim cursor-not-allowed opacity-60'
                  : paymentOption === 'full'
                  ? 'bg-white/80 border-primary/30 cursor-not-allowed text-primary'
                  : isAdvanceInvalid || isPartInvalid
                  ? 'bg-red-50/50 border-red-300 focus:border-red-500 text-red-600'
                  : 'bg-white border-primary/50 focus:border-2 focus:border-primary text-primary'
              }`}
            />
          </div>

          {paymentOption === 'advance' && isAdvanceInvalid && !isFleetManaged && (
            <p className="text-[11px] text-red-600 font-semibold bg-red-50 border border-red-200 rounded-lg px-3 py-1.5 mt-1">
              ⚠️ {t('settle.advanceError', 'Advance payment must be greater than total due')} (₹{totalDueAmount.toLocaleString('en-IN', { minimumFractionDigits: totalDueAmount % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}).
            </p>
          )}

          {paymentOption === 'part' && isPartInvalid && !isFleetManaged && (
            <p className="text-[11px] text-red-600 font-semibold bg-red-50 border border-red-200 rounded-lg px-3 py-1.5 mt-1">
              {activePayAmount <= 0
                ? '⚠️ Part payment amount must be greater than ₹0.'
                : `⚠️ ${t('settle.partError', 'Part payment must be less than total due')} (₹${totalDueAmount.toLocaleString('en-IN', { minimumFractionDigits: totalDueAmount % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}). ${t('settle.useFullPay', 'Use Full Pay for full settlement.')}`}
            </p>
          )}

          {/* Payment Method Selection */}
          {!isFleetManaged && (
            <div className="space-y-1.5 pt-1">
              <label className="font-sans text-[11px] font-bold text-text-muted uppercase tracking-wider block">
                {t('settle.paymentMethod', 'PAYMENT METHOD')}
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setPaymentMethod('upi')}
                  className={`p-2.5 rounded-xl border text-left flex items-center gap-2.5 transition-all cursor-pointer ${
                    paymentMethod === 'upi'
                      ? 'bg-primary/10 border-primary shadow-2xs'
                      : 'bg-surface border-border hover:border-primary/40'
                  }`}
                >
                  <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
                    <Smartphone className="w-4 h-4" />
                  </div>
                  <div className="min-w-0">
                    <div className="font-sans text-[11px] font-bold text-text">{t('settle.upiApp', 'UPI App / QR')}</div>
                    <div className="text-[9.5px] text-text-muted truncate">{t('settle.upiSub', 'GPay, PhonePe, Paytm')}</div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setPaymentMethod('card')}
                  className={`p-2.5 rounded-xl border text-left flex items-center gap-2.5 transition-all cursor-pointer ${
                    paymentMethod === 'card'
                      ? 'bg-primary/10 border-primary shadow-2xs'
                      : 'bg-surface border-border hover:border-primary/40'
                  }`}
                >
                  <div className="w-7 h-7 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                    <CreditCard className="w-4 h-4" />
                  </div>
                  <div className="min-w-0">
                    <div className="font-sans text-[11px] font-bold text-text">{t('settle.cards', 'Cards')}</div>
                    <div className="text-[9.5px] text-text-muted truncate">{t('settle.cardsSub', 'Debit / Credit Card')}</div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setPaymentMethod('netbanking')}
                  className={`p-2.5 rounded-xl border text-left flex items-center gap-2.5 transition-all cursor-pointer ${
                    paymentMethod === 'netbanking'
                      ? 'bg-primary/10 border-primary shadow-2xs'
                      : 'bg-surface border-border hover:border-primary/40'
                  }`}
                >
                  <div className="w-7 h-7 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center shrink-0">
                    <Landmark className="w-4 h-4" />
                  </div>
                  <div className="min-w-0">
                    <div className="font-sans text-[11px] font-bold text-text">{t('settle.netBanking', 'NetBanking')}</div>
                    <div className="text-[9.5px] text-text-muted truncate">{t('settle.netBankingSub', 'All Indian Banks')}</div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setPaymentMethod('iframe')}
                  className={`p-2.5 rounded-xl border text-left flex items-center gap-2.5 transition-all cursor-pointer ${
                    paymentMethod === 'iframe'
                      ? 'bg-primary/10 border-primary shadow-2xs'
                      : 'bg-surface border-border hover:border-primary/40'
                  }`}
                >
                  <div className="w-7 h-7 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <div className="min-w-0">
                    <div className="font-sans text-[11px] font-bold text-text">{t('settle.cashfreePg', 'Cashfree PG')}</div>
                    <div className="text-[9.5px] text-text-muted truncate">{t('settle.cashfreePgSub', 'Instant Gateway')}</div>
                  </div>
                </button>
              </div>
            </div>
          )}

          {payError && (
            <p className="text-xs text-red-600 font-semibold bg-red-50 border border-red-200 rounded-lg px-3 py-2">{payError}</p>
          )}

          {isFleetManaged ? (
            <div className="mt-3 p-3.5 bg-amber-500/10 border border-amber-500/20 rounded-xl text-center space-y-1.5 font-sans">
              <div className="flex items-center justify-center gap-1.5 text-xs font-bold text-amber-700">
                <ShieldCheck className="w-4 h-4 text-amber-600" />
                <span>Payments handled by Fleet Operator</span>
              </div>
              <p className="text-[11px] text-text-muted leading-relaxed">
                Vehicle managed by Operator <strong className="text-text">{operatorName || 'Fleet Operator'}</strong>.<br />
                Settlements and payments are handled by your fleet manager. Individual payments are disabled for this account.
              </p>
            </div>
          ) : (
            <button
              onClick={handleCashfreePayment}
              disabled={payLoading || activePayAmount <= 0 || isAdvanceInvalid || isPartInvalid}
              className="w-full h-11 rounded-xl bg-primary hover:bg-primary-hover text-white font-sans text-xs font-extrabold flex items-center justify-center gap-2 cursor-pointer shadow-sm hover:shadow transition-all active:scale-[0.99] disabled:opacity-50 mt-2.5 uppercase tracking-wide"
            >
              {payLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                  {t('settle.connectingGateway', 'Connecting Gateway...')}
                </>
              ) : (
                <>
                  <CreditCard className="w-4 h-4" />
                  {t('settle.payBtn', 'Pay Now')} (₹{activePayAmount.toLocaleString('en-IN', { minimumFractionDigits: activePayAmount % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })})
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

/* =========================================================================
   5. SUPPORT SCREEN
   ========================================================================= */
interface SupportScreenProps {
  user: UserType;
  tickets: Ticket[];
  hotline?: string;
  loginType?: 'driver' | 'operator';
  onNewTicket: () => void;
  onSelectTicket: (ticket: Ticket) => void;
  onOpenSos?: () => void;
  t: (key: string, fallback: string) => string;
}

export const SupportScreen: React.FC<SupportScreenProps> = ({
  user,
  tickets,
  hotline,
  loginType,
  onNewTicket,
  onSelectTicket,
  onOpenSos,
  t
}) => {
  const isOperator = loginType === 'operator' || user.operatorType === 'Fleet Owner' || Boolean(user.app_operator_id);
  const [ticketFilter, setTicketFilter] = useState<'open' | 'resolved' | 'all'>('open');
  const [expandedTicketId, setExpandedTicketId] = useState<string | null>(null);

  const openTicketsCount = tickets.filter(t => t.status === 'open').length;
  const resolvedTicketsCount = tickets.filter(t => t.status === 'resolved' || t.status === 'closed').length;

  const filteredTickets = tickets.filter(t => {
    if (ticketFilter === 'open') return t.status === 'open';
    if (ticketFilter === 'resolved') return t.status === 'resolved' || t.status === 'closed';
    return true;
  });

  const managerName = user.assignedManagerName && user.assignedManagerName !== 'Ramesh Naik'
    ? user.assignedManagerName
    : 'LetzRyd Operations Desk';
  const managerInitials = managerName
    .split(' ')
    .filter(Boolean)
    .map((n: string) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() || 'LR';

  const rawPhone = (user.assignedManagerPhone || '').trim();
  const isPhoneLandline = isLandline(rawPhone);
  const hasPhone = Boolean(rawPhone && rawPhone !== '9876543299');

  // Display phone: if landline, show cleanly; if mobile, show +91; if missing, show official mobile helpline
  const displayPhoneText = hasPhone 
    ? (isPhoneLandline ? rawPhone : `+91 ${rawPhone.replace(/\D/g, '').slice(-10)}`)
    : `+91 ${OFFICIAL_MOBILE_HELPLINE}`;

  // Call Link: If valid number, dial it; if missing, dial helpline
  const callPhoneHref = hasPhone 
    ? (isPhoneLandline ? `tel:${rawPhone.replace(/[^0-9+]/g, '')}` : `tel:+91${rawPhone.replace(/\D/g, '').slice(-10)}`)
    : `tel:+91${OFFICIAL_MOBILE_HELPLINE}`;

  // WhatsApp Link: Must ALWAYS be a valid mobile number (never a landline or missing)
  const whatsAppMobile = hasPhone && !isPhoneLandline
    ? getCleanMobileForWhatsApp(rawPhone)
    : OFFICIAL_MOBILE_HELPLINE;

  const formatIndianDate = (dateStr: string) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    const day = String(d.getDate()).padStart(2, '0');
    const month = d.toLocaleString('en-IN', { month: 'short' });
    const year = d.getFullYear();
    return `${day}-${month}-${year}`;
  };

  const getStatusBadge = (status: 'open' | 'resolved' | 'closed') => {
    switch (status) {
      case 'open':
        return (
          <span className="bg-red-50 text-red-700 border border-red-200 text-[10px] font-bold px-2 py-0.5 rounded flex items-center gap-1 shrink-0">
            <Clock className="w-3 h-3" />
            {t('support.open', 'Open')}
          </span>
        );
      case 'resolved':
      case 'closed':
        return (
          <span className="bg-gray-100 text-gray-600 border border-gray-200 text-[10px] font-semibold px-2 py-0.5 rounded flex items-center gap-1 shrink-0">
            <CheckCircle2 className="w-3 h-3 text-gray-500" />
            {t('support.resolved', 'Closed')}
          </span>
        );
      default:
        return null;
    }
  };

  const getPriorityBadge = (priority?: string) => {
    const p = (priority || 'medium').toLowerCase();
    if (p === 'high') {
      return <span className="bg-red-100 text-red-700 text-[9px] font-bold px-1.5 py-0.5 rounded">High Priority</span>;
    } else if (p === 'low') {
      return <span className="bg-blue-100 text-blue-700 text-[9px] font-bold px-1.5 py-0.5 rounded">Low Priority</span>;
    }
    return <span className="bg-amber-100 text-amber-700 text-[9px] font-bold px-1.5 py-0.5 rounded">Medium Priority</span>;
  };

  return (
    <div className="space-y-4 text-left font-sans">
      <div>
        <h2 className="font-sans text-base font-bold text-text">
          {t('support.title', 'Support Desk')}
        </h2>
        <p className="font-sans text-xs text-text-muted mt-0.5">
          {t('support.subtitle', 'Contact manager or raise tickets')}
        </p>
      </div>

      <div className="bg-surface border border-primary/25 rounded-2xl p-3.5 shadow-xs space-y-3 font-sans">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary text-white font-extrabold text-sm flex items-center justify-center shrink-0 shadow-2xs">
            {managerInitials}
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-sans text-[10px] font-extrabold text-primary uppercase tracking-wider">
              {isOperator ? t('support.accountManager', 'ASSIGNED ACCOUNT MANAGER') : t('support.manager', 'ASSIGNED DRIVER MANAGER')}
            </p>
            <h4 className="font-sans text-sm font-bold text-text truncate mt-0.5">{managerName}</h4>
            <p className="font-sans text-xs text-text-muted mt-0.5">{displayPhoneText}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 pt-0.5">
          <a
            href={callPhoneHref}
            className="flex-1 h-9 rounded-xl bg-green hover:bg-green/90 text-white font-sans text-xs font-bold flex items-center justify-center gap-1.5 shadow-2xs cursor-pointer transition-all active:scale-98"
          >
            <PhoneCall className="w-3.5 h-3.5" />
            <span>{isOperator ? t('support.callAccountManager', 'Call Account Manager') : t('support.callManager', 'Call Manager')}</span>
          </a>
          <a
            href={`https://wa.me/91${whatsAppMobile}`}
            target="_blank"
            rel="noreferrer"
            className="h-9 px-3.5 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 font-sans text-xs font-bold flex items-center justify-center gap-1.5 cursor-pointer transition-all active:scale-98 shrink-0"
          >
            <MessageSquare className="w-3.5 h-3.5 text-emerald-600" />
            <span>{t('support.whatsapp', 'WhatsApp')}</span>
          </a>
        </div>
      </div>

      <button
        onClick={onNewTicket}
        className="w-full h-10 rounded-xl bg-primary hover:bg-primary-hover text-white font-sans text-xs font-bold flex items-center justify-center gap-2 shadow-2xs transition-all cursor-pointer active:scale-98"
      >
        <Plus className="w-4 h-4" />
        <span>{t('support.newTicket', 'Raise New Ticket')}</span>
      </button>

      <div className="bg-surface border border-border/80 rounded-2xl p-3.5 shadow-xs text-left font-sans text-xs space-y-3">
        <div className="flex items-center justify-between border-b border-border/60 pb-2.5">
          <h3 className="font-sans text-xs font-bold text-text uppercase tracking-wider">
            {t('support.ticketsTitle', 'SUPPORT TICKETS')}
          </h3>

          <select
            value={ticketFilter}
            onChange={(e) => setTicketFilter(e.target.value as 'open' | 'resolved' | 'all')}
            className="h-8 rounded-lg border border-border bg-bg px-2 font-bold text-text text-xs outline-none focus:border-primary cursor-pointer shadow-2xs shrink-0"
          >
            <option value="open">{t('support.activeTickets', 'Active Tickets')}</option>
            <option value="resolved">{t('support.closedTickets', 'Closed Tickets')}</option>
            <option value="all">{t('support.allTickets', 'All Tickets')}</option>
          </select>
        </div>

        <div>
          {filteredTickets.length === 0 ? (
            <div className="py-6 text-center text-text-muted flex flex-col items-center justify-center space-y-2">
              <TicketIcon className="w-8 h-8 opacity-30" />
              <p className="font-sans text-xs font-semibold">
                {ticketFilter === 'open'
                  ? t('support.noActiveTickets', 'No active open tickets')
                  : ticketFilter === 'resolved'
                  ? t('support.noClosedTickets', 'No closed tickets in history')
                  : t('support.noTicketsLogged', 'No support tickets logged')}
              </p>
              {ticketFilter === 'open' && resolvedTicketsCount > 0 && (
                <button
                  onClick={() => setTicketFilter('resolved')}
                  className="text-primary font-bold hover:underline text-xs cursor-pointer"
                >
                  {t('support.viewClosedTickets', 'View Closed Tickets')} ({resolvedTicketsCount}) →
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-2.5">
              {filteredTickets.map((ticket) => {
                const isClosed = ticket.status === 'resolved' || ticket.status === 'closed';
                const isExpanded = expandedTicketId === ticket.id;
                return (
                  <div
                    key={ticket.id}
                    className={`rounded-xl border flex flex-col transition-all overflow-hidden ${
                      isClosed
                        ? 'opacity-80 bg-gray-50/50 border-border/60'
                        : 'bg-surface border-border/80 shadow-2xs hover:border-primary/50'
                    }`}
                  >
                    {/* Accordion Header Row */}
                    <div
                      onClick={() => setExpandedTicketId(isExpanded ? null : ticket.id)}
                      className="p-3 cursor-pointer flex flex-col gap-1.5"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-1.5 min-w-0 text-[11px]">
                          <span className={`font-sans font-bold ${isClosed ? 'text-gray-600' : 'text-primary'}`}>
                            {t('ticketCategory.' + ticket.category, ticket.category)}
                          </span>
                          <span className="text-text-muted">•</span>
                          <span className="font-mono font-semibold text-text-muted">
                            {ticket.id}
                          </span>
                        </div>

                        <div className="flex items-center gap-1.5 shrink-0">
                          {getStatusBadge(ticket.status)}
                          <ChevronDown
                            className={`w-3.5 h-3.5 text-text-muted transition-transform duration-200 ${
                              isExpanded ? 'rotate-180' : ''
                            }`}
                          />
                        </div>
                      </div>

                      <h4 className={`font-sans text-xs leading-relaxed ${
                        isClosed ? 'text-gray-500 font-medium' : 'text-text font-bold'
                      }`}>
                        {ticket.subject}
                      </h4>

                      <div className="flex items-center justify-between border-t border-border/40 pt-1.5 mt-0.5">
                        {getPriorityBadge(ticket.priority)}
                        <span className="font-sans text-[10px] font-medium text-text-muted">
                          {formatIndianDate(ticket.date)}
                        </span>
                      </div>
                    </div>

                    {/* Accordion Body Content */}
                    {isExpanded && (
                      <div className="px-3 pb-3 pt-1 border-t border-border/50 bg-bg/50 space-y-2.5 text-xs animate-in fade-in duration-150">
                        {ticket.description && (
                          <div className="space-y-1">
                            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider block">Description</span>
                            <p className="text-text leading-relaxed font-sans text-[11px] bg-surface p-2 rounded-lg border border-border/60">
                              {ticket.description}
                            </p>
                          </div>
                        )}

                        {ticket.response ? (
                          <div className="space-y-1 bg-emerald-50 border border-emerald-200 p-2.5 rounded-lg text-emerald-900">
                            <div className="flex items-center gap-1 text-[10px] font-extrabold uppercase tracking-wider text-emerald-800">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                              <span>Manager Resolution Note</span>
                            </div>
                            <p className="text-[11px] font-medium leading-relaxed mt-0.5">
                              {ticket.response}
                            </p>
                          </div>
                        ) : (
                          <div className="text-[11px] text-text-muted italic bg-surface p-2 rounded-lg border border-border/60 flex items-center gap-1.5">
                            <Clock className="w-3 h-3 text-amber-600" />
                            <span>Ticket is under review by support management team.</span>
                          </div>
                        )}

                        <div className="flex justify-end pt-0.5">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectTicket(ticket);
                            }}
                            className="text-primary hover:underline font-bold text-[11px] flex items-center gap-1 cursor-pointer"
                          >
                            <span>Open Details Dialog</span>
                            <ArrowRight className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/* =========================================================================
   6. PROFILE SCREEN
   ========================================================================= */
interface ProfileScreenProps {
  user: UserType;
  loginType: 'driver' | 'operator';
  onUpdateContact: (details: { emergencyContact: string; emergencyName?: string; emergencyRelation?: string; emergencyPhone?: string; address: string }) => void;
  t: (key: string, fallback: string) => string;
}

export const ProfileScreen: React.FC<ProfileScreenProps> = ({
  user,
  loginType,
  onUpdateContact,
  t
}) => {
  const isOperator = loginType === 'operator';
  const [isEditing, setIsEditing] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const cleanInitialEmergencyName = isOperator
    ? (user.assignedManagerName || user.emergencyName || '')
    : (user.emergencyName && user.emergencyName !== 'Priya Kumar' ? user.emergencyName : '');
  const cleanInitialEmergencyRelation = isOperator
    ? (user.emergencyRelation || 'Account Manager')
    : (user.emergencyRelation && user.emergencyRelation !== 'Spouse / Wife' ? user.emergencyRelation : (cleanInitialEmergencyName ? user.emergencyRelation || '' : ''));
  const cleanInitialEmergencyPhone = isOperator
    ? (user.assignedManagerPhone || user.emergencyPhone || '')
    : (user.emergencyPhone && user.emergencyPhone !== '9876543211' && user.emergencyPhone !== '9876543299' ? user.emergencyPhone : '');

  const [emergencyName, setEmergencyName] = useState(cleanInitialEmergencyName);
  const [emergencyRelation, setEmergencyRelation] = useState(cleanInitialEmergencyRelation);
  const [emergencyPhone, setEmergencyPhone] = useState(cleanInitialEmergencyPhone);
  const [bloodGroup, setBloodGroup] = useState(user.bloodGroup || 'B+');
  const [address, setAddress] = useState(user.address || '');

  useEffect(() => {
    if (isOperator) {
      setEmergencyName(user.assignedManagerName || user.emergencyName || '');
      setEmergencyRelation(user.emergencyRelation || 'Account Manager');
      setEmergencyPhone(user.assignedManagerPhone || user.emergencyPhone || '');
    } else {
      const cleanName = user.emergencyName && user.emergencyName !== 'Priya Kumar' ? user.emergencyName : '';
      const cleanPhone = user.emergencyPhone && user.emergencyPhone !== '9876543211' && user.emergencyPhone !== '9876543299' ? user.emergencyPhone : '';
      setEmergencyName(cleanName);
      setEmergencyRelation(cleanName ? (user.emergencyRelation || '') : '');
      setEmergencyPhone(cleanPhone);
    }
    setBloodGroup(user.bloodGroup || 'B+');
    setAddress(user.address || '');
  }, [user, loginType, isOperator]);

  const handleSave = () => {
    const formattedContact = emergencyName || emergencyPhone
      ? `${emergencyName}${emergencyRelation ? ` (${emergencyRelation})` : ''}${emergencyPhone ? ` - ${emergencyPhone}` : ''}`
      : '';
    onUpdateContact({
      emergencyContact: formattedContact,
      emergencyName,
      emergencyRelation,
      emergencyPhone,
      address
    });
    setIsEditing(false);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  const getRelationLabel = (rel: string) => {
    const r = (rel || '').toLowerCase();
    if (r.includes('spouse') || r.includes('wife') || r.includes('husband')) return t('relation.spouse', 'Spouse / Wife');
    if (r.includes('father')) return t('relation.father', 'Father');
    if (r.includes('mother')) return t('relation.mother', 'Mother');
    if (r.includes('brother')) return t('relation.brother', 'Brother');
    if (r.includes('sister')) return t('relation.sister', 'Sister');
    if (r.includes('relative') || r.includes('friend')) return t('relation.relative', 'Relative / Friend');
    return rel;
  };

  return (
    <div className="space-y-4 text-left font-sans pb-6 pt-0.5">
      <div className="flex items-center justify-between border-b border-border/60 pb-2.5">
        <h2 className="font-sans text-base font-extrabold text-text">
          {t('profile.title', 'User Profile')}
        </h2>

        {!isOperator && (
          <button
            onClick={() => (isEditing ? handleSave() : setIsEditing(true))}
            className={`shrink-0 flex h-8 items-center justify-center gap-1.5 rounded-xl px-3 font-sans text-xs font-bold text-white cursor-pointer shadow-xs transition-all ${
              isEditing ? 'bg-green hover:bg-green-hover' : 'bg-primary hover:bg-primary-hover'
            }`}
          >
            {isEditing ? <Check className="w-3.5 h-3.5" /> : <Edit2 className="w-3.5 h-3.5" />}
            {isEditing ? t('profile.saveChanges', 'Save Changes') : t('profile.editDetails', 'Edit Details')}
          </button>
        )}
      </div>

      {saveSuccess && (
        <div className="bg-green-light border border-green/30 text-green rounded-xl p-2.5 text-xs font-bold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{t('profile.savedSuccess', 'Profile details updated!')}</span>
        </div>
      )}

      <div className="bg-surface border border-border/80 rounded-2xl p-3.5 shadow-xs flex items-center gap-3.5 overflow-hidden">
        <div className="w-12 h-12 rounded-2xl bg-primary text-white font-black text-base flex items-center justify-center shrink-0 shadow-xs">
          {user.initials || (isOperator ? 'OP' : 'DR')}
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-sans text-sm font-extrabold text-text truncate">
            {isOperator ? `${user.name} (Fleet Operator)` : user.name}
          </h3>
          <p className="font-mono text-xs font-medium text-text-muted mt-0.5 truncate">
            {user.operatorCode && user.operatorCode !== user.id ? `${user.operatorCode} • ` : ''}ID: <span className="text-text font-bold">{user.id}</span>
          </p>
        </div>
      </div>

      <div className="bg-surface border border-border/80 rounded-2xl p-4 shadow-xs space-y-3">
        <h3 className="font-sans text-xs font-extrabold text-text uppercase tracking-wider text-text-muted">
          {isOperator ? t('profile.companyInfo', 'Company & Contact Info') : t('profile.personalTitle', 'Personal & Medical Info')}
        </h3>

        <div className="divide-y divide-border/50 font-sans text-xs">
          <div className="py-2.5 flex items-center justify-between gap-4">
            <span className="text-text-muted font-medium">{isOperator ? t('profile.companyPhone', 'Company Phone') : t('profile.registeredPhone', 'Registered Phone')}</span>
            <span className="font-sans font-bold text-text">+91 {user.phone}</span>
          </div>

          {!isOperator && (
            <>
              <div className="py-2.5 flex items-center justify-between gap-4">
                <span className="text-text-muted font-medium">{t('profile.dob', 'Date of Birth')}</span>
                <span className="font-sans font-bold text-text">{user.dob || '14-Aug-1992'}</span>
              </div>

              <div className="py-2.5 flex items-center justify-between gap-4">
                <span className="text-text-muted font-medium">{t('profile.bloodGroup', 'Blood Group')}</span>
                {isEditing ? (
                  <select
                    value={bloodGroup}
                    onChange={(e) => setBloodGroup(e.target.value)}
                    className="h-8 rounded-lg border border-border bg-bg px-2 font-bold text-text text-xs outline-none focus:border-primary cursor-pointer"
                  >
                    <option value="A+">A+</option>
                    <option value="A-">A-</option>
                    <option value="B+">B+</option>
                    <option value="B-">B-</option>
                    <option value="O+">O+</option>
                    <option value="O-">O-</option>
                    <option value="AB+">AB+</option>
                    <option value="AB-">AB-</option>
                  </select>
                ) : (
                  <span className="font-sans font-bold text-red-600">{bloodGroup}</span>
                )}
              </div>
            </>
          )}

          <div className="pt-2.5 flex flex-col gap-1">
            <span className="text-text-muted font-medium">{isOperator ? t('profile.businessAddress', 'Business / Office Address') : t('profile.address', 'Residential Address')}</span>
            {isEditing ? (
              <textarea
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                rows={2}
                className="w-full mt-1 rounded-xl border border-border bg-bg p-2.5 font-medium text-text text-xs outline-none focus:border-primary resize-none"
              />
            ) : (
              <span className="font-sans font-medium text-text text-xs leading-relaxed">{address || user.address || 'N/A'}</span>
            )}
          </div>
        </div>
      </div>

      {!isOperator ? (
        <div className="bg-surface border border-border/80 rounded-2xl p-4 shadow-xs space-y-3">
          <h3 className="font-sans text-xs font-extrabold text-text uppercase tracking-wider text-text-muted">
            {t('profile.documentsTitle', 'Documents & Credentials')}
          </h3>

          <div className="divide-y divide-border/50 font-sans text-xs">
            <div className="py-2.5 flex items-center justify-between gap-4">
              <span className="text-text-muted font-medium">{t('profile.aadharNumber', 'Aadhaar Number')}</span>
              <span className="font-mono font-bold text-text">•••• {user.aadhar.slice(-4)}</span>
            </div>

            <div className="py-2.5 flex items-center justify-between gap-4">
              <span className="text-text-muted font-medium">{t('profile.drivingLicense', 'Driving License')}</span>
              <span className="font-mono font-bold text-text">•••• {user.dlNumber.slice(-4)}</span>
            </div>

            <div className="py-2.5 flex items-center justify-between gap-4">
              <span className="text-text-muted font-medium">{t('profile.dlExpiry', 'DL Expiry Date')}</span>
              <span className="font-sans font-bold text-text">{user.dlExpiry}</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-surface border border-border/80 rounded-2xl p-4 shadow-xs space-y-3">
          <h3 className="font-sans text-xs font-extrabold text-text uppercase tracking-wider text-text-muted">
            {t('profile.fleetRegDeposit', 'Fleet Registration & Deposit')}
          </h3>

          <div className="divide-y divide-border/50 font-sans text-xs">
            <div className="py-2.5 flex items-center justify-between gap-4">
              <span className="text-text-muted font-medium">{t('profile.operatorCode', 'Operator Code')}</span>
              <span className="font-mono font-bold text-primary">{user.operatorCode}</span>
            </div>
            <div className="py-2.5 flex items-center justify-between gap-4">
              <span className="text-text-muted font-medium">{t('profile.operatorType', 'Operator Type')}</span>
              <span className="font-sans font-bold text-text">{user.operatorType === 'Fleet Owner' ? t('profile.fleetOwner', 'Fleet Owner') : (user.operatorType || t('profile.fleetOwner', 'Fleet Owner'))}</span>
            </div>
            <div className="py-2.5 flex items-center justify-between gap-4">
              <span className="text-text-muted font-medium">{t('profile.securityDeposit', 'Security Deposit')}</span>
              <span className="font-sans font-bold text-green">
                Paid: ₹{(user.depositPaidSoFar ?? user.depositAmount ?? 0).toLocaleString('en-IN')} / ₹{(user.depositTotalRequired ?? user.depositAmount ?? 0).toLocaleString('en-IN')}
              </span>
            </div>
          </div>
        </div>
      )}

      <div className="bg-surface border border-border/80 rounded-2xl p-4 shadow-xs space-y-3">
        <h3 className="font-sans text-xs font-extrabold text-text uppercase tracking-wider text-text-muted">
          {isOperator ? t('profile.assignedAccountManager', 'Assigned Account Manager') : t('profile.emergencyTitle', 'Emergency Contact')}
        </h3>

        {isEditing ? (
          <div className="space-y-3 font-sans text-xs">
            <div>
              <label className="text-text-muted font-medium block mb-1">
                {isOperator ? t('profile.managerName', 'Manager Name') : t('profile.emergencyPerson', 'Contact Person Name')}
              </label>
              <input
                type="text"
                value={emergencyName}
                onChange={(e) => setEmergencyName(e.target.value)}
                className="w-full h-9 rounded-xl border border-border bg-bg px-3 font-bold text-text text-xs outline-none focus:border-primary"
                placeholder={isOperator ? 'e.g. LetzRyd Operations Desk' : 'e.g. Sunita Kumar'}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-text-muted font-medium block mb-1">
                  {isOperator ? t('profile.role', 'Role') : t('profile.emergencyRelation', 'Relation')}
                </label>
                {isOperator ? (
                  <input
                    type="text"
                    value={emergencyRelation}
                    onChange={(e) => setEmergencyRelation(e.target.value)}
                    className="w-full h-9 rounded-xl border border-border bg-bg px-3 font-bold text-text text-xs outline-none focus:border-primary"
                    placeholder="Account Manager"
                  />
                ) : (
                  <select
                    value={emergencyRelation}
                    onChange={(e) => setEmergencyRelation(e.target.value)}
                    className="w-full h-9 rounded-xl border border-border bg-bg px-2.5 font-bold text-text text-xs outline-none focus:border-primary cursor-pointer"
                  >
                    <option value="">{t('relation.select', '-- Select Relation --')}</option>
                    <option value="Spouse / Wife">{t('relation.spouse', 'Spouse / Wife')}</option>
                    <option value="Father">{t('relation.father', 'Father')}</option>
                    <option value="Mother">{t('relation.mother', 'Mother')}</option>
                    <option value="Brother">{t('relation.brother', 'Brother')}</option>
                    <option value="Sister">{t('relation.sister', 'Sister')}</option>
                    <option value="Relative / Friend">{t('relation.relative', 'Relative / Friend')}</option>
                  </select>
                )}
              </div>

              <div>
                <label className="text-text-muted font-medium block mb-1">
                  {isOperator ? t('profile.managerPhone', 'Manager Phone') : t('profile.emergencyPhone', 'Emergency Mobile')}
                </label>
                <input
                  type="tel"
                  value={emergencyPhone}
                  onChange={(e) => setEmergencyPhone(e.target.value)}
                  className="w-full h-9 rounded-xl border border-border bg-bg px-3 font-bold text-text text-xs outline-none focus:border-primary font-mono"
                  placeholder="9812345678"
                />
              </div>
            </div>
          </div>
        ) : (!isOperator && !emergencyName && !emergencyPhone) ? (
          <div className="py-3 px-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-center space-y-2">
            <p className="font-sans text-xs text-amber-700 font-medium">
              No emergency contact on file.
            </p>
            <button
              type="button"
              onClick={() => setIsEditing(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all cursor-pointer shadow-2xs"
            >
              <Edit2 className="w-3 h-3" />
              Not Provided — Tap to Add Contact
            </button>
          </div>
        ) : (
          <div className="divide-y divide-border/50 font-sans text-xs">
            <div className="py-2.5 flex items-center justify-between gap-4">
              <span className="text-text-muted font-medium">
                {isOperator ? t('profile.managerName', 'Manager Name') : t('profile.emergencyPerson', 'Contact Person')}
              </span>
              <span className="font-sans font-bold text-text">
                {isOperator 
                  ? (user.assignedManagerName || user.emergencyName || emergencyName || 'LetzRyd Operations Desk') 
                  : (emergencyName || (
                    <span 
                      onClick={() => setIsEditing(true)} 
                      className="text-amber-600 font-medium cursor-pointer hover:underline inline-flex items-center gap-1"
                    >
                      Not Provided — Tap to Add Contact
                    </span>
                  ))}
              </span>
            </div>

            <div className="py-2.5 flex items-center justify-between gap-4">
              <span className="text-text-muted font-medium">
                {isOperator ? t('profile.role', 'Role') : t('profile.emergencyRelation', 'Relation')}
              </span>
              <span className="font-sans font-bold text-text">
                {isOperator ? (user.emergencyRelation === 'Account Manager' ? t('profile.accountManagerRole', 'Account Manager') : (user.emergencyRelation || t('profile.accountManagerRole', 'Account Manager'))) : (emergencyRelation ? getRelationLabel(emergencyRelation) : '—')}
              </span>
            </div>

            <div className="py-2.5 flex items-center justify-between gap-4">
              <span className="text-text-muted font-medium">
                {isOperator ? t('profile.managerPhone', 'Manager Phone') : t('profile.emergencyPhone', 'Emergency Mobile')}
              </span>
              <span className="font-mono font-bold text-text">
                {isOperator ? (() => {
                  const p = (user.assignedManagerPhone || user.emergencyPhone || emergencyPhone || '').trim();
                  if (!p) return `+91 ${OFFICIAL_MOBILE_HELPLINE}`;
                  return isLandline(p) ? p : `+91 ${p.replace(/\D/g, '').slice(-10)}`;
                })() : (emergencyPhone ? `+91 ${emergencyPhone.replace(/\D/g, '').slice(-10)}` : '—')}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

/* =========================================================================
   7. RENTAL PLAN SCREEN
   ========================================================================= */
interface RentalScreenProps {
  plan: RentalPlan;
  t: (key: string, fallback: string) => string;
}

export const RentalScreen: React.FC<RentalScreenProps> = ({ plan, t }) => {
  return (
    <div className="space-y-4 text-left font-sans">
      <div>
        <h2 className="font-sans text-base font-bold text-text">
          {t('rental.title', 'Driver Rental Agreement')}
        </h2>
        <p className="font-sans text-xs text-text-muted mt-0.5">
          Configured daily rate metrics and settlement terms
        </p>
      </div>

      <div className="bg-white border border-border rounded-xl p-4 shadow-xs">
        <h3 className="font-sans text-lg font-extrabold text-text">{plan.name} Plan</h3>
        <p className="font-sans text-xs text-text-muted mt-0.5">Active since {plan.planStart}</p>
        <div className="mt-3 pt-3 border-t border-border">
          <div className="font-sans text-2xl font-extrabold text-primary">
            ₹{plan.dailyRate.toLocaleString('en-IN')}<span className="text-xs font-medium text-text-muted">/day</span>
          </div>
        </div>
      </div>
    </div>
  );
};

/* =========================================================================
   8. OPERATOR SCREEN
   ========================================================================= */
interface OperatorScreenProps {
  fleet: Fleet;
  onSelectVehicle: (number: string) => void;
  t: (key: string, fallback: string) => string;
}

export const OperatorScreen: React.FC<OperatorScreenProps> = ({ fleet, onSelectVehicle, t }) => {
  const [searchQuery, setSearchQuery] = useState('');

  const totalVehicles = fleet.vehicles.length;
  const totalToPay = fleet.vehicles.reduce((sum, v) => (v.currentWeekOs < 0 ? sum + Math.abs(v.currentWeekOs) : sum), 0);
  const totalToCollect = fleet.vehicles.reduce((sum, v) => (v.currentWeekOs > 0 ? sum + v.currentWeekOs : sum), 0);

  const vehicleFleetList = fleet.vehicles.filter(
    (v) =>
      v.number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.model.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.make.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.driverName.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatCurrency = (val: number) => {
    const hasDecimals = val % 1 !== 0;
    return '₹' + Math.abs(val).toLocaleString('en-IN', {
      minimumFractionDigits: hasDecimals ? 2 : 0,
      maximumFractionDigits: 2,
    });
  };

  return (
    <div className="space-y-4 text-left font-sans">
      <div>
        <h2 className="font-sans text-base font-bold text-text">
          {t('operator.dashboardTitle', 'Fleet Overview')}
        </h2>
        <p className="font-sans text-xs text-text-muted mt-0.5">
          {t('operator.statusSubtitle', 'Real-time settlement status')} ({totalVehicles} {t('operator.vehiclesUnit', 'Vehicles')})
        </p>
      </div>

      <div className="grid grid-cols-3 gap-2 font-sans text-xs">
        <div className="p-2 sm:p-2.5 bg-surface border border-border rounded-xl text-center shadow-xs flex flex-col justify-between">
          <p className="text-[10px] font-bold text-text-muted uppercase tracking-wider">{t('operator.toPay', 'TO PAY')}</p>
          <p className="font-sans text-xs sm:text-sm font-bold text-green mt-1 whitespace-nowrap font-mono">
            +{formatCurrency(totalToPay)}
          </p>
        </div>
        <div className="p-2 sm:p-2.5 bg-surface border border-border rounded-xl text-center shadow-xs flex flex-col justify-between">
          <p className="text-[10px] font-bold text-text-muted uppercase tracking-wider">{t('operator.toCollect', 'TO COLLECT')}</p>
          <p className="font-sans text-xs sm:text-sm font-bold text-red-600 mt-1 whitespace-nowrap font-mono">
            -{formatCurrency(totalToCollect)}
          </p>
        </div>
        <div className="p-2 sm:p-2.5 bg-surface border border-border rounded-xl text-center shadow-xs flex flex-col justify-between">
          <p className="text-[10px] font-bold text-text-muted uppercase tracking-wider">{t('operator.cars', 'CARS')}</p>
          <p className="font-sans text-xs sm:text-sm font-bold text-text mt-1">{totalVehicles}</p>
        </div>
      </div>

      {/* Fleet Security Deposit Card */}
      <div className="bg-surface border border-border rounded-xl p-3 shadow-xs text-left font-sans text-xs">
        <div className="flex items-center justify-between">
          <span className="font-sans text-xs font-bold text-text uppercase tracking-wider">
            {t('operator.fleetDeposit', 'FLEET SECURITY DEPOSIT')}
          </span>
          <div className="flex items-center gap-3 text-xs font-sans">
            <span>
              <span className="text-text-muted font-medium">{t('hisaab.paid', 'Paid:')} </span>
              <span className="font-bold text-green">
                ₹{(fleet.depositPaidSoFar ?? 0).toLocaleString('en-IN', { minimumFractionDigits: (fleet.depositPaidSoFar ?? 0) % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}
              </span>
            </span>
            <span>
              <span className="text-text-muted font-medium">{t('hisaab.pending', 'Pending:')} </span>
              <span className="font-bold text-amber-700">
                ₹{(fleet.depositPending ?? 0).toLocaleString('en-IN', { minimumFractionDigits: (fleet.depositPending ?? 0) % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}
              </span>
            </span>
          </div>
        </div>
      </div>

      {/* SEARCH BAR */}
      <div className="relative">
        <Search className="w-4 h-4 text-text-muted absolute left-3 top-3" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={t('operator.searchPlaceholder', 'Search vehicle number, model or driver...')}
          className="w-full pl-9 pr-3 py-2 rounded-xl border border-border bg-bg text-xs font-medium outline-none focus:border-primary transition-colors"
        />
      </div>

      {/* VEHICLE FLEET LIST CARD */}
      <div className="bg-surface border border-border rounded-xl p-3.5 shadow-sm space-y-2.5">
        <div className="border-b border-border/60 pb-2 flex items-center justify-between">
          <h3 className="font-sans text-xs font-bold text-text uppercase tracking-wider flex items-center gap-1.5">
            <Car className="w-3.5 h-3.5 text-primary" />
            <span>{t('operator.vehicleFleet', 'VEHICLE FLEET')} ({vehicleFleetList.length})</span>
          </h3>
          <span className="text-[10px] font-semibold text-text-muted">{t('operator.tapToView', 'Tap to view Hisaab')}</span>
        </div>

        <div className="divide-y divide-border/60">
          {vehicleFleetList.length === 0 ? (
            <div className="py-6 text-center text-text-muted text-xs">
              {searchQuery ? t('operator.noVehiclesMatch', 'No vehicles match your search') : t('operator.noVehicles', 'No vehicles assigned to this fleet')}
            </div>
          ) : (
            vehicleFleetList.map((v) => (
              <div
                key={`v-${v.number}`}
                onClick={() => onSelectVehicle(v.number)}
                className="py-2.5 flex items-center justify-between first:pt-0 last:pb-0 hover:bg-bg/60 cursor-pointer rounded-md px-1 transition-colors group"
              >
                <div className="flex items-center gap-2.5 min-w-0 flex-1 pr-2">
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border bg-emerald-500/10 border-emerald-500/20 text-emerald-600">
                    <Car className="w-4 h-4" />
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono text-xs font-black text-text tracking-wide bg-bg px-1.5 py-0.5 rounded border border-border/60">
                        {v.number}
                      </span>
                      <span className="text-[10px] font-semibold text-text-muted font-sans truncate">
                        {v.make} {v.model}
                      </span>
                    </div>
                    <p className="font-sans text-[11px] text-text-muted mt-1 flex items-center gap-1 truncate">
                      <span className="text-[10px] uppercase font-bold text-text-muted/80">{t('operator.assignedDriver', 'Assigned Driver')}:</span>
                      <span className="font-semibold text-text truncate">{v.driverName || 'Unassigned'}</span>
                    </p>
                  </div>
                </div>

                {(() => {
                  const latestH = v.hisaabWeeks && v.hisaabWeeks.length > 0 ? v.hisaabWeeks[0] : null;
                  const effectiveOs = v.currentWeekOs !== 0 
                    ? v.currentWeekOs 
                    : (latestH ? ((latestH.toPay || 0) > 0 ? -latestH.toPay : (latestH.toCollect || latestH.currentWeekOs || 0)) : 0);

                  return (
                    <div className="text-right shrink-0 flex flex-col items-end">
                      {effectiveOs < 0 ? (
                        <span className="font-sans text-xs font-bold text-green whitespace-nowrap font-mono">
                          +{formatCurrency(effectiveOs)}
                        </span>
                      ) : effectiveOs > 0 ? (
                        <span className="font-sans text-xs font-bold text-red-600 whitespace-nowrap font-mono">
                          -{formatCurrency(effectiveOs)}
                        </span>
                      ) : (
                        <span className="font-sans text-xs font-bold text-text-muted font-mono">
                          ₹0
                        </span>
                      )}
                      <span className="font-sans text-[10px] font-bold text-primary group-hover:underline mt-0.5 whitespace-nowrap">
                        {t('operator.viewHisaab', 'View Hisaab →')}
                      </span>
                    </div>
                  );
                })()}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

/* =========================================================================
   9. OPERATOR VEHICLE SCREEN
   ========================================================================= */
interface OperatorVehicleScreenProps {
  vehicle: FleetVehicle;
  weekIndex: number;
  onPrevWeek: () => void;
  onNextWeek: () => void;
  onBack: () => void;
  t: (key: string, fallback: string) => string;
}

export const OperatorVehicleScreen: React.FC<OperatorVehicleScreenProps> = ({
  vehicle,
  weekIndex,
  onPrevWeek,
  onNextWeek,
  onBack,
  t
}) => {
  return (
    <div className="space-y-4 text-left font-sans">
      <div className="flex items-center gap-3">
        <button
          onClick={onBack}
          className="w-9 h-9 rounded-lg border border-border bg-white flex items-center justify-center text-text-muted hover:text-text cursor-pointer transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="flex-1 min-w-0">
          <h2 className="font-sans text-base font-bold text-text truncate">{vehicle.driverName} — Hisaab Statement</h2>
          <p className="font-sans text-xs text-text-muted truncate">Allocated Vehicle: <span className="font-mono font-semibold">{vehicle.number}</span> ({vehicle.model})</p>
        </div>
      </div>

      <HisaabScreen
        weeks={vehicle.hisaabWeeks}
        weekIndex={weekIndex}
        onPrevWeek={onPrevWeek}
        onNextWeek={onNextWeek}
        loginType="operator"
        onPayClick={() => {}}
        t={t}
      />
    </div>
  );
};

