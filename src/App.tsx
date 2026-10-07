/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect, useRef, useMemo } from 'react';
// @ts-ignore
import logoIcon from './assets/logo-icon.png';
import { motion, AnimatePresence } from 'motion/react';
import {
  Bell,
  ReceiptIndianRupee,
  Building,
  Headset,
  User as UserIcon,
  ChevronRight,
  ChevronDown,
  LogOut,
  TriangleAlert,
  AlertTriangle,
  AlertCircle,
  Car,
  CreditCard,
  Wallet,
  Home,
  FileText,
  TrendingUp,
  CheckCircle2,
  Clock,
  Sparkles,
  ShieldAlert,
  ArrowUpRight,
  Target,
  Gift,
  PhoneCall,
  Check,
  ShieldCheck,
  Info
} from 'lucide-react';

import {
  USER_DATA,
  VEHICLE_DATA,
  RENTAL_PLAN_DATA,
  HISAAB_WEEKS_DATA,
  OPERATOR_FLEET_DATA,
  INITIAL_TICKETS,
  INITIAL_NOTIFICATIONS,
  ANNOUNCEMENTS_DATA,
  SUPPORT_HOTLINE,
  LETZRYD_UPI_ID,
  TICKET_CATEGORIES,
  TRANSLATIONS_EN,
  TRANSLATIONS_HI,
  TRANSLATIONS_MR,
  TRANSLATIONS_TE,
  TRANSLATIONS_KN,
  DEMO_PROFILES,
  SALEEM_FLEET_DATA
} from './data';

import { User, Vehicle, RentalPlan, HisaabWeek, Fleet, FleetVehicle, FleetDriverItem, Ticket, Notification, Language } from './types';
import {
  auth,
  RecaptchaVerifier,
  signInWithPhoneNumber,
  isFirebaseConfigured,
  ConfirmationResult
} from './firebase';
import {
  verifyOTPBackend,
  getDriverByPhone,
  getOperatorByPhone,
  getOperatorFleet,
  getDriverHisaabs,
  getOperatorHisaabs,
  getVehicleHisaabs,
  getNotifications as fetchNotifications,
  getTickets,
  createTicket as apiCreateTicket,
  submitReferral as apiSubmitReferral,
  mapDriverToUser,
  mapOperatorToUser,
  mapDriverToVehicle,
  mapDriverToRentalPlan,
  mapHisaabToWeek,
  mapNotification,
  mapTicket,
  BACKEND_URL,
} from './api';

declare global {
  interface Window {
    recaptchaVerifier: any;
  }
}



import {
  Toast,
  NewTicketModal,
  TicketDetailModal,
  NotificationModal,
  EmergencySosModal,
  ProfileScreen,
  SettleScreen,
  SupportScreen,
  RentalScreen,
  VehicleScreen,
  HisaabScreen,
  OperatorScreen,
  OperatorVehicleScreen,
  ReferralScreen
} from './components';

const AUTH_STORAGE_KEY = 'letzryd_driver_portal_session';

function deduplicateVehiclesList(vehicles: FleetVehicle[]): FleetVehicle[] {
  if (!vehicles || !Array.isArray(vehicles)) return [];
  const seen = new Set<string>();
  const result: FleetVehicle[] = [];
  for (const v of vehicles) {
    const num = (v.number || '').trim();
    if (!num) continue;
    if (!seen.has(num)) {
      seen.add(num);
      result.push(v);
    } else {
      const idx = result.findIndex(item => (item.number || '').trim() === num);
      if (idx !== -1) {
        const existing = result[idx];
        const vHCount = v.hisaabWeeks?.length || 0;
        const eHCount = existing.hisaabWeeks?.length || 0;
        if (vHCount > eHCount) {
          result[idx] = v;
        } else if (vHCount === eHCount) {
          if (v.currentWeekOs !== 0 && existing.currentWeekOs === 0) {
            result[idx] = v;
          }
        }
      }
    }
  }
  return result;
}

export function mapFleetDataToVehicles(fleetData: any): FleetVehicle[] {
  const rawVehicles = fleetData?.vehicles || [];
  const seenVehNumbers = new Set<string>();
  const deduplicated: any[] = [];

  for (const v of rawVehicles) {
    const vNum = (v.vehicle_number || '').trim();
    if (!vNum) continue;
    if (!seenVehNumbers.has(vNum)) {
      seenVehNumbers.add(vNum);
      deduplicated.push(v);
    } else {
      const idx = deduplicated.findIndex(item => (item.vehicle_number || '').trim() === vNum);
      if (idx !== -1) {
        const existing = deduplicated[idx];
        const vHCount = v.hisaab_count || 0;
        const eHCount = existing.hisaab_count || 0;
        if (vHCount > eHCount) {
          deduplicated[idx] = v;
        } else if (vHCount === eHCount) {
          if (v.current_week_os !== 0 && existing.current_week_os === 0) {
            deduplicated[idx] = v;
          }
        }
      }
    }
  }

  return deduplicated.map((v: any) => ({
    number: v.vehicle_number,
    make: v.vehicle_make || 'Maruti',
    model: v.vehicle_model || 'Dzire CNG',
    driverName: v.driver_name || 'Driver',
    driverId: v.driver_id,
    plan: { name: 'Standard', dailyRate: v.daily_rate || 1000 },
    currentWeekOs: v.current_week_os || 0,
    status: (v.status === 'active' ? 'active' : 'idle') as 'active' | 'idle',
    hisaabWeeks: [],
  }));
}

function getInitialAuth() {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed?.operatorFleet?.vehicles) {
        parsed.operatorFleet.vehicles = deduplicateVehiclesList(parsed.operatorFleet.vehicles);
      }
      return parsed;
    }
  } catch (e) {
    console.warn('Failed to parse saved session:', e);
  }
  return null;
}

export default function App() {
  const searchParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null;
  const isReturningFromPayment = Boolean(searchParams?.get('order_id'));
  const savedSession = useMemo(() => getInitialAuth(), []);

  // Multi-Language State (Default EN, switchable to HI, MR, TE, KN)
  const [language, setLanguage] = useState<Language>(() => {
    return (typeof window !== 'undefined' ? (localStorage.getItem('letzryd_language') as Language) : null) || 'en';
  });

  // Authentication & Session (Persisted across payment redirects)
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(() => {
    if (isReturningFromPayment) return true;
    return Boolean(savedSession?.isLoggedIn);
  });
  const [loginType, setLoginType] = useState<'driver' | 'operator'>(() => savedSession?.loginType || 'driver');
  const [phoneInput, setPhoneInput] = useState<string>(() => savedSession?.phoneInput || '');
  const [otpSent, setOtpSent] = useState(false);
  const [otpInput, setOtpInput] = useState('');
  const [confirmationResult, setConfirmationResult] = useState<ConfirmationResult | null>(null);
  const [isSendingOtp, setIsSendingOtp] = useState(false);
  const [isVerifyingOtp, setIsVerifyingOtp] = useState(false);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [phoneError, setPhoneError] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [adminSearchOpen, setAdminSearchOpen] = useState(false);
  const [adminSearchQuery, setAdminSearchQuery] = useState('');
  const [adminSearchResults, setAdminSearchResults] = useState<{ name: string; phone: string; role: 'driver' | 'operator'; id: string; detail?: string }[]>([]);
  const [adminSearchLoading, setAdminSearchLoading] = useState(false);
  const [adminSearchError, setAdminSearchError] = useState<string | null>(null);
  const [adminLoginLoading, setAdminLoginLoading] = useState(false);

  // Cancellation ref: set to true when user goes back from OTP screen mid-request
  const otpRequestCancelledRef = useRef(false);

  // Global Navigation
  const [currentScreen, setCurrentScreen] = useState<string>(() => {
    if (isReturningFromPayment) return 'settle';
    return savedSession?.currentScreen || 'home';
  });
  const [prevScreen, setPrevScreen] = useState<string>('home');

  // Ledger Week Indices
  const [driverWeekIndex, setDriverWeekIndex] = useState(0);
  const [operatorVehicleWeekIndex, setOperatorVehicleWeekIndex] = useState(0);

  // Data Collections
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>(INITIAL_NOTIFICATIONS);
  const [hisaabWeeks, setHisaabWeeks] = useState<HisaabWeek[]>(() => savedSession?.hisaabWeeks || HISAAB_WEEKS_DATA);
  const [operatorFleet, setOperatorFleet] = useState<Fleet>(() => savedSession?.operatorFleet || OPERATOR_FLEET_DATA);
  const [driverUser, setDriverUser] = useState<User>(() => savedSession?.driverUser || USER_DATA);
  const [driverVehicle, setDriverVehicle] = useState<Vehicle>(() => savedSession?.driverVehicle || VEHICLE_DATA);
  const [driverRentalPlan, setDriverRentalPlan] = useState<RentalPlan>(() => savedSession?.driverRentalPlan || RENTAL_PLAN_DATA);

  // Active Vehicle Selection for Operator View
  const [selectedVehicleNumber, setSelectedVehicleNumber] = useState<string | null>(() => operatorFleet.vehicles[0]?.number || null);

  // Active Emergency SOS Alarm
  const [sosActivated, setSosActivated] = useState(false);
  const [sosTime, setSosTime] = useState<string | null>(null);

  // Modal Control States
  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const [isNewTicketOpen, setIsNewTicketOpen] = useState(false);
  const [isReferralOpen, setIsReferralOpen] = useState(false);
  const [isSosModalOpen, setIsSosModalOpen] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [isSettleModalOpen, setIsSettleModalOpen] = useState(false);
  const [settleAmount, setSettleAmount] = useState<number>(0);
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);
  const [paymentSuccess, setPaymentSuccess] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' | 'warning' } | null>(null);

  // Reactive Toast System
  const triggerToast = (msg: string, type: 'success' | 'error' | 'info' | 'warning' = 'info') => {
    setToast({ message: msg, type });
  };

  // Universal Translation Lookup for all 5 languages
  const t = (key: string, fallback: string): string => {
    let dict = TRANSLATIONS_EN;
    if (language === 'hi') dict = TRANSLATIONS_HI;
    if (language === 'mr') dict = TRANSLATIONS_MR;
    if (language === 'te') dict = TRANSLATIONS_TE;
    if (language === 'kn') dict = TRANSLATIONS_KN;

    return dict[key] || TRANSLATIONS_EN[key] || fallback;
  };

  // Format Vehicle Number with clean spacing (e.g. KA05AQ7692 -> KA 05 AQ 7692)
  const formatVehicleNumber = (num: string): string => {
    if (!num) return num;
    const match = num.match(/^([A-Z]{2})(\d{2})([A-Z]{1,2})(\d{4})$/i);
    if (match) {
      return `${match[1].toUpperCase()} ${match[2]} ${match[3].toUpperCase()} ${match[4]}`;
    }
    return num;
  };

  const handleLanguageChange = (lang: Language) => {
    setLanguage(lang);
    try {
      localStorage.setItem('letzryd_language', lang);
    } catch (e) {}
    const langNames: Record<Language, string> = {
      en: 'English',
      hi: 'हिंदी (Hindi)',
      mr: 'मराठी (Marathi)',
      te: 'తెలుగు (Telugu)',
      kn: 'ಕನ್ನಡ (Kannada)'
    };
    triggerToast(`Language changed to ${langNames[lang]}`, 'success');
  };

  // reCAPTCHA is initialized fresh on each OTP request inside handleSendOtp

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setPhoneError(null);
    const cleanPhone = phoneInput.replace('+91', '').replace(/[\s-]/g, '').trim();
    if (!cleanPhone || cleanPhone.length < 10) {
      setPhoneError('Please enter a valid 10-digit mobile number');
      triggerToast('Please enter a valid 10-digit mobile number', 'error');
      return;
    }

    // Reset cancellation flag for this new request
    otpRequestCancelledRef.current = false;

    // Step 0: Check if number is registered in LetzRyd BEFORE sending SMS
    const isDemoProfile = DEMO_PROFILES.some(p => p.phone === cleanPhone);
    let isRegisteredInBackend = false;

    if (!isDemoProfile) {
      setIsSendingOtp(true);
      try {
        const driverRes = await getDriverByPhone(cleanPhone).catch(() => null);
        const opRes = !driverRes ? await getOperatorByPhone(cleanPhone).catch(() => null) : null;
        if (driverRes || opRes) {
          isRegisteredInBackend = true;
        }
      } catch (err) {
        console.warn('Backend phone verification error:', err);
      } finally {
        setIsSendingOtp(false);
      }

      // User may have gone back while we were checking — abort
      if (otpRequestCancelledRef.current) return;

      if (!isRegisteredInBackend) {
        const errorText = `Account does not exist. Mobile number +91 ${cleanPhone} is not registered with LetzRyd. Please contact your Fleet Manager or Support.`;
        setPhoneError(errorText);
        triggerToast(errorText, 'error');
        setOtpSent(false);
        return;
      }
    }

    if (isFirebaseConfigured && auth) {
      setIsSendingOtp(true);
      try {
        // Destroy old reCAPTCHA instance AND clear its DOM so Firebase doesn't
        // throw "reCAPTCHA has already been rendered in this element"
        if (window.recaptchaVerifier) {
          try { window.recaptchaVerifier.clear(); } catch (e) {}
          window.recaptchaVerifier = null;
        }
        const rcContainer = document.getElementById('recaptcha-container');
        if (rcContainer) rcContainer.innerHTML = '';

        window.recaptchaVerifier = new RecaptchaVerifier(auth, 'recaptcha-container', {
          size: 'invisible',
          callback: () => {}
        });
        await window.recaptchaVerifier.render();

        const formattedPhone = `+91${cleanPhone}`;
        const confirmationPromise = signInWithPhoneNumber(auth, formattedPhone, window.recaptchaVerifier);
        const timeoutPromise = new Promise<never>((_, reject) =>
          setTimeout(() => reject(new Error('SMS network timeout. Please enter OTP.')), 8000)
        );
        const confirmation = await Promise.race([confirmationPromise, timeoutPromise]);

        // User went back while Firebase was sending SMS — discard result
        if (otpRequestCancelledRef.current) return;

        setConfirmationResult(confirmation);
        setOtpSent(true);
        triggerToast(`Live SMS OTP sent to ${formattedPhone}!`, 'success');
      } catch (err: any) {
        console.error('Firebase live SMS dispatch error:', err);
        if (window.recaptchaVerifier) {
          try { window.recaptchaVerifier.clear(); } catch (e) {}
          window.recaptchaVerifier = null;
        }
        // User went back while Firebase was failing — discard
        if (otpRequestCancelledRef.current) return;

        setConfirmationResult(null);
        setOtpSent(true);
        const errMsg = err?.code === 'auth/quota-exceeded'
          ? 'SMS quota exceeded. (Enter 1234 to proceed)'
          : err?.code === 'auth/too-many-requests'
          ? 'Too many attempts. Please wait or enter 1234.'
          : err?.message || 'Enter OTP code to proceed';
        triggerToast(`SMS Notice: ${errMsg}`, 'info');
      } finally {
        setIsSendingOtp(false);
      }
    } else {
      if (otpRequestCancelledRef.current) return;
      setOtpSent(true);
      triggerToast('OTP code sent successfully (Demo OTP: 1234)', 'info');
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanPhone = phoneInput.replace('+91', '').replace(/[\s-]/g, '').trim();
    const cleanOtp = otpInput.trim();
    if (!cleanOtp || cleanOtp.length < 4) {
      triggerToast('Please enter a valid OTP code', 'error');
      return;
    }

    const matchedProfile = DEMO_PROFILES.find(p => p.phone === cleanPhone);
    let inferredRole: 'driver' | 'operator' = 'driver';
    if (matchedProfile) {
      inferredRole = matchedProfile.role;
    } else {
      try {
        const opCheck = await getOperatorByPhone(cleanPhone).catch(() => null);
        const drvCheck = await getDriverByPhone(cleanPhone).catch(() => null);
        if (opCheck && !drvCheck) {
          inferredRole = 'operator';
        } else if (opCheck && drvCheck) {
          // If loginType was explicitly toggled or saved, respect it; otherwise if operator owns vehicles, default to operator
          if (loginType === 'operator') {
            inferredRole = 'operator';
          } else if (opCheck.total_vehicles && opCheck.total_vehicles > 0) {
            inferredRole = 'operator';
          } else {
            inferredRole = 'driver';
          }
        } else {
          inferredRole = 'driver';
        }
      } catch {
        inferredRole = (loginType === 'operator' ? 'operator' : 'driver');
      }
    }

    const isStaticOtp = cleanOtp === '1234';
    setIsVerifyingOtp(true);
    setBackendError(null);

    try {
      // Step 1: Firebase verification (for live carrier SMS OTP)
      if (confirmationResult && !isStaticOtp) {
        try {
          await confirmationResult.confirm(cleanOtp);
        } catch (firebaseErr: any) {
          console.error('Firebase OTP Confirmation Failed:', firebaseErr);
          const errorMsg = firebaseErr?.code === 'auth/invalid-verification-code' 
            ? 'Incorrect SMS OTP code. Please check your phone and try again, or use master OTP 1234.'
            : (firebaseErr?.message || 'Invalid SMS OTP. Please try again.');
          throw new Error(errorMsg);
        }
      } else if (!confirmationResult && !isStaticOtp) {
        // If no SMS was dispatched (offline / demo mode), only master OTP 1234 is valid
        if (cleanOtp !== '1234' && cleanOtp !== (matchedProfile?.otp || '1234')) {
          throw new Error('Invalid OTP code. Please enter the SMS OTP sent to your phone or master OTP: 1234');
        }
      }

      // Step 2: Backend auth - get JWT
      setIsLoadingProfile(true);
      let backendSuccess = false;
      try {
        const authResult = await verifyOTPBackend(cleanPhone, cleanOtp, inferredRole);
        
        // Step 3: Load profile from backend
        if (authResult.user_type === 'operator') {
          try {
            const opProfile = await getOperatorByPhone(cleanPhone);
            const fleetData = await getOperatorFleet(opProfile.app_operator_id);
            const notifs = await fetchNotifications(opProfile.app_operator_id, 'operator');
            const opHisaabs = await getOperatorHisaabs(opProfile.app_operator_id).catch(() => []);

            setDriverUser(mapOperatorToUser(opProfile));

            // Map fleet data with deduplication and driver hisaabs
            const mappedVehicles: FleetVehicle[] = mapFleetDataToVehicles(fleetData);
            const mappedDrivers: FleetDriverItem[] = (fleetData?.drivers || []).map((d: any) => ({
              driverId: d.app_driver_id,
              driverCode: d.driver_code || `DRV-${d.app_driver_id}`,
              name: d.full_name || 'Driver',
              phone: d.phone || '',
              assignedVehicle: d.assigned_vehicle || 'Unassigned',
              vehicleModel: d.vehicle_model || 'Maruti Wagonr Tour H3 CNG',
              rentalPlan: d.rental_plan || 'Fixed',
              currentWeekOs: d.current_week_os || 0,
              status: d.status || 'active',
              hisaabCount: d.hisaab_count || 0
            }));

            const mappedFleet: Fleet = {
              operatorCode: fleetData.operator_code,
              operatorName: fleetData.company_name,
              depositTotalRequired: fleetData.deposit_total_req,
              depositPaidSoFar: fleetData.deposit_paid,
              depositPending: fleetData.deposit_pending,
              vehicles: mappedVehicles,
              drivers: mappedDrivers,
            };
            setOperatorFleet(mappedFleet);
            if (opHisaabs && opHisaabs.length > 0) {
              setHisaabWeeks(opHisaabs.map(mapHisaabToWeek));
            } else if (mappedVehicles.length > 0 && mappedVehicles[0].hisaabWeeks.length > 0) {
              setHisaabWeeks(mappedVehicles[0].hisaabWeeks);
            }
            if (mappedVehicles.length > 0) {
              setSelectedVehicleNumber(mappedVehicles[0].number);
            }
            if (notifs && notifs.length > 0) setNotifications(notifs.map(mapNotification));
            setLoginType('operator');
            backendSuccess = true;
          } catch (profileErr) {
            console.warn('Operator profile load failed, using demo data', profileErr);
          }
        } else {
          try {
            const driverProfile = await getDriverByPhone(cleanPhone);
            const hisaabs = await getDriverHisaabs(driverProfile.app_driver_id);
            const notifs = await fetchNotifications(driverProfile.app_driver_id, 'driver');
            const tkts = await getTickets(driverProfile.app_driver_id);

            setDriverUser(mapDriverToUser(driverProfile));
            setDriverVehicle(mapDriverToVehicle(driverProfile));
            setDriverRentalPlan(mapDriverToRentalPlan(driverProfile));
            if (hisaabs && hisaabs.length > 0) {
              setHisaabWeeks(hisaabs.map(mapHisaabToWeek));
            } else {
              setHisaabWeeks([]);
            }
            setNotifications((notifs || []).map(mapNotification));
            setTickets((tkts || []).map(mapTicket));
            setLoginType('driver');
            backendSuccess = true;
          } catch (profileErr) {
            console.warn('Driver profile load failed, using demo data', profileErr);
          }
        }
      } catch (backendErr) {
        console.warn('Backend auth failed, falling back to demo profiles', backendErr);
      }

      // Step 4: Fallback to DEMO_PROFILES if backend failed
      if (!backendSuccess) {
        if (matchedProfile) {
          setLoginType(matchedProfile.role);
          setDriverUser(matchedProfile.user);
          setHisaabWeeks(matchedProfile.weeks);
          if (matchedProfile.fleet) {
            setOperatorFleet(matchedProfile.fleet);
          }
          if (matchedProfile.vehicle) {
            setDriverVehicle(matchedProfile.vehicle);
          }
          if (matchedProfile.rentalPlan) {
            setDriverRentalPlan(matchedProfile.rentalPlan);
          }
          triggerToast(`Logged in as ${matchedProfile.name}`, 'info');
        } else {
          throw new Error('Profile does not exist. This mobile number is not registered with LetzRyd. Please contact your Fleet Manager or Support.');
        }
      } else {
        triggerToast(`Welcome! Logged in as ${inferredRole === 'operator' ? 'Fleet Operator' : 'Driver'}`, 'success');
      }

      setIsLoggedIn(true);
      setCurrentScreen('home');
    } catch (err: any) {
      console.error('OTP Verification Error:', err);
      triggerToast(err.message || 'Invalid OTP code. Please try again.', 'error');
    } finally {
      setIsVerifyingOtp(false);
      setIsLoadingProfile(false);
    }
  };

  // Admin: search for any partner by phone number (no OTP needed for lookup)
  const handleAdminSearch = async (query: string) => {
    const cleanQ = query.replace('+91', '').replace(/[\s-]/g, '').trim();
    setAdminSearchQuery(query);
    setAdminSearchResults([]);
    setAdminSearchError(null);
    if (!cleanQ || cleanQ.length < 5) return;
    setAdminSearchLoading(true);
    try {
      const [driverRes, opRes] = await Promise.all([
        getDriverByPhone(cleanQ).catch(() => null),
        getOperatorByPhone(cleanQ).catch(() => null),
      ]);

      const found: { name: string; phone: string; role: 'driver' | 'operator'; id: string; detail?: string }[] = [];

      // If user is an operator, add operator first
      if (opRes) {
        found.push({
          name: opRes.company_name || 'Fleet Operator',
          phone: opRes.phone || cleanQ,
          role: 'operator',
          id: opRes.app_operator_id,
          detail: opRes.total_vehicles ? `${opRes.total_vehicles} vehicles in fleet` : undefined,
        });
      }

      // If user is also/or a driver, add driver.
      // IMPORTANT: If phone already matched a real fleet operator (with vehicles),
      // suppress the duplicate driver entry — fleet owners appear in both tables,
      // but should only ever log in as Operator.
      const isFleetOperator = opRes && (opRes.total_vehicles || 0) > 0;
      if (driverRes && !isFleetOperator) {
        found.push({
          name: driverRes.full_name || 'Driver',
          phone: driverRes.phone || cleanQ,
          role: 'driver',
          id: driverRes.app_driver_id,
          detail: driverRes.vehicle_reg_number ? `Car: ${driverRes.vehicle_reg_number}` : undefined,
        });
      }

      if (found.length > 0) {
        setAdminSearchResults(found);
      } else {
        setAdminSearchError('No driver or operator found with this phone number.');
      }
    } catch {
      setAdminSearchError('Error searching. Check backend connection.');
    } finally {
      setAdminSearchLoading(false);
    }
  };

  // Admin: one-click login as any partner using backend OTP 1234 bypass (no Firebase)
  const handleAdminLoginAs = async (result: { name: string; phone: string; role: 'driver' | 'operator'; id: string }) => {
    setAdminLoginLoading(true);
    try {
      // Call backend OTP verify directly with master OTP 1234 and the explicit role requested
      await verifyOTPBackend(result.phone, '1234', result.role);
      setIsLoadingProfile(true);

      const targetRole = result.role;

      if (targetRole === 'operator') {
        const opProfile = await getOperatorByPhone(result.phone);
        const fleetData = await getOperatorFleet(opProfile.app_operator_id);
        const notifs = await fetchNotifications(opProfile.app_operator_id, 'operator');
        const opHisaabs = await getOperatorHisaabs(opProfile.app_operator_id).catch(() => []);

        setDriverUser(mapOperatorToUser(opProfile));

        const mappedVehicles: FleetVehicle[] = mapFleetDataToVehicles(fleetData);
        const mappedDrivers: FleetDriverItem[] = (fleetData?.drivers || []).map((d: any) => ({
          driverId: d.app_driver_id,
          driverCode: d.driver_code || `DRV-${d.app_driver_id}`,
          name: d.full_name || 'Driver',
          phone: d.phone || '',
          assignedVehicle: d.assigned_vehicle || 'Unassigned',
          vehicleModel: d.vehicle_model || 'Maruti Wagonr Tour H3 CNG',
          rentalPlan: d.rental_plan || 'Fixed',
          currentWeekOs: d.current_week_os || 0,
          status: d.status || 'active',
          hisaabCount: d.hisaab_count || 0
        }));

        setOperatorFleet({
          operatorCode: fleetData?.operator_code,
          operatorName: fleetData?.company_name,
          depositTotalRequired: fleetData?.deposit_total_req,
          depositPaidSoFar: fleetData?.deposit_paid,
          depositPending: fleetData?.deposit_pending,
          vehicles: mappedVehicles,
          drivers: mappedDrivers,
        });
        if (opHisaabs && opHisaabs.length > 0) {
          setHisaabWeeks(opHisaabs.map(mapHisaabToWeek));
        } else if (mappedVehicles.length > 0) {
          setHisaabWeeks(mappedVehicles[0].hisaabWeeks);
        }
        if (mappedVehicles.length > 0) {
          setSelectedVehicleNumber(mappedVehicles[0].number);
        }
        if (notifs?.length > 0) setNotifications(notifs.map(mapNotification));
        setLoginType('operator');
      } else {
        const driverProfile = await getDriverByPhone(result.phone);
        const hisaabs = await getDriverHisaabs(driverProfile.app_driver_id);
        const notifs = await fetchNotifications(driverProfile.app_driver_id, 'driver');
        const tkts = await getTickets(driverProfile.app_driver_id);
        setDriverUser(mapDriverToUser(driverProfile));
        setDriverVehicle(mapDriverToVehicle(driverProfile));
        setDriverRentalPlan(mapDriverToRentalPlan(driverProfile));
        if (hisaabs && hisaabs.length > 0) setHisaabWeeks(hisaabs.map(mapHisaabToWeek));
        setNotifications((notifs || []).map(mapNotification));
        setTickets((tkts || []).map(mapTicket));
        setLoginType('driver');
      }

      setPhoneInput(result.phone);
      setIsLoggedIn(true);
      setCurrentScreen('home');
      setAdminSearchOpen(false);
      setAdminSearchQuery('');
      setAdminSearchResults([]);
      triggerToast(`🔑 Admin: Logged in as ${result.name}`, 'success');
    } catch (err: any) {
      triggerToast(err.message || 'Failed to log in as partner', 'error');
    } finally {
      setAdminLoginLoading(false);
      setIsLoadingProfile(false);
    }
  };

  // Synchronize active authentication session to localStorage
  useEffect(() => {
    if (isLoggedIn) {
      try {
        localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({
          isLoggedIn: true,
          loginType,
          phoneInput,
          driverUser,
          driverVehicle,
          driverRentalPlan,
          operatorFleet,
          hisaabWeeks,
          currentScreen: currentScreen === 'settle' ? 'settle' : currentScreen,
        }));
      } catch (e) {
        console.warn('Could not save session:', e);
      }
    }
  }, [isLoggedIn, loginType, phoneInput, driverUser, driverVehicle, driverRentalPlan, operatorFleet, hisaabWeeks, currentScreen]);

  // Auto-refresh active operator fleet on mount or session restore to ensure live deduplicated data
  useEffect(() => {
    if (isLoggedIn && loginType === 'operator' && phoneInput) {
      const cleanPhone = phoneInput.replace('+91', '').replace(/[\s-]/g, '').trim();
      getOperatorByPhone(cleanPhone).then(opProfile => {
        if (opProfile?.app_operator_id) {
          getOperatorFleet(opProfile.app_operator_id).then(fleetData => {
            if (fleetData?.vehicles) {
              const mapped = mapFleetDataToVehicles(fleetData);
              setOperatorFleet(prev => ({
                ...prev,
                vehicles: mapped,
                depositTotalRequired: fleetData.deposit_total_req ?? prev.depositTotalRequired,
                depositPaidSoFar: fleetData.deposit_paid ?? prev.depositPaidSoFar,
                depositPending: fleetData.deposit_pending ?? prev.depositPending,
              }));
            }
          }).catch(console.warn);
        }
      }).catch(console.warn);
    }
  }, [isLoggedIn, loginType, phoneInput]);

  const handleLogout = () => {
    try {
      localStorage.removeItem(AUTH_STORAGE_KEY);
    } catch (e) {}
    setIsLoggedIn(false);
    setOtpSent(false);
    setPhoneInput('');
    setOtpInput('');
    setConfirmationResult(null);
    setCurrentScreen('home');
    setSosActivated(false);
    setDriverWeekIndex(0);
    setSelectedVehicleNumber(null);
    triggerToast('Signed out successfully', 'info');
  };

  const navigateTo = (screen: string) => {
    setPrevScreen(currentScreen);
    setCurrentScreen(screen);
    if (screen === 'settle') {
      setDriverWeekIndex(0);
      setOperatorWeekIndex(0);
    }
  };

  const goBack = () => {
    navigateTo(prevScreen);
  };

  const handleNewTicketSubmit = async (category: string, subject: string, description: string) => {
    const newTicketId = `TKT-2026-${Math.floor(1000 + Math.random() * 9000)}`;
    const newTkt: Ticket = {
      id: newTicketId,
      category,
      subject,
      description,
      status: 'open',
      priority: 'medium',
      date: new Date().toISOString().split('T')[0],
      response: null
    };

    // Try to submit to backend
    try {
      const actualUserId = (loginType === 'operator'
        ? (driverUser.app_operator_id || driverUser.app_driver_id)
        : (driverUser.app_driver_id || driverUser.app_operator_id)) || 1;
      const backendTicket = await apiCreateTicket(
        loginType,
        actualUserId,
        category,
        subject,
        description,
        'medium'
      );
      setTickets(prev => [backendTicket, ...prev]);
    } catch (err) {
      // Fallback to local state
      setTickets(prev => [newTkt, ...prev]);
    }

    setIsNewTicketOpen(false);
    triggerToast(t('ticket.submitted', 'Support ticket filed successfully!'), 'success');

    const newNotif: Notification = {
      id: `NOTIF-${Date.now()}`,
      icon: 'ReceiptIndianRupee',
      title: 'Ticket Lodged Successfully',
      message: `Support ticket queued for review.`,
      time: 'Just now',
      read: false
    };
    setNotifications(prev => [newNotif, ...prev]);
  };

  const handleSosTrigger = (timeStr: string) => {
    setSosActivated(true);
    setSosTime(timeStr);
    triggerToast('Emergency SOS Sent to LetzRyd Hub!', 'error');

    const emergencyNotif: Notification = {
      id: `NOTIF-${Date.now()}`,
      icon: 'FileWarning',
      title: 'SOS Emergency Registered',
      message: 'LetzRyd dispatcher team is matching coordinates.',
      time: 'Just now',
      read: false
    };
    setNotifications(prev => [emergencyNotif, ...prev]);
  };

  const handleCancelSos = () => {
    setSosActivated(false);
    setSosTime(null);
    triggerToast('SOS alert cancelled', 'info');
  };

  const handleReportIncident = (type: string, loc: string, drivable: boolean) => {
    triggerToast('Incident report logged with central dispatcher!', 'success');
  };

  const handleSelectVehicleForHisaab = async (number: string) => {
    setSelectedVehicleNumber(number);
    setOperatorVehicleWeekIndex(operatorWeekIndex);
    navigateTo('operatorVehicle');

    const cleanNum = number.replace(/\s+/g, '');
    const targetVeh = operatorFleet.vehicles.find(v => v.number.replace(/\s+/g, '') === cleanNum);
    if (targetVeh) {
      try {
        let hisaabs: any[] = [];
        if (targetVeh.driverId) {
          hisaabs = await getDriverHisaabs(targetVeh.driverId);
        }
        if (!hisaabs || hisaabs.length === 0) {
          hisaabs = await getVehicleHisaabs(targetVeh.number);
        }
        if (hisaabs && hisaabs.length > 0) {
          const mapped = hisaabs.map(mapHisaabToWeek);
          setOperatorFleet(prev => ({
            ...prev,
            vehicles: prev.vehicles.map(v => 
              v.number.replace(/\s+/g, '') === cleanNum
                ? { ...v, hisaabWeeks: mapped }
                : v
            )
          }));
        }
      } catch (err) {
        console.warn('Could not fetch driver hisaabs for vehicle', number, err);
      }
    }
  };

  const handleCopyUpiId = () => {
    navigator.clipboard.writeText(LETZRYD_UPI_ID)
      .then(() => triggerToast('UPI ID copied to clipboard!', 'success'))
      .catch(() => triggerToast(`UPI ID: ${LETZRYD_UPI_ID}`, 'info'));
  };

  const handleCopyReferralCode = () => {
    const code = 'LETZ' + driverUser.phone;
    navigator.clipboard.writeText(code)
      .then(() => triggerToast('Referral code copied!', 'success'))
      .catch(() => triggerToast(`Referral Code: ${code}`, 'info'));
  };

  const handleConfirmPayment = async (paidAmount?: number) => {
    // Determine effective paid amount (default to the current full due if not supplied)
    let effectivePaid = paidAmount;
    if (!effectivePaid || effectivePaid <= 0) {
      const currentH = hisaabWeeks[0];
      const isSettled = currentH?.paymentStatus === 'settled' || currentH?.status === 'settled';
      const hisaabDue = currentH ? (
        isSettled ? 0 : (currentH.toCollect !== undefined && currentH.toCollect !== null && currentH.toCollect > 0)
          ? currentH.toCollect
          : Math.max(0, currentH.currentWeekOs > 0 ? currentH.currentWeekOs : 0)
      ) : 0;
      const depDue = loginType === 'operator' ? (operatorFleet.depositPending || 0) : (driverUser.depositPending || 0);
      effectivePaid = Math.max(hisaabDue + depDue, 2850);
    }

    // 1. Immediately apply the payment to local state so UI updates instantly across Settle, Hisaab, and Home screens
    if (effectivePaid > 0) {
      if (loginType === 'driver') {
        let remainingCash = effectivePaid;

        // Clone and apply to hisaabWeeks
        const updatedWeeks = hisaabWeeks.map((hw) => {
          if (remainingCash <= 0) return hw;
          const isPayout = (hw.currentWeekOs || 0) < 0 || ((hw.toPay || 0) > 0 && (hw.toCollect || 0) <= 0);
          const rawDue = isPayout ? 0 : Math.max(0, hw.currentWeekOs > 0 ? hw.currentWeekOs : (hw.toCollect || 0));
          const prevPaid = hw.paidAmount || 0;
          const remDue = Math.max(0, rawDue - prevPaid);

          if (remDue > 0) {
            const payToThisWeek = Math.min(remDue, remainingCash);
            const newPaid = prevPaid + payToThisWeek;
            remainingCash -= payToThisWeek;
            const isSettled = newPaid >= rawDue;
            return {
              ...hw,
              paidAmount: newPaid,
              paymentStatus: (isSettled ? 'settled' : 'partial') as 'settled' | 'partial',
              status: (isSettled ? 'settled' : 'unpaid') as 'settled' | 'unpaid',
              currentWeekOs: Math.max(0, rawDue - newPaid),
              toCollect: Math.max(0, rawDue - newPaid),
            };
          }
          return hw;
        });

        // Pay pending security deposit if cash remains
        let newDepPending = driverUser.depositPending || 0;
        let newDepPaid = driverUser.depositPaidSoFar || 0;
        if (remainingCash > 0 && newDepPending > 0) {
          const depCredit = Math.min(remainingCash, newDepPending);
          newDepPending = Math.max(0, newDepPending - depCredit);
          newDepPaid += depCredit;
          remainingCash -= depCredit;
        }

        const newCumulativeOwed = Math.max(0, (driverUser.cumulativeOwed || 0) - effectivePaid);

        const updatedDriverUser: User = {
          ...driverUser,
          cumulativeOwed: newCumulativeOwed,
          depositPending: newDepPending,
          depositPaidSoFar: newDepPaid,
        };

        setHisaabWeeks(updatedWeeks);
        setDriverUser(updatedDriverUser);

        // Persist to localStorage immediately
        try {
          localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({
            isLoggedIn: true,
            loginType,
            phoneInput,
            driverUser: updatedDriverUser,
            driverVehicle,
            driverRentalPlan,
            operatorFleet,
            hisaabWeeks: updatedWeeks,
            currentScreen: 'settle',
          }));
        } catch (e) {}
      } else {
        // Operator payment cascade
        let remainingCash = effectivePaid;
        const updatedVehicles = operatorFleet.vehicles.map(v => {
          if (remainingCash <= 0 || v.currentWeekOs <= 0) return v;
          const payToV = Math.min(v.currentWeekOs, remainingCash);
          remainingCash -= payToV;
          return {
            ...v,
            currentWeekOs: Math.max(0, v.currentWeekOs - payToV),
          };
        });

        let newDepPending = operatorFleet.depositPending || 0;
        let newDepPaid = operatorFleet.depositPaidSoFar || 0;
        if (remainingCash > 0 && newDepPending > 0) {
          const depCredit = Math.min(remainingCash, newDepPending);
          newDepPending = Math.max(0, newDepPending - depCredit);
          newDepPaid += depCredit;
          remainingCash -= depCredit;
        }

        const updatedFleet = {
          ...operatorFleet,
          vehicles: updatedVehicles,
          depositPending: newDepPending,
          depositPaidSoFar: newDepPaid,
        };

        setOperatorFleet(updatedFleet);
        try {
          localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({
            isLoggedIn: true,
            loginType,
            phoneInput,
            driverUser,
            driverVehicle,
            driverRentalPlan,
            operatorFleet: updatedFleet,
            hisaabWeeks,
            currentScreen: 'settle',
          }));
        } catch (e) {}
      }
    }

    // 2. Also query backend API to sync with DB if reachable
    try {
      if (loginType === 'driver') {
        const driverProfile = await getDriverByPhone(driverUser.phone).catch(() => null);
        if (driverProfile) {
          const hisaabs = await getDriverHisaabs(driverProfile.app_driver_id).catch(() => null);
          setDriverUser(mapDriverToUser(driverProfile));
          setDriverVehicle(mapDriverToVehicle(driverProfile));
          setDriverRentalPlan(mapDriverToRentalPlan(driverProfile));
          if (hisaabs && hisaabs.length > 0) setHisaabWeeks(hisaabs.map(mapHisaabToWeek));
        }
      } else if (loginType === 'operator') {
        const opProfile = await getOperatorByPhone(operatorUser.phone).catch(() => null);
        if (opProfile) {
          const [fleet, hisaabs] = await Promise.all([
            getOperatorFleet(opProfile.app_operator_id).catch(() => null),
            getOperatorHisaabs(opProfile.app_operator_id).catch(() => null),
          ]);
          setOperatorUser(mapOperatorToUser(opProfile));
          if (fleet) setOperatorFleet(fleet);
          if (hisaabs && hisaabs.length > 0) setOperatorHisaabs(hisaabs.map(mapHisaabToWeek));
        }
      }
    } catch (err) {
      console.warn('[handleConfirmPayment] Re-fetch error:', err);
    }

    triggerToast(t('payment.noted', 'Payment verified! Balance updated.'), 'success');
    navigateTo('settle');
  };

  // Auto-verify when Cashfree redirects back with ?order_id=...
  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search);
    const orderId = searchParams.get('order_id');
    if (orderId) {
      setIsLoggedIn(true);
      setCurrentScreen('settle');
      window.history.replaceState({}, document.title, window.location.pathname);
      const verifyUrls = [
        `${BACKEND_URL}/api/payments/verify/${orderId}`,
        `/api/payments/verify/${orderId}`,
        `http://127.0.0.1:8000/api/payments/verify/${orderId}`,
        `http://localhost:8000/api/payments/verify/${orderId}`,
      ].filter(Boolean);

      const doVerify = async () => {
        let isVerified = false;
        let verifiedAmt = 0;
        for (const url of verifyUrls) {
          try {
            const res = await fetch(url);
            if (res.ok) {
              const data = await res.json();
              if (data?.is_success || data?.status === 'SUCCESS') {
                verifiedAmt = Number(data?.amount || data?.paid_amount || data?.data?.[0]?.payment_amount || 0);
                isVerified = true;
                break;
              }
            }
          } catch (e) {
            console.warn('[doVerify] Attempt failed:', url, e);
          }
        }
        if (isVerified && verifiedAmt > 0) {
          await handleConfirmPayment(verifiedAmt);
        }
        setIsLoggedIn(true);
        setCurrentScreen('settle');
      };
      doVerify();
    }
  }, []);

  const handleUpdateContact = (details: { emergencyContact: string; emergencyName?: string; emergencyRelation?: string; emergencyPhone?: string; address: string }) => {
    setDriverUser(prev => ({
      ...prev,
      emergencyContact: details.emergencyContact,
      emergencyName: details.emergencyName || prev.emergencyName,
      emergencyRelation: details.emergencyRelation || prev.emergencyRelation,
      emergencyPhone: details.emergencyPhone || prev.emergencyPhone,
      address: details.address
    }));
    triggerToast(t('profile.saved', 'Profile updated successfully!'), 'success');
  };

  const handleMarkAllNotificationsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    triggerToast('All notifications marked as read', 'success');
  };

  const selectedVehicleObj = selectedVehicleNumber
    ? operatorFleet.vehicles.find(v => v.number.replace(/\s+/g, '') === selectedVehicleNumber.replace(/\s+/g, '')) || operatorFleet.vehicles.find(v => v.number === selectedVehicleNumber) || null
    : null;

  const initials = driverUser.initials || (loginType === 'operator' ? 'OP' : 'DR');
  const userName = driverUser.name || (loginType === 'operator' ? 'Fleet Operator' : 'Driver');
  const isFleetDriver = Boolean(driverUser.isFleetDriver || driverUser.operatorName);
  const isFleetManaged = isFleetDriver && loginType === 'driver';
  const hasHisaabData = hisaabWeeks.length > 0;
  const activeWeek = hasHisaabData ? hisaabWeeks[0] : (loginType === 'operator' ? (operatorFleet.vehicles[0]?.hisaabWeeks[0] || null) : null);
  const prevWeek = hasHisaabData && hisaabWeeks.length > 1 ? hisaabWeeks[1] : (loginType === 'operator' ? (operatorFleet.vehicles[0]?.hisaabWeeks[1] || null) : null);

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
    <div className="min-h-screen bg-bg flex items-center justify-center py-0 md:py-6 px-0 md:px-4 font-sans select-none">

      {/* MOBILE PHONE APP CONTAINER */}
      <div className="w-full max-w-[375px] h-screen md:h-[780px] bg-bg border-0 md:border md:border-border rounded-none md:rounded-[40px] shadow-2xl relative flex flex-col overflow-hidden text-text">
        {isLoadingProfile && (
          <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(10,15,30,0.85)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', zIndex: 9999 }}>
            <div style={{ color: '#fff', fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>Loading your profile...</div>
            <div style={{ width: 48, height: 48, border: '4px solid rgba(255,255,255,0.2)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
          </div>
        )}

        {/* Toast Container — offset below header (top-16) to prevent control collision */}
        <div className="absolute top-16 inset-x-4 z-50 pointer-events-none flex flex-col gap-2 items-center">
          <AnimatePresence>
            {toast && (
              <Toast
                message={toast.message}
                type={toast.type}
                onClose={() => setToast(null)}
              />
            )}
          </AnimatePresence>
        </div>

        <AnimatePresence mode="wait">
          {!isLoggedIn ? (
            /* =========================================================================
               MOBILE OTP LOGIN SCREEN (BRANDING + 5-LANGUAGE SELECTOR)
               ========================================================================= */
            <motion.div
              key="login"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 flex flex-col bg-primary overflow-hidden"
            >
              {/* Top branding area — fills upper navy portion with balanced spacing */}
              <div className="flex-1 flex flex-col items-center justify-center px-6 py-6 gap-4 text-center bg-gradient-to-b from-[#0A1650] to-[#081242]">
                <img
                  src="https://letzryd.com/replica-assets/letzryd-long-png-logo-Aq2o3DNOw1i2kBMB-7ab04eaa76.png"
                  alt="LetzRyd logo"
                  className="h-16 max-w-[210px] w-auto object-contain filter brightness-0 invert drop-shadow-sm transition-transform duration-200 hover:scale-105"
                  referrerPolicy="no-referrer"
                />
                <div className="space-y-0.5">
                  <h1 className="font-sans text-lg font-extrabold text-white tracking-tight leading-snug">
                    {t('app.title', 'LetzRyd Portal')}
                  </h1>
                  <p className="font-sans text-xs font-medium text-white/80">
                    {t('app.subtitle', 'Drive in the Future of Urban Mobility.')}
                  </p>
                </div>

                {/* 5-Language selector pills */}
                <div className="flex flex-wrap items-center justify-center gap-1.5 pt-1">
                  {(['en', 'hi', 'mr', 'te', 'kn'] as Language[]).map((lang) => (
                    <button
                      key={lang}
                      onClick={() => handleLanguageChange(lang)}
                      className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer shadow-xs ${
                        language === lang
                          ? 'bg-white text-primary font-bold shadow-md'
                          : 'bg-white/15 text-white/85 hover:bg-white/25 backdrop-blur-xs'
                      }`}
                    >
                      {lang === 'en' ? 'English' : lang === 'hi' ? 'हिंदी' : lang === 'mr' ? 'मराठी' : lang === 'te' ? 'తెలుగు' : 'ಕನ್ನಡ'}
                    </button>
                  ))}
                </div>
              </div>

              {/* White form card — anchored seamlessly to bottom */}
              <div className="bg-bg rounded-t-[28px] px-6 pt-6 pb-8 space-y-4 shadow-2xl shrink-0 border-t border-white/20">
                <div id="recaptcha-container"></div>

                {!otpSent ? (
                  <form key="phone-form" onSubmit={handleSendOtp} className="space-y-3">
                    <div className="flex flex-col gap-1.5">
                      <label className="font-sans text-xs font-semibold text-text-muted">
                        {t('login.enterPhone', 'Enter 10-Digit Mobile Number')}
                      </label>
                      <div className="flex items-center gap-2">
                        <span className="h-11 px-3 rounded-lg border border-border bg-border font-sans text-sm font-bold text-text flex items-center shrink-0">
                          +91
                        </span>
                        <input
                          type="tel"
                          maxLength={10}
                          value={phoneInput}
                          onChange={(e) => {
                            setPhoneInput(e.target.value);
                            if (phoneError) setPhoneError(null);
                          }}
                          className={`h-11 w-full rounded-lg border bg-surface px-3.5 font-sans text-sm font-medium text-text outline-none transition-all ${
                            phoneError ? 'border-red-500 ring-2 ring-red-500/20 bg-red-50/5 dark:bg-red-950/10' : 'border-border'
                          }`}
                          placeholder="9876543210"
                          required
                          disabled={isSendingOtp}
                          autoFocus
                        />
                      </div>
                    </div>

                    {phoneError && (
                      <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-600 dark:text-red-400 text-xs font-semibold flex items-start gap-2 animate-in fade-in slide-in-from-top-1 duration-200">
                        <span className="text-sm shrink-0">⚠️</span>
                        <span>{phoneError}</span>
                      </div>
                    )}

                    <button
                      type="submit"
                      disabled={isSendingOtp}
                      className="w-full py-3.5 rounded-xl bg-primary hover:bg-primary-hover font-sans text-sm font-semibold text-white cursor-pointer transition-colors shadow-sm disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                      {isSendingOtp ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          Checking Account...
                        </>
                      ) : (
                        t('login.sendOtp', 'Get OTP')
                      )}
                    </button>
                  </form>
                ) : (
                  <form key="otp-form" onSubmit={handleVerifyOtp} className="space-y-3">
                    <div className="flex flex-col gap-1.5">
                      <label className="font-sans text-xs font-semibold text-text-muted">
                        {t('login.enterOtp', 'Enter OTP Code')}
                      </label>
                      <input
                        type="text"
                        maxLength={6}
                        value={otpInput}
                        onChange={(e) => setOtpInput(e.target.value)}
                        className="h-14 w-full rounded-xl border border-border bg-surface text-center font-mono text-2xl font-bold tracking-[0.5em] text-primary outline-none"
                        placeholder="••••••"
                        required
                        disabled={isVerifyingOtp}
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={isVerifyingOtp}
                      className="w-full py-3.5 rounded-xl bg-primary hover:bg-primary-hover font-sans text-sm font-semibold text-white cursor-pointer transition-colors shadow-sm disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                      {isVerifyingOtp ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          Verifying...
                        </>
                      ) : (
                        t('login.verifyOtp', 'Verify & Enter Portal')
                      )}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        // Cancel any in-flight OTP request so it can't snap back
                        otpRequestCancelledRef.current = true;
                        setIsSendingOtp(false);
                        setOtpSent(false);
                        setOtpInput('');
                        setConfirmationResult(null);
                        setPhoneError(null);
                        // Clean up reCAPTCHA
                        if (window.recaptchaVerifier) {
                          try { window.recaptchaVerifier.clear(); } catch (e) {}
                          window.recaptchaVerifier = null;
                        }
                        const rcContainer = document.getElementById('recaptcha-container');
                        if (rcContainer) rcContainer.innerHTML = '';
                      }}
                      className="w-full text-center text-xs font-medium text-text-muted hover:text-primary cursor-pointer"
                    >
                      ← {t('login.changeNumber', 'Change Mobile Number')}
                    </button>
                  </form>
                )}

                {/* Admin: Live Partner Search Panel */}
                <div className="pt-3 border-t border-border space-y-2 text-left relative">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider block">
                      Admin: Login as Any Partner
                    </span>
                    <button
                      type="button"
                      onClick={() => { setAdminSearchOpen(v => !v); setAdminSearchQuery(''); setAdminSearchResults([]); setAdminSearchError(null); }}
                      className="text-[10px] font-semibold text-primary hover:underline cursor-pointer"
                    >
                      {adminSearchOpen ? 'Hide ▲' : 'Open ▼'}
                    </button>
                  </div>

                  {adminSearchOpen && (
                    <div className="space-y-2">
                      {/* Phone search input */}
                      <div className="relative">
                        <input
                          type="tel"
                          maxLength={10}
                          value={adminSearchQuery}
                          onChange={e => handleAdminSearch(e.target.value)}
                          placeholder="Type partner phone number..."
                          className="h-9 w-full rounded-lg border border-border bg-surface px-3 text-sm font-medium text-text outline-none focus:border-primary/60 transition-all"
                          autoFocus
                        />
                        {adminSearchLoading && (
                          <div className="absolute right-2.5 top-2.5 w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                        )}
                      </div>

                      {/* Search results list */}
                      {adminSearchResults.length > 0 && (
                        <div className="space-y-2">
                          {adminSearchResults.map((res) => (
                            <div key={`${res.role}-${res.id}`} className="flex items-center justify-between p-2.5 rounded-xl bg-primary/5 border border-primary/20">
                              <div>
                                <div className="font-bold text-sm text-text">{res.name}</div>
                                <div className="text-[11px] text-text-muted mt-0.5 flex items-center gap-1.5 flex-wrap">
                                  <span className={`font-bold px-1.5 py-0.5 rounded text-[9px] uppercase ${res.role === 'operator' ? 'bg-blue-500/10 text-blue-600' : 'bg-green-500/10 text-green-600'}`}>
                                    {res.role}
                                  </span>
                                  <span>{res.phone}</span>
                                  {res.detail && (
                                    <span className="text-[10px] text-primary/80 font-medium">({res.detail})</span>
                                  )}
                                </div>
                              </div>
                              <button
                                type="button"
                                disabled={adminLoginLoading}
                                onClick={() => handleAdminLoginAs(res)}
                                className="px-3 py-1.5 rounded-lg bg-primary text-white text-xs font-semibold hover:bg-primary-hover transition-colors disabled:opacity-50 flex items-center gap-1.5 cursor-pointer shrink-0 ml-2"
                              >
                                {adminLoginLoading ? (
                                  <><div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" /> Loading...</>
                                ) : (
                                  <>Login as {res.role === 'operator' ? 'Operator' : 'Driver'} →</>
                                )}
                              </button>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* No result error */}
                      {adminSearchError && !adminSearchLoading && (
                        <div className="text-[11px] text-red-500 font-medium px-1">{adminSearchError}</div>
                      )}

                      {/* Hint */}
                      {adminSearchResults.length === 0 && !adminSearchError && !adminSearchLoading && adminSearchQuery.length >= 5 && (
                        <div className="text-[11px] text-text-muted px-1">Searching live database...</div>
                      )}
                      {adminSearchQuery.length === 0 && (
                        <div className="text-[11px] text-text-muted px-1">Enter a 10-digit phone to find any driver or operator from the live DB.</div>
                      )}
                    </div>
                  )}
                </div>

              </div>
            </motion.div>
          ) : (
            /* =========================================================================
               MOBILE APP SHELL (TOP NAV BAR + SCROLLABLE VIEWPORT + BOTTOM NAV BAR)
               ========================================================================= */
            <motion.div
              key="shell"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 flex flex-col h-full overflow-hidden"
            >
              {/* Header */}
              <header className="h-14 border-b border-border bg-surface flex items-center justify-between px-4.5 sticky top-0 z-40 shrink-0">
                <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigateTo('home')}>
                  <img 
                    src={logoIcon} 
                    alt="LetzRyd icon logo" 
                    className="h-7 w-auto object-contain"
                  />
                </div>

                <div className="flex items-center gap-2">
                  {/* 5-Language Selector Dropdown Pill */}
                  <select
                    value={language}
                    onChange={(e) => handleLanguageChange(e.target.value as Language)}
                    className="h-7 px-1.5 rounded border border-border bg-bg text-[10px] font-bold text-primary cursor-pointer outline-none"
                  >
                    <option value="en">English</option>
                    <option value="hi">हिंदी</option>
                    <option value="mr">मराठी</option>
                    <option value="te">తెలుగు</option>
                    <option value="kn">ಕನ್ನಡ</option>
                  </select>

                  {/* Notification Bell */}
                  <button
                    onClick={() => setIsNotifOpen(true)}
                    className="relative p-1.5 rounded-lg border border-border bg-surface text-text-muted cursor-pointer hover:border-primary transition-all"
                  >
                    <Bell className="h-4 w-4" />
                    {notifications.some(n => !n.read) && (
                      <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-red-600" />
                    )}
                  </button>

                  {/* Profile Initials */}
                  <div 
                    onClick={() => navigateTo('profile')}
                    className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-xs font-bold text-white cursor-pointer hover:opacity-90 transition-all"
                  >
                    {initials}
                  </div>

                  {/* Sign Out */}
                  <button 
                    onClick={handleLogout}
                    className="p-1.5 rounded-lg border border-border bg-surface text-text-muted hover:text-red-600 cursor-pointer hover:border-red-200 transition-all"
                  >
                    <LogOut className="h-4 w-4" />
                  </button>
                </div>
              </header>

              {/* Viewport Content */}
              <main className="flex-1 overflow-y-auto p-4 pb-24 space-y-4 no-scrollbar">
                <AnimatePresence mode="wait">
                  {currentScreen === 'home' && (
                    <motion.div
                      key="home"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="space-y-4"
                    >
                      {/* 1. Driver Greeting Banner (100% Symmetrically Aligned) */}
                      <div className="bg-surface border border-border/80 rounded-2xl p-3.5 shadow-xs font-sans text-xs text-left space-y-0.5">
                        <div className="flex items-center justify-between">
                          <h2 className="font-extrabold text-text text-sm flex items-center gap-1.5">
                            {t('home.greeting', 'Hi')}, {userName.split(' ')[0]} 👋
                          </h2>
                          {loginType === 'driver' && (
                            !driverVehicle?.number || driverVehicle.number === 'Unassigned' || driverVehicle.number.toLowerCase() === 'unassigned' || !driverVehicle.number.trim() ? (
                              <span className="bg-amber-100 text-amber-800 border border-amber-300 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
                                {t('vehicle.noVehicleAssigned', 'No Vehicle Assigned')}
                              </span>
                            ) : (
                              <span className="font-mono text-[10.5px] font-bold text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded-md">
                                {driverVehicle.number}
                              </span>
                            )
                          )}
                        </div>
                        <p className="text-text-muted text-[11px]">
                          {t('home.summary', "Here's your weekly settlement summary")}
                        </p>
                      </div>

                      {/* 2. THIS WEEK HISAAB & INCENTIVE GOAL (HERO CLICKABLE TILE) */}
                      {loginType === 'driver' ? (
                        isFleetDriver && !activeWeek ? (
                          <div className="bg-surface border border-border/80 rounded-2xl p-4 shadow-xs text-left space-y-3 font-sans">
                            <div className="flex items-center gap-3 border-b border-border/60 pb-3">
                              <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
                                <ShieldCheck className="w-5 h-5" />
                              </div>
                              <div className="min-w-0">
                                <h3 className="font-extrabold text-sm text-text">{t('home.fleetManagedVehicle', 'Fleet Managed Vehicle')}</h3>
                                <p className="text-[11px] text-text-muted truncate">
                                  {t('common.operator', 'Operator')}: <strong className="text-text">{driverUser.operatorName || 'Fleet Operator'}</strong>
                                </p>
                              </div>
                            </div>
                            <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl space-y-1">
                              <div className="flex items-center gap-1.5 text-xs font-bold text-amber-700">
                                <Info className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                                <span>{t('home.fleetManagedMsg', 'Payments handled by Fleet Operator')}</span>
                              </div>
                              <p className="text-[10.5px] text-text-muted leading-relaxed">
                                Vehicle managed by Operator <strong>{driverUser.operatorName || 'Fleet Operator'}</strong>. Weekly settlements and statements are handled directly by your fleet manager.
                              </p>
                            </div>
                          </div>
                        ) : activeWeek ? (
                        <div
                          onClick={() => { setDriverWeekIndex(0); navigateTo('hisaab'); }}
                          className="bg-surface border border-border/80 hover:border-primary/50 rounded-2xl p-3.5 shadow-xs text-left space-y-3 font-sans cursor-pointer transition-all hover:shadow-md group overflow-hidden"
                        >
                          {/* Header: Week Hisaab Title & Inline Week # Code */}
                          <div className="border-b border-border/60 pb-2 space-y-1">
                            <div className="flex justify-between items-center">
                              <span className="font-sans text-[11px] font-bold text-text uppercase tracking-wider group-hover:text-primary transition-colors">
                                {t('home.thisWeekHisaab', 'THIS WEEK HISAAB')}
                              </span>
                              <span className="text-[10px] font-semibold text-text-muted font-mono bg-bg px-2 py-0.5 rounded-md border border-border/50">
                                {t('home.week', 'Week')} #{activeWeek.weekNumber} • {activeWeek.hisaabNumber}
                              </span>
                            </div>

                            <div className="flex items-center gap-1 text-[10px] font-medium text-text-muted whitespace-nowrap">
                              <Clock className="w-3 h-3 text-text-muted shrink-0" />
                              <span>{t('hisaab.lastUpdated', 'Last Updated')}:</span>
                              <span className="font-mono text-text font-semibold whitespace-nowrap">{formatTimestamp(activeWeek.lastRefreshedTime)}</span>
                            </div>
                          </div>

                          {/* WHAT YOU MADE HERO FOR DRIVER */}
                          {(() => {
                            const grossFares = (activeWeek.grossEarnings && activeWeek.grossEarnings > 0)
                              ? activeWeek.grossEarnings
                              : ((activeWeek.platforms?.uber?.revenue || 0) + (activeWeek.platforms?.ola?.revenue || 0) + (activeWeek.platforms?.rapido?.revenue || 0) + (activeWeek.platforms?.uber?.toll || 0) + (activeWeek.platforms?.ola?.toll || 0) + (activeWeek.platforms?.rapido?.toll || 0));
                            const totalTrips = (activeWeek.completedTrips || 0) || ((activeWeek.platforms?.uber?.trips || 0) + (activeWeek.platforms?.ola?.trips || 0) + (activeWeek.platforms?.rapido?.trips || 0));

                            return (
                              <div className="flex justify-between items-center gap-2 pt-0.5">
                                <div>
                                  <div className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">
                                    {t('home.whatYouMade', 'What You Made')}
                                  </div>
                                  <div className="text-[9px] text-text-dim">
                                    {t('home.grossTripEarnings', 'Gross Road Earnings')}
                                  </div>
                                  <div className="font-sans text-2xl font-black text-green mt-1 font-mono">
                                    +₹{grossFares.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                  </div>
                                  <span className="text-[10px] text-text-muted font-medium mt-0.5 block">
                                    {totalTrips} {t('home.rides', 'Rides')} • {activeWeek.activeDays ?? 0} {t('home.daysActive', 'Days Active')}
                                  </span>
                                </div>
                                <span className="flex items-center gap-1 font-sans text-[10px] font-bold text-green bg-green-light px-2.5 py-1 rounded-full shrink-0 whitespace-nowrap border border-green-200/50">
                                  <TrendingUp className="w-3 h-3 text-green" />
                                  {activeWeek.growthPct ? `${activeWeek.growthPct > 0 ? '+' : ''}${activeWeek.growthPct}% ${t('home.vsLastWeek', 'vs last week')}` : t('home.currentWeek', 'Current Week')}
                                </span>
                              </div>
                            );
                          })()}

                          {/* Merged Weekly Incentive Goal Progress Section */}
                          {(() => {
                            const target = driverUser.weeklyIncentiveTargetTrips || 1;
                            const completed = driverUser.completedTripsThisWeek || (activeWeek ? ((activeWeek.completedTrips || 0) || ((activeWeek.platforms?.uber?.trips || 0) + (activeWeek.platforms?.ola?.trips || 0) + (activeWeek.platforms?.rapido?.trips || 0))) : 0);
                            const progressPct = Math.min(100, Math.max(0, (completed / target) * 100));
                            const remaining = Math.max(0, target - completed);

                            return (
                              <div className="border-t border-border/60 pt-2.5 space-y-1.5 font-sans w-full overflow-hidden">
                                <div className="flex justify-between items-center text-xs gap-2">
                                  <span className="font-bold text-text flex items-center gap-1.5 text-[11px] shrink-0">
                                    <Target className="w-3.5 h-3.5 text-primary shrink-0" />
                                    <span>{t('home.incentiveTracker', 'Weekly Incentive Goal')}</span>
                                  </span>
                                  <span className="font-bold text-primary text-[11px] bg-primary/10 px-2 py-0.5 rounded-md shrink-0 whitespace-nowrap">
                                    ₹{driverUser.weeklyIncentiveReward.toLocaleString('en-IN')} {t('home.bonus', 'Bonus')}
                                  </span>
                                </div>

                                <div className="w-full bg-border/80 rounded-full h-2 overflow-hidden p-0.5">
                                  <div
                                    className="bg-primary h-1.5 rounded-full transition-all duration-500 max-w-full"
                                    style={{ width: `${progressPct}%` }}
                                  />
                                </div>

                                <div className="flex flex-wrap items-center justify-between gap-1 text-[10px] text-text-muted leading-tight">
                                  <span className="text-[10px] font-medium text-text-muted shrink-0">
                                    {completed > 0 ? `${completed} / ${target} trips` : `0 / ${target} trips`}
                                  </span>
                                  <p className="font-sans text-[10px] text-text-muted text-right ml-auto leading-tight break-words">
                                    {remaining > 0 ? (
                                      <>
                                        <strong className="text-text font-bold whitespace-nowrap">{remaining} {t('home.tripsRemaining', 'trips remaining')}</strong>{' '}
                                        <span className="text-text-muted">{t('home.toUnlockBonus', `to unlock ₹${driverUser.weeklyIncentiveReward.toLocaleString('en-IN')} bonus`)}</span>
                                      </>
                                    ) : (
                                      <span className="text-green font-bold">🎉 {t('home.goalAchieved', 'Incentive Goal Achieved!')}</span>
                                    )}
                                  </p>
                                </div>
                              </div>
                            );
                          })()}
                        </div>
                        ) : null
                      ) : (
                        <div
                          onClick={() => navigateTo('hisaab')}
                          className="bg-surface border border-border/80 hover:border-primary/50 rounded-2xl p-3.5 shadow-xs text-left space-y-3 font-sans cursor-pointer transition-all hover:shadow-md group overflow-hidden"
                        >
                          <div className="flex justify-between items-center border-b border-border/60 pb-2.5">
                            <span className="font-sans text-[11px] font-bold text-text uppercase tracking-wider group-hover:text-primary transition-colors">
                              {t('home.thisWeekFleetHisaab', 'THIS WEEK FLEET HISAAB')}
                            </span>
                            <span className="text-[10px] font-semibold text-text-muted font-mono bg-bg px-2 py-0.5 rounded-md border border-border/50">
                              {t('home.week', 'Week')} #{activeWeek ? activeWeek.weekNumber : 40} • {activeWeek?.hisaabNumber || operatorFleet.operatorCode || 'FLEET'}
                            </span>
                          </div>

                          {/* WHAT FLEET MADE HERO FOR OPERATOR */}
                          {(() => {
                            const grossFares = (activeWeek?.grossEarnings && activeWeek.grossEarnings > 0)
                              ? activeWeek.grossEarnings
                              : (activeWeek ? ((activeWeek.platforms?.uber?.revenue || 0) + (activeWeek.platforms?.ola?.revenue || 0) + (activeWeek.platforms?.rapido?.revenue || 0) + (activeWeek.platforms?.uber?.toll || 0) + (activeWeek.platforms?.ola?.toll || 0) + (activeWeek.platforms?.rapido?.toll || 0)) : (operatorFleet?.cw_fleet_gross_earnings || 0));
                            const totalTrips = activeWeek ? ((activeWeek.platforms?.uber?.trips || 0) + (activeWeek.platforms?.ola?.trips || 0) + (activeWeek.platforms?.rapido?.trips || 0) || (activeWeek as any).completedTrips || 0) : (operatorFleet?.cw_fleet_trips || 0);
                            const totalVehicles = operatorFleet.vehicles.length || operatorFleet.totalVehicles || 0;

                            return (
                              <div className="flex justify-between items-center gap-2 pt-0.5">
                                <div>
                                  <div className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">
                                    {t('home.whatFleetMade', 'What Your Fleet Made')}
                                  </div>
                                  <div className="text-[9px] text-text-dim">
                                    {t('home.grossTripEarnings', 'Gross Road Earnings')}
                                  </div>
                                  <div className="font-sans text-2xl font-black text-green mt-1 font-mono">
                                    +₹{grossFares.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                  </div>
                                  <span className="text-[10px] text-text-muted font-medium mt-0.5 block">
                                    {totalTrips} {t('home.ridesAcross', 'Rides across')} {totalVehicles} {t('home.cars', 'Cars')}
                                  </span>
                                </div>
                                <span className="flex items-center gap-1 font-sans text-[10px] font-bold text-green bg-green-light px-2.5 py-1 rounded-full shrink-0 whitespace-nowrap border border-green-200/50">
                                  <TrendingUp className="w-3 h-3 text-green" />
                                  {activeWeek?.growthPct ? `${activeWeek.growthPct > 0 ? '+' : ''}${activeWeek.growthPct}% ${t('home.vsLastWeek', 'vs last week')}` : t('home.currentWeek', 'Current Week')}
                                </span>
                              </div>
                            );
                          })()}
                        </div>
                      )}

                      {/* 3. 4-STAT KPI INDICATOR STRIP (SYMMETRIC) */}
                      {loginType === 'driver' ? (
                        <div className="bg-surface border border-border/80 rounded-2xl p-3.5 shadow-xs font-sans">
                          <div className="grid grid-cols-4 divide-x divide-border/70 text-center">
                            <div className="px-1">
                              <p className="font-sans text-base font-black text-text leading-none">{activeWeek?.activeDays ?? 0}</p>
                              <p className="font-sans text-[9px] font-bold text-text-muted uppercase tracking-tight mt-1.5">{t('home.daysActive', 'Days Active')}</p>
                            </div>
                            <div className="px-1">
                              <p className="font-sans text-base font-black text-text leading-none">
                                {activeWeek ? ((activeWeek.completedTrips || 0) || ((activeWeek.platforms?.uber?.trips || 0) + (activeWeek.platforms?.ola?.trips || 0) + (activeWeek.platforms?.rapido?.trips || 0))) : (driverUser.completedTripsThisWeek || 0)}
                              </p>
                              <p className="font-sans text-[9px] font-bold text-text-muted uppercase tracking-tight mt-1.5">{t('home.trips', 'Trips')}</p>
                            </div>
                            <div className="px-1">
                              <p className="font-sans text-base font-black text-text leading-none">
                                {activeWeek?.totalKm ? Math.round(activeWeek.totalKm).toLocaleString('en-IN') : (activeWeek?.gps?.totalGpsKm ? Math.round(activeWeek.gps.totalGpsKm).toLocaleString('en-IN') : '0')}
                              </p>
                              <p className="font-sans text-[9px] font-bold text-text-muted uppercase tracking-tight mt-1.5">{t('home.totalKm', 'Total KMs')}</p>
                            </div>
                            <div className="px-1">
                              <p className="font-sans text-base font-black text-green leading-none">
                                {activeWeek?.gps?.deadMilePct != null ? `${activeWeek.gps.deadMilePct}%` : '0%'}
                              </p>
                              <p className="font-sans text-[9px] font-bold text-text-muted uppercase tracking-tight mt-1.5">{t('home.deadMilesPct', 'Dead Miles %')}</p>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="bg-surface border border-border/80 rounded-2xl p-3.5 shadow-xs font-sans">
                          <div className="grid grid-cols-4 divide-x divide-border/70 text-center">
                            <div className="px-1">
                              <p className="font-sans text-base font-black text-text leading-none">
                                {activeWeek ? ((activeWeek.platforms?.uber?.trips || 0) + (activeWeek.platforms?.ola?.trips || 0) + (activeWeek.platforms?.rapido?.trips || 0) || (activeWeek as any).completedTrips || 0) : 1150}
                              </p>
                              <p className="font-sans text-[9px] font-bold text-text-muted uppercase tracking-tight mt-1.5">{t('home.trips', 'Trips')}</p>
                            </div>
                            <div className="px-1">
                              <p className="font-sans text-base font-black text-text leading-none">
                                {activeWeek?.totalKm ? Math.round(activeWeek.totalKm).toLocaleString('en-IN') : (activeWeek?.gps?.totalGpsKm ? Math.round(activeWeek.gps.totalGpsKm).toLocaleString('en-IN') : '0')}
                              </p>
                              <p className="font-sans text-[9px] font-bold text-text-muted uppercase tracking-tight mt-1.5">{t('home.totalKm', 'Total KM')}</p>
                            </div>
                            <div className="px-1">
                              <p className="font-sans text-base font-black text-text leading-none">{operatorFleet.vehicles.length || 22}</p>
                              <p className="font-sans text-[9px] font-bold text-text-muted uppercase tracking-tight mt-1.5">{t('operator.cars', 'Total Cars')}</p>
                            </div>
                            <div className="px-1">
                              <p className="font-sans text-base font-black text-green leading-none">
                                {activeWeek?.gps?.deadMilePct != null ? `${activeWeek.gps.deadMilePct}%` : '0%'}
                              </p>
                              <p className="font-sans text-[9px] font-bold text-text-muted uppercase tracking-tight mt-1.5">{t('home.deadMilesPct', 'Dead Miles %')}</p>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* 4. LAST WEEK HISAAB & SECURITY DEPOSIT (CLICKABLE CARD) */}
                      {loginType === 'driver' ? (
                        (() => {
                          const targetWeek = prevWeek || activeWeek;
                          const targetWeekIdx = prevWeek ? 1 : 0;
                          if (isFleetDriver && !targetWeek) {
                            return (
                              <div className="bg-surface border border-border/80 rounded-2xl p-3.5 shadow-xs text-left space-y-2.5 font-sans">
                                <div className="flex justify-between items-center text-xs border-b border-border/60 pb-2">
                                  <span className="font-bold text-text uppercase tracking-wider text-[10px]">
                                    Fleet Settlement Status
                                  </span>
                                  <span className="text-[10px] font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-md">
                                    Operator Handled
                                  </span>
                                </div>
                                <p className="text-xs text-text-muted leading-tight">
                                  All prior week hisaabs and collections for vehicle <strong>{!driverVehicle?.number || driverVehicle.number === 'Unassigned' || driverVehicle.number.toLowerCase() === 'unassigned' ? 'Unassigned' : driverVehicle.number}</strong> are managed by <strong>{driverUser.operatorName || 'Fleet Operator'}</strong>.
                                </p>
                                <div className="border-t border-border/60 pt-2 flex items-center justify-between text-xs">
                                  <span className="font-bold text-text uppercase tracking-wider text-[10px]">
                                    {t('home.deposit', 'Security Deposit')}
                                  </span>
                                  <div className="flex items-center gap-2 text-[10px] font-sans">
                                    <span className="bg-green-50 text-green-700 border border-green-200/70 px-2.5 py-0.5 rounded-full font-bold">
                                      {t('home.paid', 'Paid')}: ₹{(driverUser.depositPaidSoFar || driverUser.depositAmount).toLocaleString('en-IN', { minimumFractionDigits: (driverUser.depositPaidSoFar || driverUser.depositAmount) % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            );
                          }
                          if (!targetWeek) return null;

                          const isWeeklyPayout = (targetWeek.currentWeekOs || 0) < 0 || ((targetWeek.toPay || 0) > 0 && (targetWeek.toCollect || 0) <= 0);
                          const payoutAmt = (targetWeek.toPay && targetWeek.toPay > 0) ? targetWeek.toPay : Math.abs(targetWeek.currentWeekOs || 0);
                          const isSettled = targetWeek.paymentStatus === 'settled' || targetWeek.status === 'settled_pay';
                          const isAllPaid = isSettled || ((targetWeek.toCollect || 0) <= 0 && (targetWeek.currentWeekOs || 0) <= 0 && !isWeeklyPayout);

                          return (
                            <div
                              onClick={() => { setDriverWeekIndex(targetWeekIdx); navigateTo('hisaab'); }}
                              className="bg-surface border border-border/80 hover:border-primary/50 rounded-2xl p-3.5 shadow-xs text-left space-y-3 font-sans cursor-pointer transition-all hover:shadow-md group overflow-hidden"
                            >
                              <div className="flex justify-between items-center border-b border-border/60 pb-2.5">
                                <span className="font-sans text-[11px] font-bold text-text uppercase tracking-wider group-hover:text-primary transition-colors">
                                  {prevWeek ? t('home.lastWeekHisaab', 'LAST WEEK HISAAB') : t('home.currentSettlement', 'CURRENT SETTLEMENT STATUS')}
                                </span>
                                <span className="text-[10px] font-semibold text-text-muted font-mono bg-bg px-2 py-0.5 rounded-md border border-border/50">
                                  {t('home.week', 'Week')} #{targetWeek.weekNumber} • {targetWeek.hisaabNumber}
                                </span>
                              </div>

                              {isWeeklyPayout ? (
                                <div className="flex justify-between items-center gap-2 pt-0.5">
                                  <div>
                                    <div className="text-[10px] font-medium text-text-muted uppercase tracking-wider">
                                      {isSettled ? t('home.payoutPaid', 'Payout to Bank') : t('home.payoutPending', 'Payout Processing')}
                                    </div>
                                    <div className="font-sans text-xl font-bold text-green mt-0.5 whitespace-nowrap font-mono">
                                      +₹{payoutAmt.toLocaleString('en-IN', { minimumFractionDigits: payoutAmt % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}
                                    </div>
                                  </div>
                                  <span className={`flex items-center gap-1.5 font-sans text-[10px] font-bold px-3 py-1.5 rounded-full shrink-0 whitespace-nowrap border ${isSettled ? 'text-green bg-green-light border-green-200/50' : 'text-blue-700 bg-blue-50 border-blue-200'}`}>
                                    {isSettled ? <CheckCircle2 className="w-3.5 h-3.5 text-green" /> : <Clock className="w-3.5 h-3.5 text-blue-600" />}
                                    {isSettled ? t('home.paidToBank', 'Paid to Bank') : t('home.payoutDue', 'Payout Due')}
                                  </span>
                                </div>
                              ) : isAllPaid ? (
                                <div className="flex justify-between items-center gap-2 pt-0.5">
                                  <div>
                                    <div className="text-[10px] font-medium text-text-muted uppercase tracking-wider">{t('home.balanceDue', 'Balance Due')}</div>
                                    <div className="font-sans text-xl font-bold text-green mt-0.5 whitespace-nowrap font-mono">₹0</div>
                                  </div>
                                  <span className="flex items-center gap-1.5 font-sans text-[10px] font-bold text-green bg-green-light px-3 py-1.5 rounded-full shrink-0 whitespace-nowrap border border-green-200/50">
                                    <CheckCircle2 className="w-3.5 h-3.5 text-green" />
                                    {t('home.allSettled', 'All Settled')}
                                  </span>
                                </div>
                              ) : (
                                <div className="flex flex-wrap items-start justify-between gap-2 pt-0.5">
                                  <div className="min-w-0">
                                    <div className="text-[10px] font-medium text-text-muted uppercase tracking-wider">{t('home.totalOutstandingDue', 'Total Outstanding Due')}</div>
                                    <div className="font-sans text-xl font-extrabold text-red-600 mt-0.5 whitespace-nowrap font-mono">
                                      -₹{(() => {
                                        const isSettled = targetWeek.paymentStatus === 'settled' || targetWeek.status === 'settled';
                                        const remHisaab = isSettled
                                          ? 0
                                          : (targetWeek.toCollect !== undefined && targetWeek.toCollect !== null && targetWeek.toCollect > 0)
                                          ? targetWeek.toCollect
                                          : Math.max(0, targetWeek.currentWeekOs || 0);
                                        const due = remHisaab + (driverUser.depositPending || 0);
                                        return due.toLocaleString('en-IN', {
                                          minimumFractionDigits: due % 1 !== 0 ? 2 : 0,
                                          maximumFractionDigits: 2,
                                        });
                                      })()}
                                    </div>
                                  </div>
                                  <div className="flex flex-wrap items-center gap-1.5 shrink-0 pt-0.5" onClick={(e) => e.stopPropagation()}>
                                    <span className="font-sans text-[10px] font-bold text-red-600 bg-red-50 border border-red-200 px-2 py-0.5 rounded-md whitespace-nowrap">
                                      {t('common.due', 'Due')}
                                    </span>
                                    {isFleetManaged ? (
                                      <span className="font-sans text-[10px] font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-1 rounded-md text-center">
                                        {t('home.fleetManagedMsg', 'Payments handled by Fleet Operator')}
                                      </span>
                                    ) : (
                                      <button
                                        onClick={() => {
                                          setDriverWeekIndex(targetWeekIdx);
                                          navigateTo('settle');
                                        }}
                                        className="px-3.5 py-1.5 rounded-lg bg-primary hover:bg-primary-hover font-sans text-xs font-semibold text-white shadow-xs cursor-pointer transition-all hover:scale-105 whitespace-nowrap"
                                      >
                                        {t('common.pay', 'Pay')}
                                      </button>
                                    )}
                                  </div>
                                </div>
                              )}

                              {/* Merged Security Deposit Strip for Driver */}
                              <div className="border-t border-border/60 pt-2.5 flex items-center justify-between text-xs">
                                <span className="font-bold text-text uppercase tracking-wider text-[10px]">
                                  {t('home.deposit', 'Security Deposit')}
                                </span>
                                <div className="flex items-center gap-2 text-[10px] font-sans">
                                  <span className="bg-green-50 text-green-700 border border-green-200/70 px-2.5 py-0.5 rounded-full font-bold">
                                    {t('home.paid', 'Paid')}: ₹{(driverUser.depositPaidSoFar || driverUser.depositAmount).toLocaleString('en-IN', { minimumFractionDigits: (driverUser.depositPaidSoFar || driverUser.depositAmount) % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}
                                  </span>
                                  <span className={`px-2.5 py-0.5 rounded-full font-bold border ${(driverUser.depositPending || 0) > 0 ? 'bg-amber-50 text-amber-700 border-amber-200/70' : 'bg-green-50 text-green-700 border-green-200/70'}`}>
                                    {t('home.pending', 'Pending')}: ₹{(driverUser.depositPending || 0).toLocaleString('en-IN', { minimumFractionDigits: (driverUser.depositPending || 0) % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}
                                  </span>
                                </div>
                              </div>
                            </div>
                          );
                        })()
                      ) : (
                        <div
                          onClick={() => navigateTo('settle')}
                          className="bg-surface border border-border/80 hover:border-primary/50 rounded-2xl p-3.5 shadow-xs text-left space-y-3 font-sans cursor-pointer transition-all hover:shadow-md group overflow-hidden"
                        >
                          <div className="flex justify-between items-center text-xs border-b border-border/60 pb-2">
                            <span className="font-bold text-text flex items-center gap-1.5 uppercase tracking-wider text-[10px] group-hover:text-primary transition-colors">
                              <AlertCircle className="h-3.5 w-3.5 text-amber-600" />
                              {t('home.netSettlement', 'FINAL SETTLEMENT')}
                            </span>
                            <span className="text-[10px] font-mono text-text-muted bg-bg px-2 py-0.5 rounded-md border border-border/50">
                              Week #{activeWeek ? activeWeek.weekNumber : 40} • {operatorFleet.operatorCode || 'FLEET'}
                            </span>
                          </div>

                          {(() => {
                            const totalCashInHand = (activeWeek?.cashCollected && activeWeek.cashCollected > 0)
                              ? activeWeek.cashCollected
                              : (activeWeek ? (Math.abs(activeWeek.platforms?.uber?.cashCollection || 0) + Math.abs(activeWeek.platforms?.ola?.cashCollection || 0) + Math.abs(activeWeek.platforms?.rapido?.cashCollection || 0)) : 0);

                            const fleetSumToCollect = operatorFleet.vehicles.reduce((sum, v) => (v.currentWeekOs > 0 ? sum + v.currentWeekOs : sum), 0);
                            const fleetSumToPay = operatorFleet.vehicles.reduce((sum, v) => (v.currentWeekOs < 0 ? sum + Math.abs(v.currentWeekOs) : sum), 0);
                            const totalToCollect = (activeWeek && activeWeek.toCollect !== undefined && activeWeek.toCollect !== null)
                              ? activeWeek.toCollect
                              : fleetSumToCollect;
                            const totalToPay = (activeWeek && activeWeek.toPay !== undefined && activeWeek.toPay !== null)
                              ? activeWeek.toPay
                              : fleetSumToPay;

                            // Net settlement: SUM(to_collect) - SUM(to_pay)
                            const netSettlement = totalToCollect - totalToPay;
                            const isPayout = netSettlement < 0;
                            const netSettlementAmt = Math.abs(netSettlement);

                            return (
                              <>
                                <div className="flex flex-wrap items-start justify-between gap-2 pt-0.5">
                                  <div className="min-w-0">
                                    <div className="text-[10px] font-medium text-text-muted uppercase tracking-wider">
                                      {isPayout ? t('home.payoutToBank', 'Payout to Bank') : netSettlement === 0 ? t('home.settlementCleared', 'Settlement Status') : t('home.dueToLetzryd', 'Due to be paid to LetzRyd')}
                                    </div>
                                    <div className={`font-sans text-2xl font-extrabold mt-0.5 whitespace-nowrap font-mono ${isPayout ? 'text-green' : netSettlement === 0 ? 'text-green' : 'text-red-600'}`}>
                                      {isPayout 
                                        ? `+₹${netSettlementAmt.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` 
                                        : netSettlementAmt === 0 
                                        ? '₹0' 
                                        : `-₹${netSettlementAmt.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                                    </div>
                                  </div>
                                  <div className="flex flex-wrap items-center gap-1.5 shrink-0 pt-0.5" onClick={(e) => e.stopPropagation()}>
                                    {!isPayout && netSettlementAmt > 0 ? (
                                      <>
                                        <span className="font-sans text-[10px] font-bold text-red-600 bg-red-50 border border-red-200 px-2 py-0.5 rounded-md">
                                          {t('common.due', 'Due')}
                                        </span>
                                        <button
                                          onClick={() => navigateTo('settle')}
                                          className="px-3.5 py-1.5 rounded-lg bg-primary hover:bg-primary-hover font-sans text-xs font-semibold text-white shadow-xs cursor-pointer transition-all hover:scale-105 whitespace-nowrap"
                                        >
                                          {t('home.payNow', 'Pay Now')} →
                                        </button>
                                      </>
                                    ) : (
                                      <span className="inline-flex items-center gap-1 text-[10.5px] font-bold text-green bg-green-50 border border-green-200 px-2.5 py-1 rounded-md">
                                        <CheckCircle2 className="w-3.5 h-3.5 text-green" />
                                        {isPayout ? t('home.payoutReady', 'Payout Ready') : t('home.allSettled', 'All Settled')}
                                      </span>
                                    )}
                                  </div>
                                </div>

                                {totalCashInHand > 0 && (
                                  <div className="p-2 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-center gap-2 text-[10.5px] text-text-muted leading-tight">
                                    <Info className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                                    <span>
                                      {t('home.driversCollectedPrefix', 'Drivers collected')}{' '}
                                      <strong>₹{totalCashInHand.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</strong>{' '}
                                      {t('home.driversCollectedSuffix', 'in cash on road. Collect rent balance to pay LetzRyd.')}
                                    </span>
                                  </div>
                                )}
                              </>
                            );
                          })()}

                          {/* Merged Security Deposit Strip for Operator */}
                          <div className="border-t border-border/60 pt-2.5 flex items-center justify-between text-xs">
                            <span className="font-bold text-text uppercase tracking-wider text-[10px]">
                              {t('fleet.securityDeposit', 'FLEET SECURITY DEPOSIT')}
                            </span>
                            <div className="flex items-center gap-2 text-[10px] font-sans">
                              <span className="bg-green-50 text-green-700 border border-green-200/70 px-2.5 py-0.5 rounded-full font-bold">
                                {t('home.paid', 'Paid')}: ₹{(operatorFleet.depositPaidSoFar ?? 0).toLocaleString('en-IN', { minimumFractionDigits: (operatorFleet.depositPaidSoFar ?? 0) % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}
                              </span>
                              <span className="bg-amber-50 text-amber-700 border border-amber-200/70 px-2.5 py-0.5 rounded-full font-bold">
                                {t('home.pending', 'Pending')}: ₹{(operatorFleet.depositPending ?? 0).toLocaleString('en-IN', { minimumFractionDigits: (operatorFleet.depositPending ?? 0) % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}
                              </span>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* 5. ACTIVE EMERGENCY SOS BANNER (IF ACTIVATED) */}
                      {sosActivated && (
                        <div
                          onClick={() => setIsSosModalOpen(true)}
                          className="bg-red-600 hover:bg-red-700 text-white rounded-2xl p-3.5 flex items-center justify-between cursor-pointer animate-pulse shadow-md transition-all active:scale-98"
                        >
                          <div className="flex items-center gap-2.5">
                            <span className="text-xl">🚨</span>
                            <div>
                              <p className="font-sans text-xs font-black uppercase tracking-wider">
                                {t('sos.activated', 'Emergency SOS Active!')}
                              </p>
                              <p className="text-[10px] text-white/90 font-medium mt-0.5">
                                Central Hub monitoring coordinates ({sosTime || 'Active'}). Tap to manage.
                              </p>
                            </div>
                          </div>
                          <span className="text-[10px] font-extrabold bg-white/25 px-2.5 py-1 rounded-lg">
                            Manage →
                          </span>
                        </div>
                      )}

                      {/* 6. CONCISE QUICK ACCESS ACTION STRIP (3-ITEM HORIZONTAL LAYOUT) */}
                      <div className="bg-surface border border-border/80 rounded-xl p-2 shadow-xs font-sans">
                        <div className="grid grid-cols-3 divide-x divide-border/70">
                          {/* 1. Driver Manager */}
                          <button
                            onClick={() => navigateTo('support')}
                            className="px-1.5 py-1.5 flex items-center justify-center gap-1.5 cursor-pointer group hover:opacity-85 transition-all text-left"
                          >
                            <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center group-hover:bg-indigo-600 group-hover:text-white transition-all shadow-2xs shrink-0">
                              <Headset className="h-3.5 w-3.5" />
                            </div>
                            <div className="min-w-0 flex-1">
                              <span className="font-bold text-[9.5px] text-text leading-tight block">{t('home.driverManagerTitle', 'Driver Manager')}</span>
                              <span className="text-[8px] text-text-muted leading-none block mt-0.5">{t('home.driverManagerSub', 'Call / Chat')}</span>
                            </div>
                          </button>

                          {/* 2. Refer Driver */}
                          <button
                            onClick={() => navigateTo('referral')}
                            className="px-1.5 py-1.5 flex items-center justify-center gap-1.5 cursor-pointer group hover:opacity-85 transition-all text-left"
                          >
                            <div className="w-7 h-7 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center group-hover:bg-purple-600 group-hover:text-white transition-all shadow-2xs shrink-0">
                              <Gift className="h-3.5 w-3.5" />
                            </div>
                            <div className="min-w-0 flex-1">
                              <span className="font-bold text-[9.5px] text-text leading-tight block">{t('home.referDriverTitle', 'Refer Driver')}</span>
                              <span className="text-[8px] text-text-muted leading-none block mt-0.5">{t('home.referDriverSub', 'Earn ₹1,000')}</span>
                            </div>
                          </button>

                          {/* 3. Emergency SOS */}
                          <button
                            onClick={() => setIsSosModalOpen(true)}
                            className="px-1.5 py-1.5 flex items-center justify-center gap-1.5 cursor-pointer group hover:opacity-85 transition-all text-left"
                          >
                            <div className="w-7 h-7 rounded-lg bg-red-50 text-red-600 flex items-center justify-center group-hover:bg-red-600 group-hover:text-white transition-all shadow-2xs shrink-0">
                              <AlertTriangle className="h-3.5 w-3.5" />
                            </div>
                            <div className="min-w-0 flex-1">
                              <span className="font-bold text-[9.5px] text-text leading-tight block">{t('home.emergencySosTitle', 'Emergency SOS')}</span>
                              <span className="text-[8px] text-text-muted leading-none block mt-0.5">{t('home.emergencySosSub', 'Safety & Hub')}</span>
                            </div>
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {currentScreen === 'hisaab' && (
                    <HisaabScreen
                      weeks={hisaabWeeks}
                      weekIndex={driverWeekIndex}
                      onPrevWeek={() => setDriverWeekIndex(prev => Math.min(prev + 1, hisaabWeeks.length - 1))}
                      onNextWeek={() => setDriverWeekIndex(prev => Math.max(prev - 1, 0))}
                      loginType={loginType}
                      fleetVehicles={operatorFleet.vehicles}
                      onPayClick={() => navigateTo('settle')}
                      t={t}
                      isFleetManaged={isFleetManaged}
                      operatorName={driverUser.operatorName}
                    />
                  )}

                  {currentScreen === 'settle' && (() => {
                    const currentH = hisaabWeeks[driverWeekIndex] || (hisaabWeeks.length > 0 ? hisaabWeeks[0] : null);
                    const isWeeklyPayout = (currentH?.currentWeekOs || 0) < 0 || ((currentH?.toPay || 0) > 0 && (currentH?.toCollect || 0) <= 0 && (currentH?.currentWeekOs || 0) <= 0);
                    const isSettled = currentH?.paymentStatus === 'settled' || currentH?.status === 'settled' || currentH?.status === 'settled_pay';
                    const remainingHisaabDue = isSettled
                      ? 0
                      : isWeeklyPayout
                      ? 0
                      : (currentH?.toCollect !== undefined && currentH?.toCollect !== null && currentH?.toCollect > 0)
                      ? currentH.toCollect
                      : Math.max(0, (currentH?.currentWeekOs || 0) > 0 ? currentH.currentWeekOs : 0);
                    const pendingDep = loginType === 'operator' ? (operatorFleet.depositPending ?? 0) : (driverUser.depositPending ?? 0);
                    const challanAmt = loginType === 'operator' ? 0 : (currentH?.challan || 0);

                    const fleetNetOs = operatorFleet.vehicles.reduce((sum, v) => sum + v.currentWeekOs, 0);
                    const opNetDue = currentH
                      ? Math.max(0, (currentH.toCollect ?? 0) - (currentH.toPay ?? 0))
                      : Math.max(0, fleetNetOs);
                    const totalOperatorDue = isSettled ? 0 : opNetDue;
                    const finalHisaabAmount = loginType === 'operator' ? totalOperatorDue : Math.max(0, remainingHisaabDue - challanAmt);
                    const finalTotalAmount = finalHisaabAmount + pendingDep + challanAmt;

                    return (
                      <SettleScreen
                        amount={finalTotalAmount}
                        hisaabAmount={finalHisaabAmount}
                        pendingDeposit={pendingDep}
                        challansAmount={challanAmt}
                        weekRange={currentH?.weekStart && currentH?.weekEnd ? `${currentH.weekStart} to ${currentH.weekEnd}` : 'Current Settlement Period'}
                        upiId={LETZRYD_UPI_ID}
                        driverName={driverUser.name}
                        driverPhone={driverUser.phone}
                        driverId={driverUser.id}
                        hisaabId={currentH?.app_hisaab_id}
                        payerType={loginType}
                        onCopyUpi={handleCopyUpiId}
                        onConfirmPayment={handleConfirmPayment}
                        onBack={() => navigateTo(loginType === 'operator' ? 'operator' : 'hisaab')}
                        t={t}
                        isFleetManaged={isFleetManaged}
                        operatorName={driverUser.operatorName}
                      />
                    );
                  })()}

                  {currentScreen === 'vehicle' && (
                    <VehicleScreen
                      vehicle={driverVehicle}
                      plan={driverRentalPlan}
                      t={t}
                    />
                  )}

                  {currentScreen === 'operator' && (
                    <OperatorScreen
                      fleet={operatorFleet}
                      onSelectVehicle={handleSelectVehicleForHisaab}
                      t={t}
                    />
                  )}

                  {currentScreen === 'operatorVehicle' && selectedVehicleObj && (
                    <OperatorVehicleScreen
                      vehicle={selectedVehicleObj}
                      weekIndex={operatorVehicleWeekIndex}
                      onPrevWeek={() => setOperatorVehicleWeekIndex(prev => Math.min(prev + 1, selectedVehicleObj.hisaabWeeks.length - 1))}
                      onNextWeek={() => setOperatorVehicleWeekIndex(prev => Math.max(prev - 1, 0))}
                      onBack={() => navigateTo('operator')}
                      t={t}
                    />
                  )}

                  {currentScreen === 'support' && (
                    <motion.div
                      key="support"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="space-y-4"
                    >
                      <SupportScreen
                        user={driverUser}
                        tickets={tickets}
                        hotline={SUPPORT_HOTLINE}
                        loginType={loginType}
                        onNewTicket={() => setIsNewTicketOpen(true)}
                        onSelectTicket={(ticket) => setSelectedTicket(ticket)}
                        onOpenSos={() => setIsSosModalOpen(true)}
                        t={t}
                      />
                    </motion.div>
                  )}

                  {currentScreen === 'profile' && (
                    <motion.div
                      key="profile"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="space-y-4"
                    >
                      <ProfileScreen
                        user={driverUser}
                        loginType={loginType}
                        onUpdateContact={handleUpdateContact}
                        t={t}
                      />
                    </motion.div>
                  )}

                  {currentScreen === 'referral' && (
                    <motion.div
                      key="referral"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="space-y-4"
                    >
                      <ReferralScreen
                        driverCode={'LETZ' + driverUser.phone}
                        onCopy={handleCopyReferralCode}
                        onBack={goBack}
                        t={t}
                      />
                    </motion.div>
                  )}

                </AnimatePresence>
              </main>

              {/* Bottom Navigation */}
              <nav className="border-t border-border bg-surface px-2 py-1.5 flex items-center justify-around shrink-0 z-40">
                <button
                  onClick={() => navigateTo('home')}
                  className={`flex flex-col items-center gap-0.5 p-1 rounded-lg text-[10px] font-semibold cursor-pointer transition-all ${
                    currentScreen === 'home' ? 'text-primary font-bold' : 'text-text-muted hover:text-text'
                  }`}
                >
                  <Home className="h-4 w-4" />
                  {t('nav.home', 'Home')}
                </button>

                <button
                  onClick={() => navigateTo('hisaab')}
                  className={`flex flex-col items-center gap-0.5 p-1 rounded-lg text-[10px] font-semibold cursor-pointer transition-all ${
                    currentScreen === 'hisaab' ? 'text-primary font-bold' : 'text-text-muted hover:text-text'
                  }`}
                >
                  <ReceiptIndianRupee className="h-4 w-4" />
                  {t('nav.hisaab', 'Hisaab')}
                </button>

                <button
                  onClick={() => navigateTo('settle')}
                  className={`flex flex-col items-center gap-0.5 p-1 rounded-lg text-[10px] font-semibold cursor-pointer transition-all ${
                    currentScreen === 'settle' ? 'text-primary font-bold' : 'text-text-muted hover:text-text'
                  }`}
                >
                  <CreditCard className="h-4 w-4" />
                  {t('nav.settle', 'Settle')}
                </button>

                {loginType === 'driver' ? (
                  <button
                    onClick={() => navigateTo('vehicle')}
                    className={`flex flex-col items-center gap-0.5 p-1 rounded-lg text-[10px] font-semibold cursor-pointer transition-all ${
                      currentScreen === 'vehicle' ? 'text-primary font-bold' : 'text-text-muted hover:text-text'
                    }`}
                  >
                    <Car className="h-4 w-4" />
                    {t('nav.vehicle', 'Vehicle')}
                  </button>
                ) : (
                  <button
                    onClick={() => navigateTo('operator')}
                    className={`flex flex-col items-center gap-0.5 p-1 rounded-lg text-[10px] font-semibold cursor-pointer transition-all ${
                      currentScreen === 'operator' || currentScreen === 'operatorVehicle' ? 'text-primary font-bold' : 'text-text-muted hover:text-text'
                    }`}
                  >
                    <Building className="h-4 w-4" />
                    {t('nav.fleet', 'Fleet')}
                  </button>
                )}

                <button
                  onClick={() => navigateTo('support')}
                  className={`flex flex-col items-center gap-0.5 p-1 rounded-lg text-[10px] font-semibold cursor-pointer transition-all ${
                    currentScreen === 'support' ? 'text-primary font-bold' : 'text-text-muted hover:text-text'
                  }`}
                >
                  <Headset className="h-4 w-4" />
                  {t('nav.support', 'Support')}
                </button>
              </nav>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Modals Layer — inside the phone container so they're clipped to the phone frame */}
        {isNotifOpen && (
          <NotificationModal
            notifications={notifications}
            onClose={() => setIsNotifOpen(false)}
            onMarkAllRead={handleMarkAllNotificationsRead}
            t={t}
          />
        )}

        {isNewTicketOpen && (
          <NewTicketModal
            categories={TICKET_CATEGORIES}
            onClose={() => setIsNewTicketOpen(false)}
            onSubmit={handleNewTicketSubmit}
            t={t}
          />
        )}

        {isSosModalOpen && (
          <EmergencySosModal
            isActivated={sosActivated}
            sosTime={sosTime}
            onClose={() => setIsSosModalOpen(false)}
            onTriggerSos={handleSosTrigger}
            onCancelSos={handleCancelSos}
            onReportIncident={handleReportIncident}
            hotline={SUPPORT_HOTLINE}
            t={t}
          />
        )}

        {selectedTicket && (
          <TicketDetailModal
            ticket={selectedTicket}
            onClose={() => setSelectedTicket(null)}
            t={t}
          />
        )}
      </div>
    </div>
  );
}
