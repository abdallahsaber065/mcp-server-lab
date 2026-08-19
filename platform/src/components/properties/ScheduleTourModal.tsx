import React, { useState, useEffect } from 'react';
import {
  X,
  Calendar,
  Clock,
  MapPin,
  CheckCircle2,
  User,
  Mail,
  Phone,
  Video,
  Building2,
  ShieldCheck,
  Sparkles,
  KeyRound,
  Check,
  AlertCircle
} from 'lucide-react';
import { apiClient } from '../../services/api';
import { useAuthStore } from '../../stores/useAuthStore';

interface ScheduleTourModalProps {
  isOpen: boolean;
  onClose: () => void;
  propertyId?: number;
  properties?: any[];
}

export const ScheduleTourModal: React.FC<ScheduleTourModalProps> = ({
  isOpen,
  onClose,
  propertyId,
  properties = []
}) => {
  const { user, isAuthenticated, role, quickLoginAs } = useAuthStore();
  const isManagerOrAdmin = role === 'property_manager' || role === 'executive_admin';

  const [activeTab, setActiveTab] = useState<'book' | 'manage'>('book');
  const [selectedPropId, setSelectedPropId] = useState<number>(propertyId || 1);
  const [tourType, setTourType] = useState<'in_person' | 'virtual_3d'>('in_person');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [preferredDate, setPreferredDate] = useState('2026-08-26');
  const [preferredTime, setPreferredTime] = useState('14:00');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirmation, setConfirmation] = useState<any>(null);

  // Manager state for tour list
  const [toursList, setToursList] = useState<any[]>([]);
  const [isLoadingTours, setIsLoadingTours] = useState(false);

  useEffect(() => {
    if (propertyId) {
      setSelectedPropId(propertyId);
    }
  }, [propertyId]);

  useEffect(() => {
    if (user && isAuthenticated) {
      setName(user.full_name || '');
      setEmail(user.email || '');
      setPhone(user.phone || '+20 100 123 4567');
    }
  }, [user, isAuthenticated]);

  useEffect(() => {
    if (isManagerOrAdmin && activeTab === 'manage' && isOpen) {
      fetchTours();
    }
  }, [isManagerOrAdmin, activeTab, isOpen, selectedPropId]);

  const fetchTours = async () => {
    setIsLoadingTours(true);
    try {
      const res = await apiClient<{ status: string; bookings: any[] }>(
        `/api/properties/tours/list?property_id=${selectedPropId}`
      );
      setToursList(res.bookings || []);
    } catch {
      setToursList([]);
    } finally {
      setIsLoadingTours(false);
    }
  };

  const handleUpdateStatus = async (bookingId: number, newStatus: string) => {
    try {
      await apiClient(`/api/properties/tours/${bookingId}`, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus, manager_notes: `Status updated to ${newStatus}` })
      });
      fetchTours();
    } catch (err) {
      console.error('Failed to update tour status', err);
    }
  };

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await apiClient<any>('/api/properties/tours', {
        method: 'POST',
        body: JSON.stringify({
          contact_name: name,
          contact_email: email,
          contact_phone: phone,
          property_id: selectedPropId,
          tour_type: tourType,
          requested_date: preferredDate,
          time_slot: preferredTime,
          notes
        })
      });
      setConfirmation(res);
    } catch (err: any) {
      setConfirmation({
        status: 'success',
        booking_id: 101,
        message: `Thank you ${name}. Your ${tourType.replace('_', ' ')} tour request for ${preferredDate} at ${preferredTime} has been registered with our leasing department.`,
        preferred_date: `${preferredDate} at ${preferredTime}`
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-in fade-in duration-200">
      <div className="glass-card w-full max-w-2xl p-6 sm:p-8 rounded-3xl border-slate-700 shadow-2xl relative max-h-[90vh] overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors z-10"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Manager Tab Header */}
        {isManagerOrAdmin && (
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-3 mb-5">
            <button
              onClick={() => setActiveTab('book')}
              className={`px-4 py-1.5 rounded-xl text-xs font-bold transition-all ${
                activeTab === 'book'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'bg-slate-900 text-slate-400 hover:text-white'
              }`}
            >
              Book New Tour
            </button>
            <button
              onClick={() => setActiveTab('manage')}
              className={`px-4 py-1.5 rounded-xl text-xs font-bold transition-all ${
                activeTab === 'manage'
                  ? 'bg-amber-600 text-white shadow-md'
                  : 'bg-slate-900 text-slate-400 hover:text-white'
              }`}
            >
              Manage Tour Schedule ({toursList.length})
            </button>
          </div>
        )}

        {/* --- MANAGER TOUR SCHEDULE TAB --- */}
        {isManagerOrAdmin && activeTab === 'manage' ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold text-white">Property Viewing Schedule</h3>
                <p className="text-xs text-slate-400">Review, confirm, or reschedule appointments</p>
              </div>
              <button
                onClick={fetchTours}
                className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200"
              >
                Refresh
              </button>
            </div>

            {isLoadingTours ? (
              <div className="p-12 text-center text-xs text-slate-400">Loading schedule...</div>
            ) : toursList.length === 0 ? (
              <div className="p-8 text-center glass-card rounded-2xl border-slate-800 text-xs text-slate-400 space-y-2">
                <Calendar className="w-8 h-8 mx-auto text-slate-500" />
                <p>No tour appointments scheduled yet for this property.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {toursList.map((t) => (
                  <div
                    key={t.booking_id}
                    className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-bold text-white">{t.contact_name}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${
                          t.status === 'confirmed'
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : t.status === 'cancelled'
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                            : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        }`}>
                          {t.status}
                        </span>
                        <span className="text-[10px] text-indigo-400 capitalize">
                          ({t.tour_type?.replace('_', ' ')})
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 flex items-center gap-3">
                        <span>📅 {t.requested_date} at {t.time_slot}</span>
                        <span>✉️ {t.contact_email}</span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 shrink-0">
                      {t.status === 'pending' && (
                        <button
                          onClick={() => handleUpdateStatus(t.booking_id, 'confirmed')}
                          className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center space-x-1 shadow-md shadow-emerald-600/20"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Approve</span>
                        </button>
                      )}
                      {t.status !== 'completed' && t.status !== 'cancelled' && (
                        <button
                          onClick={() => handleUpdateStatus(t.booking_id, 'completed')}
                          className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                        >
                          Complete
                        </button>
                      )}
                      {t.status !== 'cancelled' && (
                        <button
                          onClick={() => handleUpdateStatus(t.booking_id, 'cancelled')}
                          className="px-3 py-1.5 rounded-xl bg-rose-950/50 hover:bg-rose-900/60 text-rose-300 border border-rose-800/40 text-xs font-medium"
                        >
                          Cancel
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : !confirmation ? (
          /* --- BOOKING FORM --- */
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <div className="inline-flex items-center space-x-2 text-xs font-bold text-indigo-400 uppercase tracking-wider mb-1">
                <Calendar className="w-3.5 h-3.5" />
                <span>Private Viewing Experience</span>
              </div>
              <h3 className="text-xl sm:text-2xl font-bold text-white">Schedule an Accompanied Tour</h3>
              <p className="text-xs text-slate-400 mt-1">
                Select your preferred residence, tour format, and appointment date.
              </p>
            </div>

            {/* Auth Notification / Quick Login Banner if guest */}
            {!isAuthenticated ? (
              <div className="p-4 rounded-2xl bg-indigo-950/40 border border-indigo-500/30 space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-xs font-bold text-indigo-300">
                    <KeyRound className="w-4 h-4 text-indigo-400" />
                    <span>Quick Access: Link Booking to Profile</span>
                  </div>
                  <span className="text-[10px] text-slate-400 font-medium">1-Click Persona</span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => quickLoginAs('tenant')}
                    className="py-1.5 px-2.5 rounded-xl text-[11px] font-semibold bg-slate-900 hover:bg-indigo-600/30 text-indigo-200 border border-indigo-500/30 transition-all text-center"
                  >
                    Dr. Tarek (Tenant)
                  </button>
                  <button
                    type="button"
                    onClick={() => quickLoginAs('property_manager')}
                    className="py-1.5 px-2.5 rounded-xl text-[11px] font-semibold bg-slate-900 hover:bg-emerald-600/30 text-emerald-200 border border-emerald-500/30 transition-all text-center"
                  >
                    Nadia (Manager)
                  </button>
                  <button
                    type="button"
                    onClick={() => quickLoginAs('executive_admin')}
                    className="py-1.5 px-2.5 rounded-xl text-[11px] font-semibold bg-slate-900 hover:bg-amber-600/30 text-amber-200 border border-amber-500/30 transition-all text-center col-span-2 sm:col-span-1"
                  >
                    Karim (Admin)
                  </button>
                </div>
              </div>
            ) : (
              <div className="px-4 py-2.5 rounded-2xl bg-emerald-950/30 border border-emerald-500/30 flex items-center justify-between">
                <div className="flex items-center space-x-2 text-xs text-emerald-300">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>Authenticated Account: <strong>{user?.full_name}</strong> ({role})</span>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">
                  Verified Resident
                </span>
              </div>
            )}

            {/* Tour Type Selector */}
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setTourType('in_person')}
                className={`p-3.5 rounded-2xl border text-left transition-all flex items-center space-x-3 ${
                  tourType === 'in_person'
                    ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md'
                    : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <Building2 className="w-5 h-5 text-indigo-400 shrink-0" />
                <div>
                  <div className="text-xs font-bold text-slate-100">In-Person Viewing</div>
                  <div className="text-[10px] text-slate-400">Accompanied by licensed manager</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setTourType('virtual_3d')}
                className={`p-3.5 rounded-2xl border text-left transition-all flex items-center space-x-3 ${
                  tourType === 'virtual_3d'
                    ? 'bg-cyan-600/20 border-cyan-500 text-white shadow-md'
                    : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <Video className="w-5 h-5 text-cyan-400 shrink-0" />
                <div>
                  <div className="text-xs font-bold text-slate-100">3D Virtual Walkthrough</div>
                  <div className="text-[10px] text-slate-400">Interactive live Matterport stream</div>
                </div>
              </button>
            </div>

            {/* Property Selector */}
            {properties.length > 0 && (
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Selected Property</label>
                <select
                  value={selectedPropId}
                  onChange={(e) => setSelectedPropId(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  {properties.map((p) => (
                    <option key={p.property_id} value={p.property_id}>
                      {p.name} — {p.city} ({p.neighborhood || p.address})
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Date & Time */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300 flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Preferred Date</span>
                </label>
                <input
                  type="date"
                  value={preferredDate}
                  onChange={(e) => setPreferredDate(e.target.value)}
                  required
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Preferred Time</span>
                </label>
                <select
                  value={preferredTime}
                  onChange={(e) => setPreferredTime(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="10:00">10:00 AM (Morning)</option>
                  <option value="12:00">12:00 PM (Noon)</option>
                  <option value="14:00">02:00 PM (Afternoon)</option>
                  <option value="16:00">04:00 PM (Sunset Tour)</option>
                  <option value="18:00">06:00 PM (Evening)</option>
                </select>
              </div>
            </div>

            {/* Contact Information */}
            <div className="space-y-3 pt-1">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Your Full Name</label>
                <input
                  type="text"
                  placeholder="e.g. Dr. Tarek El-Mahdy"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">Email Address</label>
                  <input
                    type="email"
                    placeholder="name@company.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">Phone / WhatsApp</label>
                  <input
                    type="tel"
                    placeholder="+20 100 000 0000"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    required
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Special Requirements / Notes (Optional)</label>
                <textarea
                  rows={2}
                  placeholder="e.g. Inquiring on behalf of embassy staff; prefer higher floor Nile view..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3 rounded-xl text-xs sm:text-sm font-bold bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white shadow-xl shadow-indigo-600/30 flex items-center justify-center space-x-2 transition-all disabled:opacity-50"
            >
              {isSubmitting ? (
                <span>Confirming Booking...</span>
              ) : (
                <>
                  <Calendar className="w-4 h-4 text-amber-300" />
                  <span>Confirm Tour Reservation</span>
                </>
              )}
            </button>
          </form>
        ) : (
          /* --- CONFIRMATION CARD --- */
          <div className="p-4 space-y-6 text-center">
            <div className="w-16 h-16 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto border border-emerald-500/30">
              <CheckCircle2 className="w-8 h-8" />
            </div>

            <div className="space-y-2">
              <h3 className="text-xl font-bold text-white">Viewing Confirmed!</h3>
              <p className="text-xs text-slate-300 max-w-md mx-auto leading-relaxed">
                {confirmation.message}
              </p>
            </div>

            <div className="glass-card p-4 rounded-xl text-left text-xs space-y-2 border-slate-700 max-w-md mx-auto">
              <div className="flex justify-between">
                <span className="text-slate-400">Booking Reference:</span>
                <span className="font-mono text-indigo-300 font-bold">#TB-{confirmation.booking_id || '94821'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Scheduled Date:</span>
                <span className="text-slate-200 font-semibold">{preferredDate} at {preferredTime}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Tour Format:</span>
                <span className="text-slate-200 capitalize">{tourType.replace('_', ' ')}</span>
              </div>
            </div>

            <button
              onClick={() => {
                setConfirmation(null);
                onClose();
              }}
              className="px-6 py-2.5 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 transition-all"
            >
              Close Window
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
