import React, { useState } from 'react';
import { motion } from 'motion/react';
import { 
  X, Sparkles, Copy, Send, ReceiptIndianRupee, FileWarning, Award, CheckCircle, 
  Bell, PhoneCall, Building2, ShieldCheck, Car, FileText, RefreshCw, Mail, MapPin, 
  Phone, CheckCircle2, ChevronRight, Info, ExternalLink, BadgeCheck
} from 'lucide-react';
import { Ticket, Notification } from '../types';

interface ReferralModalProps {
  onClose: () => void;
  driverCode: string;
  onCopy: () => void;
  t: (key: string, fallback: string) => string;
}

export const ReferralModal: React.FC<ReferralModalProps> = ({ onClose, driverCode, onCopy, t }) => {
  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm overflow-y-auto">
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject.trim() || !description.trim()) return;
    onSubmit(category, subject, description);
  };

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center p-3 bg-black/60 backdrop-blur-sm overflow-y-auto">
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
  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm overflow-y-auto">
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
    <div className="absolute inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm overflow-y-auto">
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
    <div className="absolute inset-0 z-50 flex items-center justify-center p-3 bg-black/65 backdrop-blur-sm overflow-y-auto">
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
  initialTab?: 'services' | 'company' | 'refunds' | 'terms' | 'contact';
  t?: (key: string, fallback: string) => string;
}

export const CompanyServicesLegalModal: React.FC<CompanyServicesLegalModalProps> = ({
  isOpen = true,
  onClose,
  initialTab = 'services',
  t = (_k, fb) => fb
}) => {
  const [activeTab, setActiveTab] = useState<'services' | 'company' | 'refunds' | 'terms' | 'contact'>(initialTab);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm overflow-y-auto animate-in fade-in duration-200">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 10 }}
        className="bg-surface border border-border rounded-2xl w-full max-w-lg shadow-2xl relative text-left font-sans flex flex-col max-h-[90vh] my-auto overflow-hidden"
      >
        {/* Top Header */}
        <div className="p-4 sm:p-5 bg-gradient-to-r from-[#0A1650] to-[#122474] text-white flex items-start justify-between shrink-0">
          <div className="space-y-0.5 pr-4">
            <h2 className="text-base font-bold tracking-tight leading-snug">
              SAMVREEDDHI MOBILITY PRIVATE LIMITED
            </h2>
            <p className="text-xs text-white/80">
              Operating Brand: LetzRyd
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-xl bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-colors cursor-pointer shrink-0"
            aria-label="Close modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center border-b border-border bg-bg/80 px-3 py-2 gap-1 overflow-x-auto shrink-0 scrollbar-none">
          <button
            onClick={() => setActiveTab('services')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'services'
                ? 'bg-primary text-white shadow-xs'
                : 'text-text-muted hover:text-text hover:bg-surface'
            }`}
          >
            <Car className="w-3.5 h-3.5" />
            Services & Pricing
          </button>
          <button
            onClick={() => setActiveTab('company')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'company'
                ? 'bg-primary text-white shadow-xs'
                : 'text-text-muted hover:text-text hover:bg-surface'
            }`}
          >
            <Building2 className="w-3.5 h-3.5" />
            Company Info
          </button>
          <button
            onClick={() => setActiveTab('refunds')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'refunds'
                ? 'bg-primary text-white shadow-xs'
                : 'text-text-muted hover:text-text hover:bg-surface'
            }`}
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refund Policy
          </button>
          <button
            onClick={() => setActiveTab('terms')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'terms'
                ? 'bg-primary text-white shadow-xs'
                : 'text-text-muted hover:text-text hover:bg-surface'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            Terms
          </button>
          <button
            onClick={() => setActiveTab('contact')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'contact'
                ? 'bg-primary text-white shadow-xs'
                : 'text-text-muted hover:text-text hover:bg-surface'
            }`}
          >
            <Phone className="w-3.5 h-3.5" />
            Contact Us
          </button>
        </div>

        {/* Tab Content Area */}
        <div className="p-4 sm:p-5 overflow-y-auto space-y-4 text-xs text-text leading-relaxed">
          {/* TAB 1: SERVICES & PRICING */}
          {activeTab === 'services' && (
            <div className="space-y-3.5">
              <div className="bg-primary/5 border border-primary/20 rounded-xl p-3.5 space-y-1">
                <span className="font-bold text-primary text-xs uppercase tracking-wider block">
                  Core Business Activity
                </span>
                <p className="text-text-muted">
                  <strong>SAMVREEDDHI MOBILITY PRIVATE LIMITED</strong> offers commercial electric vehicle (EV) leasing, driver partner onboarding, vehicle allocation, and automated revenue settlement operations across major urban hubs in India.
                </p>
              </div>

              <h4 className="font-bold text-text text-sm">Products & Services Offered (All Prices in INR):</h4>

              {/* Service 1 */}
              <div className="border border-border rounded-xl p-3 bg-surface space-y-1.5">
                <div className="flex justify-between items-start gap-2">
                  <div className="font-bold text-text text-xs flex items-center gap-1.5">
                    <Car className="w-4 h-4 text-primary" />
                    1. Commercial Electric Vehicle (EV) Fleet Rental
                  </div>
                  <span className="font-mono font-extrabold text-primary bg-primary/10 px-2 py-0.5 rounded text-[11px] shrink-0">
                    ₹700 – ₹1,000 / day
                  </span>
                </div>
                <p className="text-text-muted text-[11.5px]">
                  Provision of 4-wheeler commercial EVs (Tata Tigor EV, Mahindra e-Verito, etc.) to verified driver partners for ride-hailing services (Uber, Ola, Rapido). Weekly billing cycle: ₹4,900 – ₹7,000 / week. Includes comprehensive EV maintenance, commercial fleet insurance, 24/7 roadside assistance, and battery telematics.
                </p>
              </div>

              {/* Service 2 */}
              <div className="border border-border rounded-xl p-3 bg-surface space-y-1.5">
                <div className="flex justify-between items-start gap-2">
                  <div className="font-bold text-text text-xs flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-green" />
                    2. Driver Partner Security Deposit (Refundable)
                  </div>
                  <span className="font-mono font-extrabold text-green bg-green-light px-2 py-0.5 rounded text-[11px] shrink-0">
                    ₹5,000 – ₹15,000 (Refundable)
                  </span>
                </div>
                <p className="text-text-muted text-[11.5px]">
                  Standing capital security deposit collected at vehicle handover to ensure safe custody of the EV. Drivers may settle in full or via convenient installments (₹1,000, ₹2,000, or custom). <strong>100% Refundable</strong> upon return of vehicle at contract completion.
                </p>
              </div>

              {/* Service 3 */}
              <div className="border border-border rounded-xl p-3 bg-surface space-y-1.5">
                <div className="flex justify-between items-start gap-2">
                  <div className="font-bold text-text text-xs flex items-center gap-1.5">
                    <RefreshCw className="w-4 h-4 text-amber-600" />
                    3. Weekly Hisaab Accounting & Settlement Platform
                  </div>
                  <span className="font-mono font-extrabold text-amber-700 bg-amber-50 px-2 py-0.5 rounded text-[11px] shrink-0">
                    Weekly Net Settlement
                  </span>
                </div>
                <p className="text-text-muted text-[11.5px]">
                  Automated weekly reconciliation platform netting driver gross earnings from ride-hailing platforms against vehicle rent, Fastag tolls, and charging costs. Excess net earnings are credited to drivers, and pending vehicle rentals are collected via Cashfree UPI/NetBanking gateway.
                </p>
              </div>
            </div>
          )}

          {/* TAB 2: COMPANY INFO */}
          {activeTab === 'company' && (
            <div className="space-y-3">
              <div className="border border-border rounded-xl p-3.5 bg-surface space-y-2">
                <h4 className="font-bold text-sm text-text">Corporate Legal Entity Details</h4>
                <div className="space-y-1.5 text-[11.5px]">
                  <div className="flex justify-between py-1 border-b border-border/50">
                    <span className="text-text-muted">Legal Entity Name:</span>
                    <strong className="text-text">SAMVREEDDHI MOBILITY PRIVATE LIMITED</strong>
                  </div>
                  <div className="flex justify-between py-1 border-b border-border/50">
                    <span className="text-text-muted">Operating Brand:</span>
                    <strong className="text-text">LetzRyd</strong>
                  </div>
                  <div className="flex justify-between py-1 border-b border-border/50">
                    <span className="text-text-muted">Business Type:</span>
                    <span className="text-text font-medium">Electric Vehicle Fleet & Urban Mobility Platform</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-border/50">
                    <span className="text-text-muted">Country of Incorporation:</span>
                    <span className="text-text font-medium">India</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-border/50">
                    <span className="text-text-muted">Operational Hubs:</span>
                    <span className="text-text font-medium">Hyderabad, Bengaluru, Mumbai, Delhi-NCR</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-text-muted">Payment Partner:</span>
                    <span className="text-text font-medium">Cashfree Payments India Pvt. Ltd.</span>
                  </div>
                </div>
              </div>

              <div className="bg-bg border border-border rounded-xl p-3 text-[11.5px] text-text-muted space-y-1">
                <strong className="text-text block">Compliance Statement:</strong>
                <p>
                  SAMVREEDDHI MOBILITY PRIVATE LIMITED operates in full compliance with applicable Indian commercial vehicle leasing laws, Motor Vehicles Act regulations, and RBI guidelines for digital collection gateways.
                </p>
              </div>
            </div>
          )}

          {/* TAB 3: REFUND & CANCELLATION POLICY */}
          {activeTab === 'refunds' && (
            <div className="space-y-3">
              <div className="border border-border rounded-xl p-3.5 bg-surface space-y-2">
                <h4 className="font-bold text-sm text-text flex items-center gap-1.5">
                  <RefreshCw className="w-4 h-4 text-green" />
                  Refund & Cancellation Policy
                </h4>
                <div className="space-y-2 text-[11.5px] text-text-muted">
                  <p>
                    <strong className="text-text">1. Security Deposit Refund:</strong> All security deposits collected by <strong>SAMVREEDDHI MOBILITY PRIVATE LIMITED</strong> from driver partners are 100% refundable upon completion or termination of the vehicle lease agreement.
                  </p>
                  <p>
                    <strong className="text-text">2. Refund Timeline:</strong> Following vehicle return at our authorized operational hub and standard damage/challan inspection, the eligible refund amount will be credited directly to the driver partner’s registered bank account / UPI ID within <strong>5 to 7 business days</strong>.
                  </p>
                  <p>
                    <strong className="text-text">3. Advance Payment Adjustments:</strong> Any excess or advance payment made during weekly hisaab settlements will be adjusted towards the driver’s subsequent weekly rental dues or refunded upon written request.
                  </p>
                  <p>
                    <strong className="text-text">4. Cancellation Policy:</strong> Driver partners wishing to discontinue or return their vehicle may do so by submitting a 7-day prior notice to their assigned Fleet Manager. The vehicle must be returned in good running condition to the designated hub.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: TERMS & CONDITIONS */}
          {activeTab === 'terms' && (
            <div className="space-y-3">
              <div className="border border-border rounded-xl p-3.5 bg-surface space-y-2">
                <h4 className="font-bold text-sm text-text flex items-center gap-1.5">
                  <FileText className="w-4 h-4 text-primary" />
                  Terms & Conditions
                </h4>
                <div className="space-y-2 text-[11.5px] text-text-muted">
                  <p>
                    <strong className="text-text">1. Driver Eligibility:</strong> The driver partner must possess a valid commercial driver's license (TR/Badge where applicable), government-issued ID (Aadhaar/PAN), and pass background verification.
                  </p>
                  <p>
                    <strong className="text-text">2. Vehicle Custody:</strong> The vehicle remains the sole legal property of SAMVREEDDHI MOBILITY PRIVATE LIMITED or its authorized asset partners. The driver partner is granted operational custody for lawful commercial ride-hailing purposes only.
                  </p>
                  <p>
                    <strong className="text-text">3. Settlement Cycle:</strong> Weekly hisaabs run Monday 00:00 to Sunday 23:59. Settlements are published every Monday. Net dues must be cleared through the LetzRyd portal via Cashfree Payment Gateway by Wednesday midnight.
                  </p>
                  <p>
                    <strong className="text-text">4. Maintenance & Safety:</strong> Regular servicing and manufacturer warranty maintenance are handled by LetzRyd. Drivers must report any roadside accident, warning lights, or breakdown immediately via the portal’s SOS desk.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: CONTACT US */}
          {activeTab === 'contact' && (
            <div className="space-y-3">
              <div className="border border-border rounded-xl p-3.5 bg-surface space-y-3">
                <h4 className="font-bold text-sm text-text">Customer Care & Corporate Contact</h4>
                <div className="space-y-2.5 text-[11.5px]">
                  <div className="flex items-start gap-2.5">
                    <Building2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-text block">Corporate Entity:</span>
                      <span className="text-text-muted">SAMVREEDDHI MOBILITY PRIVATE LIMITED</span>
                    </div>
                  </div>
                  <div className="flex items-start gap-2.5">
                    <Mail className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-text block">Support & Grievance Email:</span>
                      <a href="mailto:support@letzryd.com" className="text-primary font-bold hover:underline">
                        support@letzryd.com
                      </a>
                    </div>
                  </div>
                  <div className="flex items-start gap-2.5">
                    <Phone className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-text block">Helpline & WhatsApp Support:</span>
                      <a href="tel:+919691938866" className="text-text font-bold hover:text-primary">
                        +91 96919 38866 / +91 74837 31338
                      </a>
                      <span className="text-[10px] text-text-muted block">Available Monday – Saturday, 9:00 AM – 7:00 PM IST</span>
                    </div>
                  </div>
                  <div className="flex items-start gap-2.5">
                    <MapPin className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-text block">Operational Headquarters:</span>
                      <span className="text-text-muted">
                        Hyderabad, Telangana - 500081, India
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-3 bg-bg border-t border-border flex items-center justify-between text-[11px] text-text-muted shrink-0">
          <span>© 2026 SAMVREEDDHI MOBILITY PRIVATE LIMITED</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-primary hover:bg-primary-hover text-white font-bold cursor-pointer transition-colors shadow-xs"
          >
            Close
          </button>
        </div>
      </motion.div>
    </div>
  );
};
