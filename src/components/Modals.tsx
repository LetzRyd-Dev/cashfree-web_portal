import React, { useState } from 'react';
import { motion } from 'motion/react';
import { X, Sparkles, Copy, Send, ReceiptIndianRupee, FileWarning, Award, CheckCircle, Bell, PhoneCall } from 'lucide-react';
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
            <label className="font-sans text-xs font-semibold text-text-muted">Ticket Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="h-10 w-full rounded-lg border border-border bg-surface px-3 font-sans text-xs text-text outline-none focus:border-green"
            >
              {categories.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div className="flex flex-col gap-1">
            <label className="font-sans text-xs font-semibold text-text-muted">Issue Subject</label>
            <input
              type="text"
              required
              placeholder="Summary of the issue..."
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="h-10 w-full rounded-lg border border-border bg-surface px-3 font-sans text-xs text-text placeholder:text-text-dim outline-none focus:border-green"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="font-sans text-xs font-semibold text-text-muted">Detailed Description</label>
            <textarea
              required
              rows={3}
              placeholder="Describe what happened, relevant week dates, or vehicle issues..."
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
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-primary hover:bg-primary-hover font-sans text-xs font-semibold text-white cursor-pointer shadow-sm transition-colors flex items-center gap-1.5"
            >
              <Send className="w-3.5 h-3.5" />
              Submit Ticket
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
          <span className="font-sans text-xs font-semibold text-text-muted">• {ticket.category}</span>
        </div>

        <h3 className="font-sans text-lg font-bold text-text">{ticket.subject}</h3>

        <div className="p-3.5 rounded-lg bg-bg border border-border">
          <p className="font-sans text-xs font-semibold text-text-muted mb-1">Issue Details</p>
          <p className="font-sans text-xs text-text leading-relaxed">{ticket.description}</p>
        </div>

        {ticket.response && (
          <div className="p-3.5 rounded-lg bg-green-light border border-green/30">
            <p className="font-sans text-xs font-bold text-green flex items-center gap-1.5 mb-1">
              <CheckCircle className="w-4 h-4" /> LetzRyd Support Resolution
            </p>
            <p className="font-sans text-xs text-green leading-relaxed">{ticket.response}</p>
          </div>
        )}

        <div className="flex justify-end pt-1">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-primary hover:bg-primary-hover text-white font-sans text-xs font-semibold cursor-pointer shadow-sm transition-colors"
          >
            Close
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
            <Bell className="w-5 h-5 text-primary" /> Notifications & Updates
          </h3>
          {notifications.some(n => !n.read) && (
            <button onClick={onMarkAllRead} className="font-sans text-xs font-semibold text-primary hover:underline cursor-pointer">Mark All Read</button>
          )}
        </div>

        <div className="space-y-2.5 max-h-[50vh] overflow-y-auto pr-1">
          {notifications.length === 0 ? (
            <div className="py-8 text-center text-text-muted">No new notifications</div>
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
              LetzRyd Central Control Hub (24x7)
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
                Central Control Hub notified at <strong>{sosTime || 'Just now'}</strong>. Dispatchers are matching vehicle coordinates.
              </p>
            </div>

            <div className="flex flex-col gap-2">
              <a
                href={`tel:${hotline}`}
                className="w-full py-3 rounded-xl bg-red-600 hover:bg-red-700 text-white font-sans text-xs font-extrabold flex items-center justify-center gap-2 cursor-pointer shadow-md transition-all active:scale-98"
              >
                <PhoneCall className="w-4 h-4" />
                <span>Call Helpline: {hotline}</span>
              </a>
              <button
                type="button"
                onClick={onCancelSos}
                className="w-full py-2.5 rounded-xl border border-border bg-bg text-text-muted hover:text-text font-sans text-xs font-bold cursor-pointer transition-colors"
              >
                Cancel SOS Alert
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
                Direct Hotline: {hotline}
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
                  <span>Report submitted! Dispatcher is reviewing your details.</span>
                </div>
              ) : (
                <form onSubmit={handleIncidentSubmit} className="space-y-2.5 text-xs font-sans">
                  <div>
                    <label className="text-text-muted font-medium block mb-1">Issue Category</label>
                    <select
                      value={incidentType}
                      onChange={(e) => setIncidentType(e.target.value)}
                      className="w-full h-8.5 rounded-xl border border-border bg-bg px-2.5 font-bold text-text text-xs outline-none focus:border-red-500 cursor-pointer"
                    >
                      <option value="Roadside Breakdown">Roadside Breakdown</option>
                      <option value="Minor Collision / Accident">Minor Collision / Accident</option>
                      <option value="Flat Tyre / Suspension">Flat Tyre / Suspension</option>
                      <option value="EV Battery / Range Issue">EV Battery / Range Issue</option>
                      <option value="Medical Emergency">Medical Emergency</option>
                      <option value="Other Safety Incident">Other Safety Incident</option>
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
                    <span className="text-text-muted font-medium">Is Vehicle Drivable?</span>
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => setIsDrivable(true)}
                        className={`px-2.5 py-1 rounded-lg text-xs font-bold cursor-pointer transition-all ${
                          isDrivable ? 'bg-green text-white shadow-2xs' : 'bg-bg text-text-muted border border-border'
                        }`}
                      >
                        Yes
                      </button>
                      <button
                        type="button"
                        onClick={() => setIsDrivable(false)}
                        className={`px-2.5 py-1 rounded-lg text-xs font-bold cursor-pointer transition-all ${
                          !isDrivable ? 'bg-red-600 text-white shadow-2xs' : 'bg-bg text-text-muted border border-border'
                        }`}
                      >
                        No
                      </button>
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="w-full h-9 mt-1 rounded-xl bg-primary hover:bg-primary-hover text-white font-sans text-xs font-bold cursor-pointer transition-all shadow-xs"
                  >
                    Submit Incident Report
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

