import React from 'react';
import { Building2, MapPin, Sparkles, PlusCircle } from 'lucide-react';
import { useAuthStore } from '../../stores/useAuthStore';

interface PropertyHeroBannerProps {
  totalProperties: number;
  totalUnits: number;
  selectedCity: string;
  onSelectCity: (city: string) => void;
  onOpenAdminModal: () => void;
}

export const PropertyHeroBanner: React.FC<PropertyHeroBannerProps> = ({
  totalProperties,
  totalUnits,
  selectedCity,
  onSelectCity,
  onOpenAdminModal
}) => {
  const { user } = useAuthStore();
  const canManage = user?.role === 'executive_admin' || user?.role === 'property_manager';

  const cities = [
    { key: 'all', label: 'All Cities' },
    { key: 'Cairo', label: 'Cairo' },
    { key: 'New Cairo', label: 'New Cairo' },
    { key: 'Giza', label: 'Giza' },
    { key: 'Sheikh Zayed', label: 'Sheikh Zayed' },
    { key: 'Alexandria', label: 'Alexandria' }
  ];

  return (
    <div className="glass-card p-6 sm:p-8 rounded-3xl border-slate-800 space-y-6 shadow-xl relative overflow-hidden bg-slate-950/80">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="inline-flex items-center space-x-2 text-xs font-bold text-indigo-400 uppercase tracking-wider">
            <Building2 className="w-3.5 h-3.5" />
            <span>Cornerstone Real Estate Portfolio</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
            Properties & Available Suites Directory
          </h1>
          <p className="text-xs sm:text-sm text-slate-400">
            Browse verified luxury residential holdings, sky penthouses, and commercial headquarters across Egypt.
          </p>
        </div>

        {/* Admin / Property Manager Quick Listing CTA */}
        {canManage && (
          <button
            onClick={onOpenAdminModal}
            className="self-start sm:self-auto px-4 py-2.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30 flex items-center space-x-2 transition-all shrink-0"
          >
            <PlusCircle className="w-4 h-4" />
            <span>+ Add New Listing</span>
          </button>
        )}
      </div>

      {/* City Tabs and Stats Banner */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800/80">
        <div className="flex flex-wrap gap-2">
          {cities.map((c) => (
            <button
              key={c.key}
              onClick={() => onSelectCity(c.key)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                selectedCity.toLowerCase() === c.key.toLowerCase()
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>

        <div className="flex items-center space-x-4 text-xs text-slate-400">
          <span>
            Holdings: <strong className="text-slate-200">{totalProperties}</strong>
          </span>
          <span>•</span>
          <span>
            Total Suites: <strong className="text-emerald-400">{totalUnits}</strong>
          </span>
        </div>
      </div>
    </div>
  );
};
