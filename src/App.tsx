/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect, useRef } from 'react';
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
  Check
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

import { User, Vehicle, RentalPlan, HisaabWeek, Fleet, FleetVehicle, Ticket, Notification, Language } from './types';
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
  getNotifications as fetchNotifications,
  getTickets,
  createTicket as apiCreateTicket,
  submitReferral as apiSubmitReferral,
  mapDriverToUser,
  mapDriverToVehicle,
  mapDriverToRentalPlan,
  mapHisaabToWeek,
  mapNotification,
  mapTicket,
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

export default function App() {
  // Multi-Language State (Default EN, switchable to HI, MR, TE, KN)
  const [language, setLanguage] = useState<Language>('en');

  // Authentication & Session
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loginType, setLoginType] = useState<'driver' | 'operator'>('driver');
  const [phoneInput, setPhoneInput] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [otpInput, setOtpInput] = useState('');
  const [confirmationResult, setConfirmationResult] = useState<ConfirmationResult | null>(null);
  const [isSendingOtp, setIsSendingOtp] = useState(false);
  const [isVerifyingOtp, setIsVerifyingOtp] = useState(false);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [phoneError, setPhoneError] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [demoDropdownOpen, setDemoDropdownOpen] = useState(false);

  // Cancellation ref: set to true when user goes back from OTP screen mid-request
  const otpRequestCancelledRef = useRef(false);

  // Global Navigation
  const [currentScreen, setCurrentScreen] = useState<string>('home');
  const [prevScreen, setPrevScreen] = useState<string>('home');

  // Ledger Week Indices
  const [driverWeekIndex, setDriverWeekIndex] = useState(0);
  const [operatorVehicleWeekIndex, setOperatorVehicleWeekIndex] = useState(0);

  // Data Collections
  const [tickets, setTickets] = useState<Ticket[]>(INITIAL_TICKETS);
  const [notifications, setNotifications] = useState<Notification[]>(INITIAL_NOTIFICATIONS);
  const [hisaabWeeks, setHisaabWeeks] = useState<HisaabWeek[]>(HISAAB_WEEKS_DATA);
  const [operatorFleet, setOperatorFleet] = useState<Fleet>(OPERATOR_FLEET_DATA);
  const [driverUser, setDriverUser] = useState<User>(USER_DATA);
  const [driverVehicle, setDriverVehicle] = useState<Vehicle>(VEHICLE_DATA);
  const [driverRentalPlan, setDriverRentalPlan] = useState<RentalPlan>(RENTAL_PLAN_DATA);

  // Active Vehicle Selection for Operator View
  const [selectedVehicleNumber, setSelectedVehicleNumber] = useState<string | null>('KA05AQ7692');

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
        const confirmation = await signInWithPhoneNumber(auth, formattedPhone, window.recaptchaVerifier);

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
    const inferredRole: 'driver' | 'operator' = matchedProfile 
      ? matchedProfile.role 
      : (cleanPhone === '9691938866' || cleanPhone === '9848012345' ? 'operator' : 'driver');

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
            const notifs = await fetchNotifications(opProfile.app_operator_id);

            setDriverUser({
              id: opProfile.operator_code,
              name: opProfile.company_name,
              operatorCode: opProfile.operator_code,
              phone: opProfile.phone,
              joined: '',
              initials: opProfile.initials || 'OP',
              aadhar: '',
              dlNumber: '',
              dlExpiry: '',
              emergencyContact: opProfile.assigned_manager_phone ? `${opProfile.assigned_manager_name} - ${opProfile.assigned_manager_phone}` : '',
              emergencyName: opProfile.assigned_manager_name || '',
              emergencyRelation: 'Account Manager',
              emergencyPhone: opProfile.assigned_manager_phone || '',
              address: opProfile.address || '',
              bloodGroup: '',
              dob: '',
              operatorType: 'Fleet Owner',
              assignedManagerName: opProfile.assigned_manager_name || '',
              assignedManagerPhone: opProfile.assigned_manager_phone || '',
              depositAmount: opProfile.deposit_total_req,
              depositTotalRequired: opProfile.deposit_total_req,
              depositPaidSoFar: opProfile.deposit_paid,
              depositPending: opProfile.deposit_pending,
              depositNextDueDate: '',
              cumulativeOwed: opProfile.cw_to_collect || 0,
              weeklyIncentiveTargetTrips: 0,
              completedTripsThisWeek: 0,
              weeklyIncentiveReward: 0,
            } as any);

            // Map fleet data with driver hisaabs
            const mappedVehicles: FleetVehicle[] = await Promise.all((fleetData.vehicles || []).map(async (v: any) => {
              let vehicleHisaabs: HisaabWeek[] = [];
              if (v.driver_id) {
                try {
                  const hisaabs = await getDriverHisaabs(v.driver_id);
                  vehicleHisaabs = (hisaabs || []).map(mapHisaabToWeek);
                } catch (hisaabErr) {
                  console.warn(`Failed to fetch hisaabs for driver ID ${v.driver_id}:`, hisaabErr);
                }
              }
              return {
                number: v.vehicle_number,
                make: v.vehicle_make,
                model: v.vehicle_model,
                driverName: v.driver_name,
                plan: { name: 'Standard', dailyRate: v.daily_rate || 1000 },
                currentWeekOs: v.current_week_os || 0,
                status: (v.status === 'active' ? 'active' : 'idle') as 'active' | 'idle',
                hisaabWeeks: vehicleHisaabs.length > 0 ? vehicleHisaabs : HISAAB_WEEKS_DATA,
              };
            }));

            const mappedFleet: Fleet = {
              operatorCode: fleetData.operator_code,
              operatorName: fleetData.company_name,
              depositTotalRequired: fleetData.deposit_total_req,
              depositPaidSoFar: fleetData.deposit_paid,
              depositPending: fleetData.deposit_pending,
              vehicles: mappedVehicles,
            };
            setOperatorFleet(mappedFleet);
            if (mappedVehicles.length > 0 && mappedVehicles[0].hisaabWeeks.length > 0) {
              setHisaabWeeks(mappedVehicles[0].hisaabWeeks);
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
            const notifs = await fetchNotifications(driverProfile.app_driver_id);
            const tkts = await getTickets(driverProfile.app_driver_id);

            setDriverUser(mapDriverToUser(driverProfile));
            setDriverVehicle(mapDriverToVehicle(driverProfile));
            setDriverRentalPlan(mapDriverToRentalPlan(driverProfile));
            if (hisaabs && hisaabs.length > 0) setHisaabWeeks(hisaabs.map(mapHisaabToWeek));
            if (notifs && notifs.length > 0) setNotifications(notifs.map(mapNotification));
            if (tkts && tkts.length > 0) setTickets(tkts.map(mapTicket));
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

  const handleLogout = () => {
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
      const driverIdFromCode = parseInt((driverUser.id || '0').replace(/\D/g, '').slice(-4)) || 1;
      const backendTicket = await apiCreateTicket(
        loginType,
        driverIdFromCode,
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

  const handleSelectVehicleForHisaab = (number: string) => {
    setSelectedVehicleNumber(number);
    setOperatorVehicleWeekIndex(0);
    const targetVeh = operatorFleet.vehicles.find(v => v.number.replace(/\s+/g, '') === number.replace(/\s+/g, '') || v.number === number);
    if (targetVeh && targetVeh.hisaabWeeks && targetVeh.hisaabWeeks.length > 0) {
      setHisaabWeeks(targetVeh.hisaabWeeks);
    }
    navigateTo('operatorVehicle');
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

  const handleConfirmPayment = async () => {
    // Re-fetch live profile + hisaabs from DB so all pages show real updated values
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
      } else {
        const opProfile = await getOperatorByPhone(driverUser.phone).catch(() => null);
        if (opProfile) {
          const fleetData = await getOperatorFleet(opProfile.app_operator_id).catch(() => null);
          if (fleetData) {
            const mappedVehicles: FleetVehicle[] = await Promise.all((fleetData.vehicles || []).map(async (v: any) => {
              let vehicleHisaabs: HisaabWeek[] = [];
              if (v.driver_id) {
                try {
                  const hisaabs = await getDriverHisaabs(v.driver_id);
                  vehicleHisaabs = (hisaabs || []).map(mapHisaabToWeek);
                } catch (e) {}
              }
              return {
                number: v.vehicle_number,
                make: v.vehicle_make,
                model: v.vehicle_model,
                driverName: v.driver_name,
                plan: { name: 'Standard', dailyRate: v.daily_rate || 1000 },
                currentWeekOs: v.current_week_os || 0,
                status: (v.status === 'active' ? 'active' : 'idle') as 'active' | 'idle',
                hisaabWeeks: vehicleHisaabs,
              };
            }));
            setOperatorFleet({
              operatorCode: fleetData.operator_code,
              operatorName: fleetData.company_name,
              depositTotalRequired: fleetData.deposit_total_req,
              depositPaidSoFar: fleetData.deposit_paid,
              depositPending: fleetData.deposit_pending,
              vehicles: mappedVehicles,
            });
            const selVeh = mappedVehicles.find(v => v.number === selectedVehicleNumber || v.number.replace(/\s+/g, '') === (selectedVehicleNumber || '').replace(/\s+/g, '')) || mappedVehicles[0];
            if (selVeh && selVeh.hisaabWeeks && selVeh.hisaabWeeks.length > 0) {
              setHisaabWeeks(selVeh.hisaabWeeks);
            }
          }
          setDriverUser(prev => ({
            ...prev,
            depositPaidSoFar: opProfile.deposit_paid,
            depositPending: opProfile.deposit_pending,
            cumulativeOwed: opProfile.cw_to_collect || 0
          }));
        }
      }
    } catch (err) {
      console.warn('[handleConfirmPayment] Re-fetch after payment failed:', err);
    }

    triggerToast(t('payment.noted', 'Payment verified! Balance updated.'), 'success');
    navigateTo('settle');
  };

  // Auto-verify when Cashfree redirects back with ?order_id=...
  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search);
    const orderId = searchParams.get('order_id');
    if (orderId) {
      window.history.replaceState({}, document.title, window.location.pathname);
      fetch(`/api/payments/verify/${orderId}`)
        .then(res => res.json())
        .then(data => {
          if (data?.is_success || data?.status === 'SUCCESS') {
            handleConfirmPayment();
          }
        })
        .catch(err => console.warn('Order verification notice:', err));
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
  const activeWeek = hisaabWeeks[0] || HISAAB_WEEKS_DATA[0];
  const prevWeek = hisaabWeeks[1] || HISAAB_WEEKS_DATA[1];

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

                {/* Demo Quick Login Profiles Dropdown */}
                <div className="pt-3 border-t border-border space-y-2 text-left relative">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider block">
                      ⚡ Quick Switch Demo Profiles:
                    </span>
                    <span className="text-[10px] font-semibold text-primary font-mono">OTP: 1234</span>
                  </div>

                  {/* Dropdown Toggle Button */}
                  <button
                    type="button"
                    onClick={() => setDemoDropdownOpen(!demoDropdownOpen)}
                    className="w-full flex items-center justify-between p-2.5 rounded-xl bg-surface border border-border hover:border-primary/60 text-xs font-medium text-text cursor-pointer transition-all shadow-xs"
                  >
                    <div className="flex items-center gap-2">
                      <div className="h-6 w-6 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold text-[11px]">
                        👤
                      </div>
                      <span className="font-semibold text-text">
                        Select a Demo Profile to Login...
                      </span>
                    </div>
                    <ChevronDown
                      className={`h-4 w-4 text-text-muted transition-transform duration-200 ${
                        demoDropdownOpen ? 'rotate-180 text-primary' : ''
                      }`}
                    />
                  </button>

                  {/* Dropdown Menu Popup */}
                  <AnimatePresence>
                    {demoDropdownOpen && (
                      <motion.div
                        initial={{ opacity: 0, y: -4, scale: 0.98 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -4, scale: 0.98 }}
                        transition={{ duration: 0.15 }}
                        className="w-full bg-surface border border-border rounded-xl shadow-lg p-1.5 space-y-1 max-h-[260px] overflow-y-auto no-scrollbar z-50 mt-1"
                      >
                        {/* Operators Group */}
                        <div className="px-2 pt-1 pb-0.5 text-[9px] font-bold text-text-muted uppercase tracking-wider">
                          🏢 Fleet Operators
                        </div>
                        {DEMO_PROFILES.filter((p) => p.role === 'operator').map((p) => (
                          <button
                            key={p.phone}
                            type="button"
                            onClick={async () => {
                              setDemoDropdownOpen(false);
                              setLoginType(p.role);
                              setPhoneInput(p.phone);
                              setOtpInput(p.otp);
                              setDriverUser(p.user);
                              setHisaabWeeks(p.weeks);
                              if (p.fleet) setOperatorFleet(p.fleet);
                              if (p.vehicle) setDriverVehicle(p.vehicle);
                              if (p.rentalPlan) setDriverRentalPlan(p.rentalPlan);
                              setIsLoggedIn(true);
                              setCurrentScreen('home');
                              triggerToast(`Logged in as ${p.name}`, 'success');

                              try {
                                const opProfile = await getOperatorByPhone(p.phone);
                                const fleetData = await getOperatorFleet(opProfile.app_operator_id);
                                const notifs = await fetchNotifications(opProfile.app_operator_id);
                                if (fleetData) {
                                  const mappedVehicles: FleetVehicle[] = await Promise.all((fleetData.vehicles || []).map(async (v: any) => {
                                    let vH: HisaabWeek[] = [];
                                    if (v.driver_id) {
                                      try {
                                        const hList = await getDriverHisaabs(v.driver_id);
                                        vH = (hList || []).map(mapHisaabToWeek);
                                      } catch (e) {}
                                    }
                                    return {
                                      number: v.vehicle_number,
                                      make: v.vehicle_make,
                                      model: v.vehicle_model,
                                      driverName: v.driver_name,
                                      plan: { name: 'Standard', dailyRate: v.daily_rate || 1000 },
                                      currentWeekOs: v.current_week_os || 0,
                                      status: (v.status === 'active' ? 'active' : 'idle') as 'active' | 'idle',
                                      hisaabWeeks: vH.length > 0 ? vH : HISAAB_WEEKS_DATA,
                                    };
                                  }));
                                  setOperatorFleet({
                                    operatorCode: fleetData.operator_code,
                                    operatorName: fleetData.company_name,
                                    depositTotalRequired: fleetData.deposit_total_req,
                                    depositPaidSoFar: fleetData.deposit_paid,
                                    depositPending: fleetData.deposit_pending,
                                    vehicles: mappedVehicles,
                                  });
                                  if (mappedVehicles.length > 0 && mappedVehicles[0].hisaabWeeks.length > 0) {
                                    setHisaabWeeks(mappedVehicles[0].hisaabWeeks);
                                    setSelectedVehicleNumber(mappedVehicles[0].number);
                                  }
                                }
                                if (notifs && notifs.length > 0) setNotifications(notifs.map(mapNotification));
                              } catch (err) {}
                            }}
                            className="w-full text-left p-2 rounded-lg hover:bg-primary/5 border border-transparent hover:border-primary/20 flex items-center justify-between text-xs cursor-pointer transition-all group"
                          >
                            <div>
                              <div className="font-bold text-text group-hover:text-primary transition-colors flex items-center gap-1.5">
                                <span>{p.name}</span>
                                <span className="text-[10px] font-normal text-text-muted">({p.phone})</span>
                              </div>
                              <div className="text-[10px] text-text-muted">
                                {p.fleet
                                  ? `${p.fleet.vehicles.length} Vehicles • ₹${Math.abs(p.fleet.vehicles.reduce((sum, v) => sum + (v.currentWeekOs < 0 ? v.currentWeekOs : 0), 0)).toLocaleString('en-IN', { minimumFractionDigits: Math.abs(p.fleet.vehicles.reduce((sum, v) => sum + (v.currentWeekOs < 0 ? v.currentWeekOs : 0), 0)) % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })} To Pay`
                                  : 'Fleet Operator'}
                              </div>
                            </div>
                            <span className="text-[10px] font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-md">
                              {p.tag}
                            </span>
                          </button>
                        ))}

                        {/* Drivers Group */}
                        <div className="px-2 pt-2 pb-0.5 text-[9px] font-bold text-text-muted uppercase tracking-wider border-t border-border/50">
                          🚗 Drivers
                        </div>
                        {DEMO_PROFILES.filter((p) => p.role === 'driver').map((p) => (
                          <button
                            key={p.phone}
                            type="button"
                            onClick={async () => {
                              setDemoDropdownOpen(false);
                              setLoginType(p.role);
                              setPhoneInput(p.phone);
                              setOtpInput(p.otp);
                              setDriverUser(p.user);
                              setHisaabWeeks(p.weeks);
                              if (p.fleet) setOperatorFleet(p.fleet);
                              if (p.vehicle) setDriverVehicle(p.vehicle);
                              if (p.rentalPlan) setDriverRentalPlan(p.rentalPlan);
                              setIsLoggedIn(true);
                              setCurrentScreen('home');
                              triggerToast(`Logged in as ${p.name}`, 'success');

                              try {
                                const profile = await getDriverByPhone(p.phone);
                                const hisaabs = await getDriverHisaabs(profile.app_driver_id);
                                const notifs = await fetchNotifications(profile.app_driver_id);
                                const tkts = await getTickets(profile.app_driver_id);
                                setDriverUser(mapDriverToUser(profile));
                                setDriverVehicle(mapDriverToVehicle(profile));
                                setDriverRentalPlan(mapDriverToRentalPlan(profile));
                                if (hisaabs && hisaabs.length > 0) setHisaabWeeks(hisaabs.map(mapHisaabToWeek));
                                if (notifs && notifs.length > 0) setNotifications(notifs.map(mapNotification));
                                if (tkts && tkts.length > 0) setTickets(tkts.map(mapTicket));
                              } catch (err) {}
                            }}
                            className="w-full text-left p-2 rounded-lg hover:bg-primary/5 border border-transparent hover:border-primary/20 flex items-center justify-between text-xs cursor-pointer transition-all group"
                          >
                            <div>
                              <div className="font-bold text-text group-hover:text-primary transition-colors flex items-center gap-1.5">
                                <span>{p.name}</span>
                                <span className="text-[10px] font-normal text-text-muted">({p.phone})</span>
                              </div>
                              <div className="text-[10px] text-text-muted">
                                {p.vehicle ? `${p.vehicle.number} • ${p.vehicle.model}` : 'Assigned Vehicle'}
                              </div>
                            </div>
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                              p.tag.includes('Unpaid')
                                ? 'bg-amber-500/10 text-amber-600'
                                : 'bg-green-light text-green'
                            }`}>
                              {p.tag}
                            </span>
                          </button>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>
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
              <main className="flex-1 overflow-y-auto p-4 space-y-4 no-scrollbar">
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
                        <h2 className="font-extrabold text-text text-sm flex items-center gap-1.5">
                          {t('home.greeting', 'Hi')}, {userName.split(' ')[0]} 👋
                        </h2>
                        <p className="text-text-muted text-[11px]">
                          {t('home.summary', "Here's your weekly settlement summary")}
                        </p>
                      </div>

                      {/* 2. THIS WEEK HISAAB & INCENTIVE GOAL (HERO CLICKABLE TILE) */}
                      {loginType === 'driver' ? (
                        <div
                          onClick={() => { setDriverWeekIndex(0); navigateTo('hisaab'); }}
                          className="bg-surface border border-border/80 hover:border-primary/50 rounded-2xl p-3.5 shadow-xs text-left space-y-3 font-sans cursor-pointer transition-all hover:shadow-md group"
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

                          {/* Financial Amount & Growth Badge */}
                          <div className="flex justify-between items-center gap-2 pt-0.5">
                            <div>
                              <div className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">{t('home.estimatedPayout', 'ESTIMATED PAYOUT')}</div>
                              {(() => {
                                const rawDue = activeWeek.toCollect || (activeWeek.currentWeekOs > 0 ? activeWeek.currentWeekOs : 0);
                                const paid = activeWeek.paidAmount || 0;
                                const isSettled = activeWeek.status === 'settled' || activeWeek.paymentStatus === 'settled' || (paid >= rawDue && rawDue > 0);
                                const isPayout = activeWeek.currentWeekOs < 0 || (activeWeek.toPay && activeWeek.toPay > 0);
                                const val = isPayout 
                                  ? (activeWeek.toPay || Math.abs(activeWeek.currentWeekOs))
                                  : (isSettled ? 0 : Math.max(0, rawDue - paid));
                                return (
                                  <div className={`font-sans text-2xl font-black mt-0.5 ${isPayout ? 'text-green' : isSettled ? 'text-green' : 'text-red-600'}`}>
                                    {isSettled && !isPayout ? '₹0' : `${isPayout ? '+₹' : '-₹'}${val.toLocaleString('en-IN', { minimumFractionDigits: val % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}`}
                                  </div>
                                );
                              })()}
                            </div>
                            {/* Growth Trend Badge */}
                            <span className="flex items-center gap-1 font-sans text-[10px] font-bold text-green bg-green-light px-2.5 py-1 rounded-full shrink-0 whitespace-nowrap border border-green-200/50">
                              <TrendingUp className="w-3 h-3 text-green" />
                              {activeWeek.growthPct}% {t('home.vsLastWeek', 'vs last week')}
                            </span>
                          </div>

                          {/* Merged Weekly Incentive Goal Progress Section */}
                          {(() => {
                            const target = driverUser.weeklyIncentiveTargetTrips || 1;
                            const completed = driverUser.completedTripsThisWeek || 0;
                            const progressPct = Math.min(100, Math.max(0, (completed / target) * 100));
                            const remaining = Math.max(0, target - completed);

                            return (
                              <div className="border-t border-border/60 pt-2.5 space-y-1.5 font-sans">
                                <div className="flex justify-between items-center text-xs">
                                  <span className="font-bold text-text flex items-center gap-1.5 text-[11px]">
                                    <Target className="w-3.5 h-3.5 text-primary" />
                                    {t('home.incentiveTracker', 'Weekly Incentive Goal')}
                                  </span>
                                  <span className="font-bold text-primary text-[11px] bg-primary/10 px-2 py-0.5 rounded-md">
                                    ₹{driverUser.weeklyIncentiveReward.toLocaleString('en-IN')} {t('home.bonus', 'Bonus')}
                                  </span>
                                </div>

                                <div className="w-full bg-border/80 rounded-full h-2 overflow-hidden p-0.5">
                                  <div
                                    className="bg-primary h-1.5 rounded-full transition-all duration-500"
                                    style={{ width: `${progressPct}%` }}
                                  />
                                </div>

                                <p className="font-sans text-[10px] text-text-muted text-right">
                                  {remaining > 0 ? (
                                    <>
                                      <strong>{remaining} {t('home.tripsRemaining', 'trips remaining')}</strong> {t('home.toUnlockBonus', `to unlock ₹${driverUser.weeklyIncentiveReward.toLocaleString('en-IN')} bonus`)}
                                    </>
                                  ) : (
                                    <span className="text-green font-bold">🎉 {t('home.goalAchieved', 'Incentive Goal Achieved!')}</span>
                                  )}
                                </p>
                              </div>
                            );
                          })()}
                        </div>
                      ) : (
                        <div
                          onClick={() => navigateTo('hisaab')}
                          className="bg-surface border border-border/80 hover:border-primary/50 rounded-2xl p-3.5 shadow-xs text-left space-y-3 font-sans cursor-pointer transition-all hover:shadow-md group"
                        >
                          <div className="flex justify-between items-center border-b border-border/60 pb-2.5">
                            <span className="font-sans text-[11px] font-bold text-text uppercase tracking-wider group-hover:text-primary transition-colors">
                              THIS WEEK FLEET HISAAB
                            </span>
                            <span className="text-[10px] font-semibold text-text-muted font-mono bg-bg px-2 py-0.5 rounded-md border border-border/50">
                              Week #{activeWeek.weekNumber} • {activeWeek.hisaabNumber}
                            </span>
                          </div>

                          <div className="flex justify-between items-center gap-2 pt-0.5">
                            <div>
                              <div className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">Fleet Payout</div>
                              <div className="font-sans text-2xl font-black text-green mt-0.5">
                                +₹{Math.abs(operatorFleet.vehicles.reduce((sum, v) => sum + (v.currentWeekOs < 0 ? v.currentWeekOs : 0), 0)).toLocaleString('en-IN', { minimumFractionDigits: Math.abs(operatorFleet.vehicles.reduce((sum, v) => sum + (v.currentWeekOs < 0 ? v.currentWeekOs : 0), 0)) % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}
                              </div>
                            </div>
                            <span className="flex items-center gap-1 font-sans text-[10px] font-bold text-green bg-green-light px-2.5 py-1 rounded-full shrink-0 whitespace-nowrap border border-green-200/50">
                              <TrendingUp className="w-3 h-3 text-green" />
                              12.5% vs last week
                            </span>
                          </div>
                        </div>
                      )}

                      {/* 3. 4-STAT KPI INDICATOR STRIP (SYMMETRIC) */}
                      {loginType === 'driver' ? (
                        <div className="bg-surface border border-border/80 rounded-2xl p-3.5 shadow-xs font-sans">
                          <div className="grid grid-cols-4 divide-x divide-border/70 text-center">
                            <div className="px-1">
                              <p className="font-sans text-base font-black text-text leading-none">{activeWeek.activeDays}</p>
                              <p className="font-sans text-[9px] font-bold text-text-muted uppercase tracking-tight mt-1.5">{t('home.daysActive', 'Days Active')}</p>
                            </div>
                            <div className="px-1">
                              <p className="font-sans text-base font-black text-text leading-none">{driverUser.completedTripsThisWeek}</p>
                              <p className="font-sans text-[9px] font-bold text-text-muted uppercase tracking-tight mt-1.5">{t('home.trips', 'Trips')}</p>
                            </div>
                            <div className="px-1">
                              <p className="font-sans text-base font-black text-text leading-none">2,441</p>
                              <p className="font-sans text-[9px] font-bold text-text-muted uppercase tracking-tight mt-1.5">{t('home.totalKm', 'Total KMs')}</p>
                            </div>
                            <div className="px-1">
                              <p className="font-sans text-base font-black text-green leading-none">{activeWeek.gps.deadMilePct}%</p>
                              <p className="font-sans text-[9px] font-bold text-text-muted uppercase tracking-tight mt-1.5">{t('home.deadMilesPct', 'Dead Miles %')}</p>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="bg-surface border border-border/80 rounded-2xl p-3.5 shadow-xs font-sans">
                          <div className="grid grid-cols-4 divide-x divide-border/70 text-center">
                            <div className="px-1">
                              <p className="font-sans text-base font-black text-text leading-none">1,165</p>
                              <p className="font-sans text-[9px] font-bold text-text-muted uppercase tracking-tight mt-1.5">Trips</p>
                            </div>
                            <div className="px-1">
                              <p className="font-sans text-base font-black text-text leading-none">12,205</p>
                              <p className="font-sans text-[9px] font-bold text-text-muted uppercase tracking-tight mt-1.5">Total KM</p>
                            </div>
                            <div className="px-1">
                              <p className="font-sans text-base font-black text-text leading-none">{operatorFleet.vehicles.length}</p>
                              <p className="font-sans text-[9px] font-bold text-text-muted uppercase tracking-tight mt-1.5">Total Cars</p>
                            </div>
                            <div className="px-1">
                              <p className="font-sans text-base font-black text-green leading-none">8.2%</p>
                              <p className="font-sans text-[9px] font-bold text-text-muted uppercase tracking-tight mt-1.5">Dead Miles %</p>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* 4. LAST WEEK HISAAB & SECURITY DEPOSIT (CLICKABLE CARD) */}
                      {loginType === 'driver' ? (
                        <div
                          onClick={() => { setDriverWeekIndex(1); navigateTo('hisaab'); }}
                          className="bg-surface border border-border/80 hover:border-primary/50 rounded-2xl p-3.5 shadow-xs text-left space-y-3 font-sans cursor-pointer transition-all hover:shadow-md group"
                        >
                          {prevWeek && (
                            <>
                              <div className="flex justify-between items-center border-b border-border/60 pb-2.5">
                                <span className="font-sans text-[11px] font-bold text-text uppercase tracking-wider group-hover:text-primary transition-colors">
                                  {t('home.lastWeekHisaab', 'LAST WEEK HISAAB')}
                                </span>
                                <span className="text-[10px] font-semibold text-text-muted font-mono bg-bg px-2 py-0.5 rounded-md border border-border/50">
                                  {t('home.week', 'Week')} #{prevWeek.weekNumber} • {prevWeek.hisaabNumber}
                                </span>
                              </div>

                              {prevWeek.paymentStatus === 'settled' || prevWeek.status === 'settled_pay' || ((prevWeek.toCollect || 0) <= 0 && (prevWeek.currentWeekOs || 0) <= 0) ? (
                                <div className="flex justify-between items-center gap-2 pt-0.5">
                                  <div>
                                    <div className="text-[10px] font-medium text-text-muted uppercase tracking-wider">{t('home.balanceDue', 'Balance Due')}</div>
                                    <div className="font-sans text-xl font-bold text-green mt-0.5">₹0</div>
                                  </div>
                                  <span className="flex items-center gap-1.5 font-sans text-[10px] font-bold text-green bg-green-light px-3 py-1.5 rounded-full shrink-0 whitespace-nowrap border border-green-200/50">
                                    <CheckCircle2 className="w-3.5 h-3.5 text-green" />
                                    {prevWeek.currentWeekOs < 0
                                      ? t('home.paidToBank', 'Paid to Bank')
                                      : t('home.paidToLetzryd', 'Paid to LetzRyd')}
                                  </span>
                                </div>
                              ) : (
                                <div className="flex justify-between items-center gap-2 pt-0.5">
                                  <div>
                                    <div className="text-[10px] font-medium text-text-muted uppercase tracking-wider">Total Outstanding Due</div>
                                    <div className="font-sans text-xl font-extrabold text-red-600 mt-0.5">
                                      -₹{(() => {
                                        const due = Math.max(0, (prevWeek.toCollect || prevWeek.currentWeekOs || 0) - (prevWeek.paidAmount || 0)) + (driverUser.depositPending || 0);
                                        return due.toLocaleString('en-IN', {
                                          minimumFractionDigits: due % 1 !== 0 ? 2 : 0,
                                          maximumFractionDigits: 2,
                                        });
                                      })()}
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-2 shrink-0" onClick={(e) => e.stopPropagation()}>
                                    <span className="font-sans text-[10px] font-bold text-red-600 bg-red-50 border border-red-200 px-2 py-0.5 rounded-md">
                                      Due
                                    </span>
                                    <button
                                      onClick={() => {
                                        setDriverWeekIndex(1); // Point to Last Week (Week 29)
                                        navigateTo('settle');
                                      }}
                                      className="px-3.5 py-1.5 rounded-lg bg-primary hover:bg-primary-hover font-sans text-xs font-semibold text-white shadow-xs cursor-pointer transition-all hover:scale-105"
                                    >
                                      Pay
                                    </button>
                                  </div>
                                </div>
                              )}
                            </>
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
                      ) : (
                        <div
                          onClick={() => navigateTo('operator')}
                          className="bg-surface border border-border/80 hover:border-primary/50 rounded-2xl p-3.5 shadow-xs text-left space-y-3 font-sans cursor-pointer transition-all hover:shadow-md group"
                        >
                          <div className="flex justify-between items-center text-xs border-b border-border/60 pb-2">
                            <span className="font-bold text-text flex items-center gap-1.5 uppercase tracking-wider text-[10px] group-hover:text-primary transition-colors">
                              <AlertCircle className="h-3.5 w-3.5 text-amber-600" />
                              FLEET COLLECTION DUES
                            </span>
                            <span className="text-[10px] font-mono text-text-muted bg-bg px-2 py-0.5 rounded-md border border-border/50">
                              Week #{activeWeek.weekNumber} • {operatorFleet.operatorCode || 'FLEET'}
                            </span>
                          </div>

                          <div className="flex justify-between items-center gap-2 pt-0.5">
                            <div>
                              <div className="text-[10px] font-medium text-text-muted uppercase tracking-wider">Total Outstanding Due</div>
                              <div className="font-sans text-xl font-extrabold text-red-600 mt-0.5">
                                -₹{(() => {
                                  const opDue = (operatorFleet.vehicles.reduce((sum, v) => (v.currentWeekOs > 0 ? sum + v.currentWeekOs : sum), 0) + (operatorFleet.depositPending ?? 0));
                                  return opDue.toLocaleString('en-IN', {
                                    minimumFractionDigits: opDue % 1 !== 0 ? 2 : 0,
                                    maximumFractionDigits: 2,
                                  });
                                })()}
                              </div>
                            </div>
                            <div className="flex items-center gap-2 shrink-0" onClick={(e) => e.stopPropagation()}>
                              <span className="font-sans text-[10px] font-bold text-red-600 bg-red-50 border border-red-200 px-2 py-0.5 rounded-md">
                                Due
                              </span>
                              <button
                                onClick={() => navigateTo('settle')}
                                className="px-3.5 py-1.5 rounded-lg bg-primary hover:bg-primary-hover font-sans text-xs font-semibold text-white shadow-xs cursor-pointer transition-all hover:scale-105"
                              >
                                Pay
                              </button>
                            </div>
                          </div>

                          {/* Merged Security Deposit Strip for Operator */}
                          <div className="border-t border-border/60 pt-2.5 flex items-center justify-between text-xs">
                            <span className="font-bold text-text uppercase tracking-wider text-[10px]">
                              FLEET SECURITY DEPOSIT
                            </span>
                            <div className="flex items-center gap-2 text-[10px] font-sans">
                              <span className="bg-green-50 text-green-700 border border-green-200/70 px-2.5 py-0.5 rounded-full font-bold">
                                Paid: ₹{(operatorFleet.depositPaidSoFar ?? 0).toLocaleString('en-IN', { minimumFractionDigits: (operatorFleet.depositPaidSoFar ?? 0) % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}
                              </span>
                              <span className="bg-amber-50 text-amber-700 border border-amber-200/70 px-2.5 py-0.5 rounded-full font-bold">
                                Pending: ₹{(operatorFleet.depositPending ?? 0).toLocaleString('en-IN', { minimumFractionDigits: (operatorFleet.depositPending ?? 0) % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}
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
                            className="px-2 py-1 flex items-center justify-center gap-2 cursor-pointer group hover:opacity-85 transition-all text-left"
                          >
                            <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center group-hover:bg-indigo-600 group-hover:text-white transition-all shadow-2xs shrink-0">
                              <Headset className="h-3.5 w-3.5" />
                            </div>
                            <div className="min-w-0">
                              <span className="font-bold text-[10px] text-text leading-tight block truncate">{t('home.driverManagerTitle', 'Driver Manager')}</span>
                              <span className="text-[8.5px] text-text-muted leading-none block mt-0.5 truncate">{t('home.driverManagerSub', 'Call / Chat')}</span>
                            </div>
                          </button>

                          {/* 2. Refer Driver */}
                          <button
                            onClick={() => navigateTo('referral')}
                            className="px-2 py-1 flex items-center justify-center gap-2 cursor-pointer group hover:opacity-85 transition-all text-left"
                          >
                            <div className="w-7 h-7 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center group-hover:bg-purple-600 group-hover:text-white transition-all shadow-2xs shrink-0">
                              <Gift className="h-3.5 w-3.5" />
                            </div>
                            <div className="min-w-0">
                              <span className="font-bold text-[10px] text-text leading-tight block truncate">{t('home.referDriverTitle', 'Refer Driver')}</span>
                              <span className="text-[8.5px] text-text-muted leading-none block mt-0.5 truncate">{t('home.referDriverSub', 'Earn ₹1,000')}</span>
                            </div>
                          </button>

                          {/* 3. Emergency SOS */}
                          <button
                            onClick={() => setIsSosModalOpen(true)}
                            className="px-2 py-1 flex items-center justify-center gap-2 cursor-pointer group hover:opacity-85 transition-all text-left"
                          >
                            <div className="w-7 h-7 rounded-lg bg-red-50 text-red-600 flex items-center justify-center group-hover:bg-red-600 group-hover:text-white transition-all shadow-2xs shrink-0">
                              <AlertTriangle className="h-3.5 w-3.5" />
                            </div>
                            <div className="min-w-0">
                              <span className="font-bold text-[10px] text-text leading-tight block truncate">{t('home.emergencySosTitle', 'Emergency SOS')}</span>
                              <span className="text-[8.5px] text-text-muted leading-none block mt-0.5 truncate">{t('home.emergencySosSub', 'Safety & Hub')}</span>
                            </div>
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {currentScreen === 'hisaab' && (() => {
                    const currentVeh = loginType === 'operator'
                      ? (selectedVehicleObj || operatorFleet.vehicles[0])
                      : null;
                    const activeWeeks = (loginType === 'operator' && currentVeh?.hisaabWeeks && currentVeh.hisaabWeeks.length > 0)
                      ? currentVeh.hisaabWeeks
                      : hisaabWeeks;

                    return (
                      <HisaabScreen
                        weeks={activeWeeks}
                        weekIndex={driverWeekIndex}
                        onPrevWeek={() => setDriverWeekIndex(prev => Math.min(prev + 1, activeWeeks.length - 1))}
                        onNextWeek={() => setDriverWeekIndex(prev => Math.max(prev - 1, 0))}
                        loginType={loginType}
                        fleetVehicles={operatorFleet.vehicles}
                        selectedVehicleNumber={selectedVehicleNumber || operatorFleet.vehicles[0]?.number}
                        onSelectVehicle={(num) => {
                          setSelectedVehicleNumber(num);
                          setDriverWeekIndex(0);
                          const target = operatorFleet.vehicles.find(v => v.number === num || v.number.replace(/\s+/g, '') === num.replace(/\s+/g, ''));
                          if (target && target.hisaabWeeks && target.hisaabWeeks.length > 0) {
                            setHisaabWeeks(target.hisaabWeeks);
                          }
                        }}
                        onPayClick={() => navigateTo('settle')}
                        t={t}
                      />
                    );
                  })()}

                  {currentScreen === 'settle' && (() => {
                    const currentH = hisaabWeeks[driverWeekIndex];
                    const rawDue = currentH ? Math.max(0, (currentH.toCollect || currentH.currentWeekOs || 0)) : 0;
                    const paidSoFar = currentH?.paidAmount || 0;
                    const remainingHisaabDue = Math.max(0, rawDue - paidSoFar);
                    const pendingDep = loginType === 'operator' ? (operatorFleet.depositPending ?? 0) : (driverUser.depositPending ?? 0);
                    const challanAmt = loginType === 'operator' ? 0 : (currentH?.challan || 0);

                    const totalOperatorDue = operatorFleet.vehicles.reduce((sum, v) => (v.currentWeekOs > 0 ? sum + v.currentWeekOs : sum), 0);
                    const finalHisaabAmount = loginType === 'operator' ? totalOperatorDue : remainingHisaabDue;
                    const finalTotalAmount = finalHisaabAmount + pendingDep + challanAmt;

                    return (
                      <SettleScreen
                        amount={finalTotalAmount}
                        hisaabAmount={finalHisaabAmount}
                        pendingDeposit={pendingDep}
                        challansAmount={challanAmt}
                        weekRange={`${currentH?.weekStart} to ${currentH?.weekEnd}`}
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
                    <SupportScreen
                      user={driverUser}
                      tickets={tickets}
                      hotline={SUPPORT_HOTLINE}
                      onNewTicket={() => setIsNewTicketOpen(true)}
                      onSelectTicket={(ticket) => setSelectedTicket(ticket)}
                      onOpenSos={() => setIsSosModalOpen(true)}
                      t={t}
                    />
                  )}

                  {currentScreen === 'profile' && (
                    <ProfileScreen
                      user={driverUser}
                      loginType={loginType}
                      onUpdateContact={handleUpdateContact}
                      t={t}
                    />
                  )}

                  {currentScreen === 'referral' && (
                    <ReferralScreen
                      driverCode={'LETZ' + driverUser.phone}
                      onCopy={handleCopyReferralCode}
                      onBack={goBack}
                      t={t}
                    />
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
