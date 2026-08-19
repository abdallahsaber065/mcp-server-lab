import React from 'react';
import { Calendar, Clock, MapPin, Check, Video, Building2, User, Mail } from 'lucide-react';
import { useAppStore } from '../../stores/useAppStore';

export interface ShowcaseTour {
  booking_id: number;
  property_id?: number;
  property_name?: string;
  unit_number?: string;
  contact_name: string;
  contact_email: string;
  tour_type: string;
  requested_date: string;
  time_slot: string;
  status: string;
}

interface ChatToursShowcaseProps {
  tours: ShowcaseTour[];
  title?: string;
}

export const ChatToursShowcase: React.FC<ChatToursShowcaseProps> = ({
  tours = [],
  title = 'Scheduled Tour Appointments'
}) => {
  const { navigateToChatWithPrompt } = useAppStore();

  if (!tours || tours.length === 0) return null;

  return (
    <div className="p-3.5 sm:p-4 rounded-2xl bg-slate-950/90 border border-amber-500/30 space-y-3 my-2 shadow-xl">
      <div className="flex items-center space-x-2">
        <div className="p-1.5 rounded-lg bg-amber-500/20 text-amber-400">
          <Calendar className="w-4 h-4" />
        </div>
        <div>
          <h4 className="text-xs sm:text-sm font-bold text-white leading-tight">{title}</h4>
          <span className="text-[10px] text-slate-400 font-medium">
            {tours.length} viewing {tours.length === 1 ? 'appointment' : 'appointments'}
          </span>
        </div>
      </div>

      <div className="space-y-2 pt-1">
        {tours.slice(0, 4).map((tour) => (
          <div
            key={tour.booking_id}
            className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5"
          >
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold text-white">{tour.contact_name}</span>
                <span
                  className={`px-2 py-0.2 rounded text-[9px] font-extrabold uppercase ${
                    tour.status === 'confirmed'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : tour.status === 'cancelled'
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                      : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  }`}
                >
                  {tour.status}
                </span>
                <span className="text-[10px] text-indigo-300 capitalize">
                  ({tour.tour_type?.replace('_', ' ')})
                </span>
              </div>
              <div className="text-[11px] text-slate-400 flex flex-wrap items-center gap-3">
                <span className="flex items-center gap-1">
                  <Building2 className="w-3 h-3 text-slate-500" />
                  {tour.property_name || `Property #${tour.property_id}`}
                  {tour.unit_number ? ` (Suite ${tour.unit_number})` : ''}
                </span>
                <span>📅 {tour.requested_date} at {tour.time_slot}</span>
              </div>
            </div>

            <div className="flex items-center space-x-2 shrink-0">
              <button
                onClick={() =>
                  navigateToChatWithPrompt(
                    `Please update tour booking #${tour.booking_id} for ${tour.contact_name} to 'confirmed' and issue the confirmation memo.`
                  )
                }
                className="py-1 px-2.5 rounded-lg text-[10px] font-bold bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 flex items-center space-x-1 transition-all"
              >
                <Check className="w-3 h-3" />
                <span>Confirm</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
