import React, { useState } from 'react';
import { Sparkles, Calendar, ArrowRight, CheckCircle2 } from 'lucide-react';
import { apiClient } from '../../services/api';

interface VipInquiryCtaProps {
  onOpenScheduleModal: () => void;
}

export const VipInquiryCta: React.FC<VipInquiryCtaProps> = ({ onOpenScheduleModal }) => {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    try {
      await apiClient('/api/properties/inquire', {
        method: 'POST',
        body: JSON.stringify({
          name: 'VIP Subscriber',
          email,
          tour_type: 'in_person',
          notes: 'Subscribed to VIP Private Off-Market Catalog'
        }),
        skipAuth: true
      });
      setSubmitted(true);
    } catch {
      setSubmitted(true);
    }
  };

  return (
    <section className="relative overflow-hidden rounded-3xl border border-indigo-500/30 p-8 sm:p-14 bg-gradient-to-br from-indigo-950/80 via-slate-950 to-slate-900 shadow-2xl">
      <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 max-w-3xl space-y-6">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          <span>Exclusive Private Portfolio Access</span>
        </div>

        <div className="space-y-3">
          <h2 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
            Ready to Experience Cairo & Alexandria's Finest Addresses?
          </h2>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            Schedule an accompanied private tour or subscribe to our exclusive off-market listings catalog before public release.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 pt-2 items-start sm:items-center">
          <button
            onClick={onOpenScheduleModal}
            className="px-6 py-3.5 rounded-xl text-xs sm:text-sm font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-xl shadow-indigo-600/30 flex items-center space-x-2 transition-all hover:scale-[1.02]"
          >
            <Calendar className="w-4 h-4 text-amber-400" />
            <span>Schedule Private Viewing</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </button>

          {!submitted ? (
            <form onSubmit={handleSubmit} className="flex w-full sm:w-auto items-center">
              <input
                type="email"
                placeholder="Enter your VIP email address..."
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full sm:w-72 bg-slate-950/80 border border-slate-700/80 rounded-l-xl px-4 py-3 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              />
              <button
                type="submit"
                className="px-4 py-3 bg-slate-800 hover:bg-slate-700 border border-l-0 border-slate-700 rounded-r-xl text-xs font-semibold text-slate-200 transition-all shrink-0"
              >
                Join VIP List
              </button>
            </form>
          ) : (
            <div className="flex items-center space-x-2 text-xs font-semibold text-emerald-300 bg-emerald-950/50 px-4 py-3 rounded-xl border border-emerald-500/30">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Thank you. You have been added to the VIP catalog list!</span>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};
