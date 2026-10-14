import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'motion/react';
import { 
  X, Sparkles, Copy, Send, ReceiptIndianRupee, FileWarning, Award, CheckCircle, 
  Bell, PhoneCall, Building2, ShieldCheck, Car, FileText, RefreshCw, Mail, MapPin, 
  Phone, CheckCircle2, ChevronRight, Info, ExternalLink, BadgeCheck, Users
} from 'lucide-react';
import { Ticket, Notification } from '../types';

interface ReferralModalProps {
  onClose: () => void;
  driverCode: string;
  onCopy: () => void;
  t: (key: string, fallback: string) => string;
}

export const ReferralModal: React.FC<ReferralModalProps> = ({ onClose, driverCode, onCopy, t }) => {
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  return (
    <div 
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      className="absolute inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm overflow-y-auto"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-surface border border-border rounded-xl w-full max-w-sm p-5 shadow-lg relative text-left font-sans space-y-4 my-auto"
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-8 h-8 rounded-lg border border-border bg-surface flex items-center justify-center text-text-muted hover:text-text cursor-pointer transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-green-light text-green flex items-center justify-center shrink-0">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-sans text-base font-bold text-text">{t('refer.title', 'Refer Driver & Earn ₹1,000')}</h3>
            <p className="font-sans text-xs text-text-muted mt-0.5">{t('refer.subtitle', 'Share your referral link with EV drivers joining LetzRyd.')}</p>
          </div>
        </div>

        <div className="bg-bg border border-border rounded-xl p-4 space-y-2">
          <p className="font-sans text-[10px] font-bold text-text-muted uppercase tracking-wider">{t('refer.yourCode', 'YOUR REFERRAL CODE')}</p>
          <div className="flex items-center justify-between bg-surface border border-border rounded-lg p-2.5">
            <span className="font-sans text-sm font-bold text-primary">{driverCode}</span>
            <button
              onClick={onCopy}
              className="flex items-center gap-1 px-3 py-1 rounded-md bg-primary hover:bg-primary-hover text-white text-xs font-semibold cursor-pointer shadow-sm transition-colors"
            >
              <Copy className="w-3.5 h-3.5" />
              {t('refer.copyCode', 'Copy Code')}
            </button>
          </div>
        </div>

        <div className="p-3 rounded-lg bg-green-light/40 border border-green/30 font-sans text-xs text-green font-medium">
          🎁 {t('refer.rewardInfo', 'Receive ₹1,000 credit directly in your next weekly Hisaab when your referred driver completes 50 rides.')}
        </div>
      </motion.div>
    </div>
  );
};

interface NewTicketModalProps {
  onClose: () => void;
  categories: string[];
  onSubmit: (category: string, subject: string, description: string) => void;
  t: (key: string, fallback: string) => string;
}

export const NewTicketModal: React.FC<NewTicketModalProps> = ({ onClose, categories, onSubmit, t }) => {
  const [category, setCategory] = useState(categories[0] || '');
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject.trim() || !description.trim()) return;
    onSubmit(category, subject, description);
  };

  return (
    <div 
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      className="absolute inset-0 z-50 flex items-center justify-center p-3 bg-black/60 backdrop-blur-sm overflow-y-auto"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-surface border border-border rounded-xl w-full p-5 shadow-lg relative text-left font-sans my-auto"
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-8 h-8 rounded-lg border border-border bg-surface flex items-center justify-center text-text-muted hover:text-text cursor-pointer transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        <h3 className="font-sans text-lg font-bold text-text mb-3">{t('support.newTicket', 'Raise Support Ticket')}</h3>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="flex flex-col gap-1">
            <label className="font-sans text-xs font-semibold text-text-muted">{t('support.ticketCategory', 'Ticket Category')}</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="h-10 w-full rounded-lg border border-border bg-surface px-3 font-sans text-xs text-text outline-none focus:border-green"
            >
              {categories.map((c) => <option key={c} value={c}>{t('ticketCategory.' + c, c)}</option>)}
            </select>
          </div>

          <div className="flex flex-col gap-1">
            <label className="font-sans text-xs font-semibold text-text-muted">{t('support.issueSubject', 'Issue Subject')}</label>
            <input
              type="text"
              required
              placeholder={t('support.subjectPlaceholder', 'Summary of the issue...')}
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="h-10 w-full rounded-lg border border-border bg-surface px-3 font-sans text-xs text-text placeholder:text-text-dim outline-none focus:border-green"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="font-sans text-xs font-semibold text-text-muted">{t('support.detailedDescription', 'Detailed Description')}</label>
            <textarea
              required
              rows={3}
              placeholder={t('support.descriptionPlaceholder', 'Describe what happened, relevant week dates, or vehicle issues...')}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-lg border border-border bg-surface p-3 font-sans text-xs text-text placeholder:text-text-dim outline-none focus:border-green resize-none leading-relaxed"
            />
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg border border-border bg-surface font-sans text-xs font-semibold text-text-muted hover:text-text cursor-pointer transition-colors"
            >
              {t('common.cancel', 'Cancel')}
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-primary hover:bg-primary-hover font-sans text-xs font-semibold text-white cursor-pointer shadow-sm transition-colors flex items-center gap-1.5"
            >
              <Send className="w-3.5 h-3.5" />
              {t('support.submitTicket', 'Submit Ticket')}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
};

interface TicketDetailModalProps {
  ticket: Ticket;
  onClose: () => void;
  t: (key: string, fallback: string) => string;
}

export const TicketDetailModal: React.FC<TicketDetailModalProps> = ({ ticket, onClose, t }) => {
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  return (
    <div 
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      className="absolute inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm overflow-y-auto"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-surface border border-border rounded-xl w-full max-w-lg p-5 shadow-lg relative text-left font-sans space-y-3 my-auto"
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-8 h-8 rounded-lg border border-border bg-surface flex items-center justify-center text-text-muted hover:text-text cursor-pointer transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-2 pr-8">
          <span className="font-sans text-xs font-bold text-primary">{ticket.id}</span>
          <span className="font-sans text-xs font-semibold text-text-muted">• {t('ticketCategory.' + ticket.category, ticket.category)}</span>
        </div>

        <h3 className="font-sans text-lg font-bold text-text">{ticket.subject}</h3>

        <div className="p-3.5 rounded-lg bg-bg border border-border">
          <p className="font-sans text-xs font-semibold text-text-muted mb-1">{t('ticketDetail.issueDetails', 'Issue Details')}</p>
          <p className="font-sans text-xs text-text leading-relaxed">{ticket.description}</p>
        </div>

        {ticket.response && (
          <div className="p-3.5 rounded-lg bg-green-light border border-green/30">
            <p className="font-sans text-xs font-bold text-green flex items-center gap-1.5 mb-1">
              <CheckCircle className="w-4 h-4" /> {t('ticketDetail.resolutionTitle', 'LetzRyd Support Resolution')}
            </p>
            <p className="font-sans text-xs text-green leading-relaxed">{ticket.response}</p>
          </div>
        )}

        <div className="flex justify-end pt-1">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-primary hover:bg-primary-hover text-white font-sans text-xs font-semibold cursor-pointer shadow-sm transition-colors"
          >
            {t('ticketDetail.closeBtn', 'Close')}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

interface NotificationModalProps {
  onClose: () => void;
  notifications: Notification[];
  onMarkAllRead: () => void;
  t: (key: string, fallback: string) => string;
}

export const NotificationModal: React.FC<NotificationModalProps> = ({ onClose, notifications, onMarkAllRead, t }) => {
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  const getIcon = (iconName: string) => {
    switch (iconName) {
      case 'ReceiptIndianRupee': return <ReceiptIndianRupee className="w-4 h-4 text-green" />;
      case 'FileWarning': return <FileWarning className="w-4 h-4 text-amber-600" />;
      case 'Award': return <Award className="w-4 h-4 text-primary" />;
      case 'CheckCircle': return <CheckCircle className="w-4 h-4 text-green" />;
      default: return <Bell className="w-4 h-4 text-primary" />;
    }
  };

  return (
    <div 
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      className="absolute inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm overflow-y-auto"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-surface border border-border rounded-xl w-full max-w-lg p-5 shadow-lg relative text-left font-sans space-y-3 my-auto"
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-8 h-8 rounded-lg border border-border bg-surface flex items-center justify-center text-text-muted hover:text-text cursor-pointer transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-center justify-between border-b border-border pb-2.5 pr-8">
          <h3 className="font-sans text-base font-bold text-text flex items-center gap-2">
            <Bell className="w-5 h-5 text-primary" /> {t('notif.title', 'Notifications & Updates')}
          </h3>
          {notifications.some(n => !n.read) && (
            <button onClick={onMarkAllRead} className="font-sans text-xs font-semibold text-primary hover:underline cursor-pointer">{t('notif.markAllRead', 'Mark All Read')}</button>
          )}
        </div>

        <div className="space-y-2.5 max-h-[50vh] overflow-y-auto pr-1">
          {notifications.length === 0 ? (
            <div className="py-8 text-center text-text-muted">{t('notif.empty', 'No new notifications')}</div>
          ) : (
            notifications.map((n) => (
              <div key={n.id} className={`p-3.5 rounded-lg border flex gap-3 ${n.read ? 'bg-surface border-border' : 'bg-green-light/40 border-green/30'}`}>
                <div className="w-8 h-8 rounded-lg bg-bg flex items-center justify-center shrink-0 border border-border">{getIcon(n.icon)}</div>
                <div className="flex-1 space-y-1">
                  <div className="flex justify-between items-start">
                    <p className="font-sans text-xs font-bold text-text">{n.title}</p>
                    {!n.read && <span className="w-2 h-2 rounded-full bg-primary shrink-0 mt-1" />}
                  </div>
                  <p className="font-sans text-xs text-text-muted leading-relaxed">{n.message}</p>
                  <p className="font-sans text-[10px] text-text-dim pt-0.5">{n.time}</p>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="flex justify-end pt-1">
          <button onClick={onClose} className="px-4 py-2 rounded-lg bg-primary hover:bg-primary-hover text-white font-sans text-xs font-semibold cursor-pointer shadow-sm transition-colors">
            {t('notif.closeFeed', 'Close Feed')}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

/* =========================================================================
   EMERGENCY SOS MODAL
   ========================================================================= */
interface EmergencySosModalProps {
  onClose: () => void;
  isActivated: boolean;
  sosTime: string | null;
  onTriggerSos: (timeStr: string) => void;
  onCancelSos: () => void;
  onReportIncident: (type: string, loc: string, drivable: boolean) => void;
  hotline: string;
  t: (key: string, fallback: string) => string;
}

export const EmergencySosModal: React.FC<EmergencySosModalProps> = ({
  onClose,
  isActivated,
  sosTime,
  onTriggerSos,
  onCancelSos,
  onReportIncident,
  hotline,
  t
}) => {
  const [incidentType, setIncidentType] = useState('Roadside Breakdown');
  const [location, setLocation] = useState('');
  const [isDrivable, setIsDrivable] = useState(false);
  const [incidentSubmitted, setIncidentSubmitted] = useState(false);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  const handleIncidentSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!location.trim()) return;
    onReportIncident(incidentType, location, isDrivable);
    setIncidentSubmitted(true);
    setTimeout(() => {
      setIncidentSubmitted(false);
      onClose();
    }, 2000);
  };

  const handlePressSos = () => {
    const timeNow = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
    onTriggerSos(timeNow);
  };

  return (
    <div 
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      className="absolute inset-0 z-50 flex items-center justify-center p-3 bg-black/65 backdrop-blur-sm overflow-y-auto"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-surface border border-red-200/80 rounded-2xl w-full max-w-sm p-4 shadow-2xl relative text-left font-sans space-y-3.5 my-auto max-h-[92%] overflow-y-auto no-scrollbar"
      >
        <button
          onClick={onClose}
          className="absolute top-3.5 right-3.5 w-7 h-7 rounded-lg border border-border bg-bg flex items-center justify-center text-text-muted hover:text-text cursor-pointer transition-colors"
        >
          <X className="w-3.5 h-3.5" />
        </button>

        {/* HEADER */}
        <div className="flex items-center gap-2.5 pr-7 border-b border-border/60 pb-2.5">
          <div className="w-8 h-8 rounded-xl bg-red-100 text-red-600 flex items-center justify-center shrink-0 border border-red-200 font-bold">
            🚨
          </div>
          <div>
            <h3 className="font-sans text-sm font-extrabold text-red-700 leading-tight">
              {t('sos.title', 'Emergency SOS Safety Center')}
            </h3>
            <p className="font-sans text-[10px] text-text-muted mt-0.5">
              {t('sos.controlHub', 'LetzRyd Central Control Hub (24x7)')}
            </p>
          </div>
        </div>

        {/* ACTIVE SOS STATE */}
        {isActivated ? (
          <div className="space-y-3">
            <div className="bg-red-500/10 border-2 border-red-500 rounded-2xl p-4 text-center space-y-2 animate-pulse">
              <div className="text-3xl">📡</div>
              <h4 className="font-sans text-base font-black text-red-600">
                {t('sos.activated', 'Emergency SOS Active!')}
              </h4>
              <p className="font-sans text-xs font-semibold text-text leading-relaxed">
                {t('sos.hubNotified', 'Central Control Hub notified at')} <strong>{sosTime || t('common.justNow', 'Just now')}</strong>. {t('sos.matchingCoords', 'Dispatchers are matching vehicle coordinates.')}
              </p>
            </div>

            <div className="flex flex-col gap-2">
              <a
                href={`tel:${hotline}`}
                className="w-full py-3 rounded-xl bg-red-600 hover:bg-red-700 text-white font-sans text-xs font-extrabold flex items-center justify-center gap-2 cursor-pointer shadow-md transition-all active:scale-98"
              >
                <PhoneCall className="w-4 h-4" />
                <span>{t('sos.callHelpline', 'Call Helpline')}: {hotline}</span>
              </a>
              <button
                type="button"
                onClick={onCancelSos}
                className="w-full py-2.5 rounded-xl border border-border bg-bg text-text-muted hover:text-text font-sans text-xs font-bold cursor-pointer transition-colors"
              >
                {t('sos.cancelAlert', 'Cancel SOS Alert')}
              </button>
            </div>
          </div>
        ) : (
          /* INACTIVE SOS TRIGGER & REPORT FORM */
          <div className="space-y-3">
            {/* SOS BUTTON HERO */}
            <div className="bg-red-50/70 border border-red-200/80 rounded-2xl p-3 text-center space-y-2">
              <p className="font-sans text-[11px] text-text font-medium leading-tight">
                {t('sos.subtitle', 'Press emergency button to transmit real-time coordinates to dispatch.')}
              </p>
              <button
                type="button"
                onClick={handlePressSos}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-700 hover:to-rose-700 text-white font-sans text-xs font-black tracking-wider uppercase flex items-center justify-center gap-2 cursor-pointer shadow-lg shadow-red-600/30 transition-all active:scale-95"
              >
                <span className="w-2.5 h-2.5 rounded-full bg-white animate-ping"></span>
                {t('sos.pressToAlert', 'Press to Alert Hub')}
              </button>
              <a
                href={`tel:${hotline}`}
                className="inline-flex items-center gap-1 font-sans text-[10px] font-bold text-red-700 hover:underline pt-0.5"
              >
                <PhoneCall className="w-3 h-3" />
                {t('sos.directHotline', 'Direct Hotline')}: {hotline}
              </a>
            </div>

            {/* ROADSIDE BREAKDOWN / ACCIDENT FORM */}
            <div className="bg-surface border border-border/80 rounded-2xl p-3 space-y-2.5">
              <h4 className="font-sans text-[11px] font-bold text-text uppercase tracking-wider text-text-muted">
                {t('sos.reportAccident', 'Report Accident or Roadside Breakdown')}
              </h4>

              {incidentSubmitted ? (
                <div className="p-3 bg-green-light border border-green/30 text-green rounded-xl text-xs font-bold flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 shrink-0" />
                  <span>{t('sos.reportSubmitted', 'Report submitted! Dispatcher is reviewing your details.')}</span>
                </div>
              ) : (
                <form onSubmit={handleIncidentSubmit} className="space-y-2.5 text-xs font-sans">
                  <div>
                    <label className="text-text-muted font-medium block mb-1">{t('sos.incidentType', 'Issue Category')}</label>
                    <select
                      value={incidentType}
                      onChange={(e) => setIncidentType(e.target.value)}
                      className="w-full h-8.5 rounded-xl border border-border bg-bg px-2.5 font-bold text-text text-xs outline-none focus:border-red-500 cursor-pointer"
                    >
                      <option value="Roadside Breakdown">{t('sos.incidentRoadside', 'Roadside Breakdown')}</option>
                      <option value="Minor Collision / Accident">{t('sos.incidentCollision', 'Minor Collision / Accident')}</option>
                      <option value="Flat Tyre / Suspension">{t('sos.incidentTyre', 'Flat Tyre / Suspension')}</option>
                      <option value="EV Battery / Range Issue">{t('sos.incidentBattery', 'EV Battery / Range Issue')}</option>
                      <option value="Medical Emergency">{t('sos.incidentMedical', 'Medical Emergency')}</option>
                      <option value="Other Safety Incident">{t('sos.incidentOther', 'Other Safety Incident')}</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-text-muted font-medium block mb-1">{t('sos.location', 'Current Location / Nearest Landmark')}</label>
                    <input
                      type="text"
                      required
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      placeholder={t('sos.locationPlaceholder', 'e.g. Near Hitec City Metro Station, Outer Ring Road')}
                      className="w-full h-8.5 rounded-xl border border-border bg-bg px-2.5 font-medium text-text text-xs outline-none focus:border-red-500"
                    />
                  </div>

                  <div className="flex items-center justify-between pt-0.5">
                    <span className="text-text-muted font-medium">{t('sos.isDrivable', 'Is Vehicle Drivable?')}</span>
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => setIsDrivable(true)}
                        className={`px-2.5 py-1 rounded-lg text-xs font-bold cursor-pointer transition-all ${
                          isDrivable ? 'bg-green text-white shadow-2xs' : 'bg-bg text-text-muted border border-border'
                        }`}
                      >
                        {t('common.yes', 'Yes')}
                      </button>
                      <button
                        type="button"
                        onClick={() => setIsDrivable(false)}
                        className={`px-2.5 py-1 rounded-lg text-xs font-bold cursor-pointer transition-all ${
                          !isDrivable ? 'bg-red-600 text-white shadow-2xs' : 'bg-bg text-text-muted border border-border'
                        }`}
                      >
                        {t('common.no', 'No')}
                      </button>
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="w-full h-9 mt-1 rounded-xl bg-primary hover:bg-primary-hover text-white font-sans text-xs font-bold cursor-pointer transition-all shadow-xs"
                  >
                    {t('sos.submitReport', 'Submit Incident Report')}
                  </button>
                </form>
              )}
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
};

export interface CompanyServicesLegalModalProps {
  isOpen?: boolean;
  onClose: () => void;
  t?: (key: string, fallback: string) => string;
}

export const CompanyServicesLegalModal: React.FC<CompanyServicesLegalModalProps> = ({
  isOpen = true,
  onClose,
  t = (_k, fb) => fb
}) => {
  const [activeSection, setActiveSection] = useState<'about' | 'contact' | 'refund' | 'terms' | 'privacy'>('about');
  const [contactForm, setContactForm] = useState({
    firstName: '',
    lastName: '',
    email: '',
    message: ''
  });
  const [contactSubmitted, setContactSubmitted] = useState(false);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  if (!isOpen) return null;

  const scrollToSection = (sectionId: string, sectionKey: 'about' | 'contact' | 'refund' | 'terms' | 'privacy') => {
    setActiveSection(sectionKey);
    const container = scrollContainerRef.current;
    const target = document.getElementById(sectionId);
    if (container && target) {
      const targetOffset = target.offsetTop - container.offsetTop;
      container.scrollTo({ top: Math.max(0, targetOffset - 6), behavior: 'smooth' });
    }
    if (cardRef.current) {
      cardRef.current.scrollTop = 0;
    }
  };

  const handleContactSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!contactForm.firstName || !contactForm.email || !contactForm.message) return;
    setContactSubmitted(true);
  };

  return (
    <div 
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      className="absolute inset-0 z-50 flex items-center justify-center p-2.5 bg-black/60 backdrop-blur-xs overflow-hidden"
    >
      <div
        ref={cardRef}
        onScroll={(e) => { e.currentTarget.scrollTop = 0; }}
        className="bg-surface border border-border rounded-2xl w-full max-w-[345px] shadow-2xl relative text-left font-sans flex flex-col max-h-[85vh] h-[85vh] my-auto overflow-hidden animate-in fade-in duration-150"
      >
        {/* Top Header */}
        <div className="p-3 bg-gradient-to-r from-[#0A1650] to-[#14267A] text-white flex items-start justify-between shrink-0 sticky top-0 z-20">
          <div className="space-y-0.5 pr-2">
            <h2 className="text-[11.5px] font-bold tracking-tight leading-snug">
              SAMVREEDDHI MOBILITY PRIVATE LIMITED
            </h2>
            <p className="text-[10px] text-white/80">
              Operating Brand: LetzRyd • Services & Policies
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-6 h-6 rounded-lg bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-colors cursor-pointer shrink-0"
            aria-label="Close"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Quick Navigation Pills */}
        <div className="flex items-center gap-1.5 px-3 py-2 bg-bg border-b border-border/80 overflow-x-auto no-scrollbar shrink-0 text-[10px] font-medium sticky top-0 z-10">
          <button
            onClick={() => scrollToSection('legal-about', 'about')}
            className={`px-2 py-1 rounded-md shrink-0 transition-colors ${
              activeSection === 'about' ? 'bg-primary text-white font-semibold' : 'bg-surface border border-border text-text-muted hover:text-text'
            }`}
          >
            About & Services
          </button>
          <button
            onClick={() => scrollToSection('legal-contact', 'contact')}
            className={`px-2 py-1 rounded-md shrink-0 transition-colors ${
              activeSection === 'contact' ? 'bg-primary text-white font-semibold' : 'bg-surface border border-border text-text-muted hover:text-text'
            }`}
          >
            Headquarters & Contact
          </button>
          <button
            onClick={() => scrollToSection('legal-refund', 'refund')}
            className={`px-2 py-1 rounded-md shrink-0 transition-colors ${
              activeSection === 'refund' ? 'bg-primary text-white font-semibold' : 'bg-surface border border-border text-text-muted hover:text-text'
            }`}
          >
            Refund Policy
          </button>
          <button
            onClick={() => scrollToSection('legal-terms', 'terms')}
            className={`px-2 py-1 rounded-md shrink-0 transition-colors ${
              activeSection === 'terms' ? 'bg-primary text-white font-semibold' : 'bg-surface border border-border text-text-muted hover:text-text'
            }`}
          >
            Terms of Service
          </button>
          <button
            onClick={() => scrollToSection('legal-privacy', 'privacy')}
            className={`px-2 py-1 rounded-md shrink-0 transition-colors ${
              activeSection === 'privacy' ? 'bg-primary text-white font-semibold' : 'bg-surface border border-border text-text-muted hover:text-text'
            }`}
          >
            Privacy Policy
          </button>
        </div>

        {/* Scrollable Content Container */}
        <div 
          ref={scrollContainerRef}
          className="flex-1 min-h-0 p-3 overflow-y-auto space-y-4 text-[10px] text-text leading-relaxed"
        >
          {/* SECTION 1: ABOUT US & SERVICES */}
          <div id="legal-about" className="space-y-2 pt-0.5">
            <h3 className="font-bold text-[11px] text-text border-b border-border/70 pb-1 flex items-center gap-1.5">
              <Car className="w-3.5 h-3.5 text-primary" />
              <span>About LetzRyd & Services</span>
            </h3>

            <div className="border border-border/80 rounded-xl p-2.5 bg-surface space-y-2">
              <p className="text-text-muted leading-relaxed">
                LetzRyd provides vehicles and drivers to ride hailing service companies, as well as opportunities for vehicle ownership (including leasing) to drivers and their management companies. Through the vehicle and driver management platform, LetzRyd aims to improve driver incomes by increasing vehicle utilization rates.
              </p>
              
              <div className="border-t border-border/50 pt-2 space-y-1">
                <span className="font-bold text-[10.5px] text-text block">Leadership & Founding Team</span>
                <div className="grid grid-cols-3 gap-1.5 pt-0.5">
                  <div className="p-1.5 rounded-lg bg-bg border border-border/60 text-center">
                    <span className="font-semibold text-text block text-[10px]">Tarun Jain</span>
                    <span className="text-[9px] text-text-muted">Founder</span>
                  </div>
                  <div className="p-1.5 rounded-lg bg-bg border border-border/60 text-center">
                    <span className="font-semibold text-text block text-[10px]">Kushagra Dokania</span>
                    <span className="text-[9px] text-text-muted">Founder</span>
                  </div>
                  <div className="p-1.5 rounded-lg bg-bg border border-border/60 text-center">
                    <span className="font-semibold text-text block text-[10px]">Sarvagna G</span>
                    <span className="text-[9px] text-text-muted">Founder</span>
                  </div>
                </div>
              </div>

              <div className="border-t border-border/50 pt-2 space-y-1.5">
                <span className="font-bold text-[10.5px] text-text block">Core Operational Offerings</span>
                <div className="space-y-1 text-text-muted">
                  <div className="p-1.5 rounded-lg bg-bg/50 border border-border/50">
                    <strong className="text-text block text-[10px]">1. Commercial Fleet Leasing:</strong>
                    Vehicle allocation to driver partners for platform commercial ride operations.
                  </div>
                  <div className="p-1.5 rounded-lg bg-bg/50 border border-border/50">
                    <strong className="text-text block text-[10px]">2. Vehicle Custody Management:</strong>
                    Security deposit collection and tracking during commercial partner onboarding.
                  </div>
                  <div className="p-1.5 rounded-lg bg-bg/50 border border-border/50">
                    <strong className="text-text block text-[10px]">3. Settlement & Reconciliation Platform:</strong>
                    Netting weekly platform trip collections against rental agreements with digital settlements.
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* SECTION 2: HEADQUARTERS & CONTACT */}
          <div id="legal-contact" className="space-y-2 pt-1">
            <h3 className="font-bold text-[11px] text-text border-b border-border/70 pb-1 flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-primary" />
              <span>Headquarters & Contact</span>
            </h3>

            <div className="border border-border/80 rounded-xl p-2.5 bg-surface space-y-2">
              <div>
                <span className="font-bold text-[10.5px] text-text block">SAMVREEDDHI MOBILITY PRIVATE LIMITED</span>
                <p className="text-text-muted mt-0.5 leading-relaxed">
                  4th floor, 503-A, Sir M. Visvesvaraya Rd, opp. Krishna Kuteer, above Leon Grill, BTM 6th Stage, Arekere, Bengaluru, Karnataka 560076
                </p>
                <a
                  href="https://maps.app.goo.gl/nZGVYU1hpsR2W77w8?g_st=awb"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-primary hover:underline font-semibold mt-1"
                >
                  <span>View on Google Maps</span>
                  <ExternalLink className="w-2.5 h-2.5" />
                </a>
              </div>

              <div className="border-t border-border/50 pt-2 space-y-1.5">
                <div className="flex items-center justify-between py-0.5 border-b border-border/40">
                  <span className="text-text-muted">Contact Email:</span>
                  <a href="mailto:admin@letzryd.com" className="text-primary font-semibold hover:underline">
                    admin@letzryd.com
                  </a>
                </div>
                <div className="flex items-center justify-between py-0.5 border-b border-border/40">
                  <span className="text-text-muted">Contact Phone:</span>
                  <a href="tel:+919035239090" className="text-text font-semibold hover:text-primary">
                    +91 9035239090
                  </a>
                </div>
                <div className="flex items-center justify-between py-0.5">
                  <span className="text-text-muted">Grievance Officer:</span>
                  <span className="text-text font-semibold">Tarun Jain (admin@letzryd.com)</span>
                </div>
              </div>

              {/* Inquiry Form */}
              <div className="border-t border-border/50 pt-2.5 space-y-2">
                <span className="font-bold text-[10.5px] text-text block">Send a Message</span>
                {contactSubmitted ? (
                  <div className="p-2.5 rounded-lg bg-green-light/40 border border-green/30 text-green font-medium flex items-center gap-1.5">
                    <CheckCircle className="w-3.5 h-3.5 shrink-0" />
                    <span>Thank you. Your message has been received by our support team.</span>
                  </div>
                ) : (
                  <form onSubmit={handleContactSubmit} className="space-y-2">
                    <div className="grid grid-cols-2 gap-1.5">
                      <input
                        type="text"
                        required
                        placeholder="First Name*"
                        value={contactForm.firstName}
                        onChange={(e) => setContactForm({ ...contactForm, firstName: e.target.value })}
                        className="h-7 px-2 rounded-lg border border-border bg-bg text-[10px] text-text outline-none focus:border-primary"
                      />
                      <input
                        type="text"
                        placeholder="Last Name"
                        value={contactForm.lastName}
                        onChange={(e) => setContactForm({ ...contactForm, lastName: e.target.value })}
                        className="h-7 px-2 rounded-lg border border-border bg-bg text-[10px] text-text outline-none focus:border-primary"
                      />
                    </div>
                    <input
                      type="email"
                      required
                      placeholder="Your email*"
                      value={contactForm.email}
                      onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
                      className="h-7 w-full px-2 rounded-lg border border-border bg-bg text-[10px] text-text outline-none focus:border-primary"
                    />
                    <textarea
                      required
                      rows={2}
                      placeholder="Message*"
                      value={contactForm.message}
                      onChange={(e) => setContactForm({ ...contactForm, message: e.target.value })}
                      className="w-full p-2 rounded-lg border border-border bg-bg text-[10px] text-text outline-none focus:border-primary resize-none leading-relaxed"
                    />
                    <button
                      type="submit"
                      className="w-full h-7 rounded-lg bg-primary hover:bg-primary-hover text-white font-semibold text-[10.5px] cursor-pointer transition-colors flex items-center justify-center gap-1"
                    >
                      <Send className="w-3 h-3" />
                      <span>Submit</span>
                    </button>
                  </form>
                )}
              </div>
            </div>
          </div>

          {/* SECTION 3: REFUND POLICY */}
          <div id="legal-refund" className="space-y-2 pt-1">
            <h3 className="font-bold text-[11px] text-text border-b border-border/70 pb-1 flex items-center gap-1.5">
              <RefreshCw className="w-3.5 h-3.5 text-primary" />
              <span>Refund Policy</span>
            </h3>

            <div className="border border-border/80 rounded-xl p-2.5 bg-surface space-y-1.5 leading-relaxed">
              <span className="font-bold text-[10.5px] text-text block">SECTION 20: REFUND</span>
              <p className="text-text-muted">
                "The services we provide don’t have any refund policy and no refund would be given to anyone."
              </p>
              <p className="text-text-dim text-[9.5px] pt-1 border-t border-border/40">
                Operational Note: Refundable vehicle custody deposits (where applicable under written driver agreements) are settled upon formal de-allocation and return of vehicle custody, following deduction of verified rental and toll liabilities.
              </p>
            </div>
          </div>

          {/* SECTION 4: TERMS OF SERVICE */}
          <div id="legal-terms" className="space-y-2 pt-1">
            <h3 className="font-bold text-[11px] text-text border-b border-border/70 pb-1 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-primary" />
              <span>Terms of Service</span>
            </h3>

            <div className="border border-border/80 rounded-xl p-2.5 bg-surface space-y-3 text-text-muted leading-relaxed">
              <div className="space-y-1">
                <strong className="text-text block text-[10.5px]">OVERVIEW</strong>
                <p>
                  This website is operated by SAMVREEDDHI MOBILITY PRIVATE LIMITED. Throughout the site, the terms “we”, “us” and “our” refer to SAMVREEDDHI MOBILITY PRIVATE LIMITED. SAMVREEDDHI MOBILITY PRIVATE LIMITED offers this website, including all information, tools and services available from this site to you, the user, conditioned upon your acceptance of all terms, conditions, policies and notices stated here.
                </p>
                <p>
                  By visiting our site and/ or purchasing something from us, you engage in our “Service” and agree to be bound by the following terms and conditions (“Terms of Service”, “Terms”), including those additional terms and conditions and policies referenced herein and/or available by hyperlink.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 1 – ONLINE STORE TERMS</strong>
                <p>
                  By agreeing to these Terms of Service, you represent that you are at least the age of majority in your state or province of residence. You may not use our products for any illegal or unauthorized purpose nor may you, in the use of the Service, violate any laws in your jurisdiction (including but not limited to copyright laws).
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 2 – GENERAL CONDITIONS</strong>
                <p>
                  We reserve the right to refuse service to anyone for any reason at any time. You understand that your content (not including credit card information), may be transferred unencrypted. Credit card information is always encrypted during transfer over networks.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 3 – ACCURACY, COMPLETENESS AND TIMELINESS OF INFORMATION</strong>
                <p>
                  We are not responsible if information made available on this site is not accurate, complete or current. The material on this site is provided for general information only and should not be relied upon as the sole basis for making decisions.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 4 – MODIFICATIONS TO THE SERVICE AND PRICES</strong>
                <p>
                  Prices for our products are subject to change without notice. We reserve the right at any time to modify or discontinue the Service without notice at any time.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 5 – PRODUCTS OR SERVICES</strong>
                <p>
                  Certain products or services may be available exclusively online through the website. We reserve the right, but are not obligated, to limit the sales of our products or Services to any person, geographic region or jurisdiction.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 6 – ACCURACY OF BILLING AND ACCOUNT INFORMATION</strong>
                <p>
                  We reserve the right to refuse any order you place with us. You agree to provide current, complete and accurate purchase and account information for all purchases made at our store.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 7 – OPTIONAL TOOLS</strong>
                <p>
                  We may provide you with access to third-party tools over which we neither monitor nor have any control nor input. You acknowledge and agree that we provide access to such tools ”as is” and “as available” without any warranties.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 8 – THIRD-PARTY LINKS</strong>
                <p>
                  Certain content, products and services available via our Service may include materials from third-parties. Third-party links on this site may direct you to third-party websites that are not affiliated with us.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 9 – USER COMMENTS, FEEDBACK AND OTHER SUBMISSIONS</strong>
                <p>
                  If you send creative ideas, suggestions, proposals, or other materials, you agree that we may, at any time, without restriction, edit, copy, publish, distribute, translate and otherwise use in any medium any comments that you forward to us.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 10 – PERSONAL INFORMATION</strong>
                <p>
                  Your submission of personal information through the store is governed by our Privacy Policy.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 11 – ERRORS, INACCURACIES AND OMISSIONS</strong>
                <p>
                  Occasionally there may be information on our site or in the Service that contains typographical errors, inaccuracies or omissions. We reserve the right to correct any errors and update information.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 12 – PROHIBITED USES</strong>
                <p>
                  You are prohibited from using the site or its content for any unlawful purpose, to solicit others to perform unlawful acts, to violate any regulations, to infringe upon intellectual property rights, or to upload malicious code.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 13 – DISCLAIMER OF WARRANTIES; LIMITATION OF LIABILITY</strong>
                <p>
                  We do not guarantee, represent or warrant that your use of our service will be uninterrupted, timely, secure or error-free. In no case shall SAMVREEDDHI MOBILITY PRIVATE LIMITED, our directors, officers, employees, or affiliates be liable for any injury, loss, claim, or direct or indirect damages.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 14 – INDEMNIFICATION</strong>
                <p>
                  You agree to indemnify, defend and hold SAMVREEDDHI MOBILITY PRIVATE LIMITED harmless from any claim or demand made by any third-party due to or arising out of your breach of these Terms of Service.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 15 – SEVERABILITY</strong>
                <p>
                  In the event that any provision of these Terms of Service is determined to be unlawful, void or unenforceable, such provision shall nonetheless be enforceable to the fullest extent permitted by applicable law.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 16 – TERMINATION</strong>
                <p>
                  The obligations and liabilities of the parties incurred prior to the termination date shall survive the termination of this agreement for all purposes.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 17 – ENTIRE AGREEMENT</strong>
                <p>
                  These Terms of Service and any policies or operating rules posted by us on this site constitute the entire agreement and understanding between you and us.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 18 – GOVERNING LAW</strong>
                <p>
                  These Terms of Service and any separate agreements whereby we provide you Services shall be governed by and construed in accordance with the laws of India and jurisdiction of Bangalore, Karnataka.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 19 – CHANGES TO TERMS OF SERVICE</strong>
                <p>
                  You can review the most current version of the Terms of Service at any time on this page. We reserve the right to update, change or replace any part of these Terms by posting updates to our website.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 20 – REFUND</strong>
                <p>
                  The services we provide don’t have any refund policy and no refund would be given to anyone.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">SECTION 21 – CONTACT INFORMATION</strong>
                <p>
                  Questions about the Terms of Service should be sent to us at{' '}
                  <a href="mailto:admin@letzryd.com" className="text-primary font-semibold hover:underline">
                    admin@letzryd.com
                  </a>{' '}
                  or via telephone at{' '}
                  <a href="tel:+919035239090" className="text-text font-semibold hover:text-primary">
                    +91 9035239090
                  </a>.
                </p>
              </div>
            </div>
          </div>

          {/* SECTION 5: PRIVACY POLICY */}
          <div id="legal-privacy" className="space-y-2 pt-1">
            <h3 className="font-bold text-[11px] text-text border-b border-border/70 pb-1 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-primary" />
              <span>Privacy Policy</span>
            </h3>

            <div className="border border-border/80 rounded-xl p-2.5 bg-surface space-y-3 text-text-muted leading-relaxed">
              <div className="flex items-center justify-between pb-1 border-b border-border/40">
                <span className="font-bold text-text text-[10.5px]">Statutory Privacy Notice</span>
                <span className="text-[9px] text-text-dim">Last Updated: 05/02/2026</span>
              </div>

              <p className="text-[9.5px] italic text-text-dim">
                THIS DOCUMENT IS AN ELECTRONIC RECORD IN TERMS OF INFORMATION TECHNOLOGY ACT, 2000 AND RULES THERE UNDER AS APPLICABLE AND THE AMENDED PROVISIONS PERTAINING TO ELECTRONIC RECORDS IN VARIOUS STATUTES. THIS ELECTRONIC RECORD IS GENERATED BY A COMPUTER SYSTEM AND DOES NOT REQUIRE ANY PHYSICAL OR DIGITAL SIGNATURES.
              </p>

              <p className="text-[9.5px] italic text-text-dim">
                THIS DOCUMENT IS PUBLISHED IN ACCORDANCE WITH THE PROVISIONS OF RULE 3 (1) OF THE INFORMATION TECHNOLOGY (INTERMEDIARIES GUIDELINES) RULES, 2011 THAT REQUIRE PUBLISHING THE RULES AND REGULATIONS, TERMS OF SERVICES, PRIVACY POLICY AND USER AGREEMENT FOR ACCESS OR TERMS OF USAGE OF WWW.LETZRYD.COM (HEREINAFTER REFERRED TO AS THE “SITE”).
              </p>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">Privacy Notice & Disclosures</strong>
                <p>
                  Though we make every effort to preserve user privacy, we may need to disclose personal information when required by law wherein we have a good-faith belief that such action is necessary to comply with an appropriate law enforcement investigation, judicial proceeding, court order or legal process served on our Site. We may also disclose personal information to third parties for delivering services to users.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">General Description & Information Collected</strong>
                <p>
                  The Site may collect a user’s name, postal address, telephone number, mobile number, e-mail address, Permanent Account Number (PAN), Aadhaar card, and driving licence. Data will be retained for a reasonable period as required under Applicable Law. Explicit consent from users will be obtained before collecting sensitive personal data.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">Vehicle Use Data & Location Tracking</strong>
                <p>
                  Vehicles contain hardware that gathers and transmits information about vehicle use as a security measure against accident or theft. To prevent theft and locate you in case of emergency or lockout, we track the vehicle location. Location information is confined to Samvreeddhi Mobility Private Limited services and never impermissibly made public. Location data may be shared with insurance companies or law enforcement during investigations.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">Driver & Vehicle Information</strong>
                <p>
                  As a customer or partner of Samvreeddhi Mobility Private Limited, you authorize us to access your driver’s record and vehicle history report from applicable authorities and registries. You have the right to request discontinuance of use of your personal information by closing your account.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">Non-Personal & Aggregate Information</strong>
                <p>
                  We collect non-personal data that does not permit direct association with an individual, including IP addresses, URLs, and browser types to understand usage patterns and administer the platform.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">Security Practices</strong>
                <p>
                  Information collected is protected by appropriate technical and organizational security measures to prevent unauthorized access or accidental loss, conforming to Applicable Laws.
                </p>
              </div>

              <div className="space-y-1">
                <strong className="text-text block text-[10px]">Opt-in Clause & Communications</strong>
                <p>
                  You will be required to enter a valid phone number. By registering your phone number, you consent to be contacted via phone calls and/or SMS/WhatsApp notifications regarding account transactions and updates.
                </p>
              </div>

              <div className="p-2 rounded-lg bg-bg border border-border/70 space-y-1">
                <strong className="text-text block text-[10px]">Grievance Officer</strong>
                <p className="text-[9.5px]">
                  For questions or complaints regarding this Privacy Policy, contact:
                </p>
                <div className="text-[9.5px] font-semibold text-text">
                  Name: Tarun Jain • Email: <a href="mailto:admin@letzryd.com" className="text-primary hover:underline">admin@letzryd.com</a>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-2.5 bg-bg border-t border-border flex items-center justify-between text-[10px] text-text-muted shrink-0">
          <span className="truncate pr-2 font-medium">SAMVREEDDHI MOBILITY PRIVATE LIMITED</span>
          <button
            onClick={onClose}
            className="px-3 py-1 rounded-lg bg-primary hover:bg-primary-hover text-white text-[11px] font-semibold cursor-pointer transition-colors shrink-0"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

