import React, { useState } from 'react';
import { Search, MapPin, DollarSign, Building2, Sparkles, Calendar, ArrowRight, ShieldCheck } from 'lucide-react';
import { useAppStore } from '../../stores/useAppStore';

interface MarketingHeroProps {
  onOpenScheduleModal: (propertyId?: number) => void;
}

export const MarketingHero: React.FC<MarketingHeroProps> = ({ onOpenScheduleModal }) => {
  const { setCurrentPage } = useAppStore();
  const [selectedCity, setSelectedCity] = useState<string>('all');
  const [selectedBeds, setSelectedBeds] = useState<string>('all');
  const [maxBudget, setMaxBudget] = useState<string>('50000');

  const handleSearch = () => {
    const params = new URLSearchParams();
    if (selectedCity !== 'all') params.set('city', selectedCity);
    if (selectedBeds !== 'all') params.set('beds', selectedBeds);
    if (maxBudget) params.set('maxRent', maxBudget);
    window.history.replaceState(null, '', `/properties?${params.toString()}`);
    setCurrentPage('properties');
  };

  return (
    <section className="relative overflow-hidden rounded-3xl border border-slate-800 shadow-2xl bg-slate-950">
      {/* Background Hero Image with Dark Gradient Overlay */}
      <div className="absolute inset-0 z-0">
        <img
          src="/images/properties/nile_tower_ext.jpg"
          alt="Cornerstone Luxury Residences"
          className="w-full h-full object-cover object-center opacity-30 scale-105 transition-transform duration-1000"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/80 to-slate-950/40" />
      </div>

      <div className="relative z-10 p-8 sm:p-14 max-w-5xl space-y-8">
        {/* Badge */}
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 backdrop-blur-md">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          <span>Prime Residences & Commercial Real Estate • Cairo & Alexandria</span>
        </div>

        {/* Hero Title & Subtitle */}
        <div className="space-y-4 max-w-3xl">
          <h1 className="text-3xl sm:text-6xl font-extrabold text-white tracking-tight leading-tight">
            Discover Exceptional Living in{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-cyan-300 to-emerald-400">
              Egypt's Most Prestigious
            </span>{' '}
            Addresses
          </h1>
          <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-2xl">
            From panoramic Nile sky penthouses in Garden City and historic Zamalek heritage suites to private Mediterranean seafront residences in Alexandria.
          </p>
        </div>

        {/* Real Estate Discovery Search Bar */}
        <div className="glass-card p-4 sm:p-5 rounded-2xl border-slate-700/80 backdrop-blur-xl shadow-2xl space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* City Selector */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-indigo-400" />
                <span>Location</span>
              </label>
              <select
                value={selectedCity}
                onChange={(e) => setSelectedCity(e.target.value)}
                className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="all">All Prime Locations</option>
                <option value="Cairo">Cairo (Zamalek & Garden City)</option>
                <option value="New Cairo">New Cairo (Fifth Settlement)</option>
                <option value="Giza">Giza (Pyramids Vista & Dokki)</option>
                <option value="Sheikh Zayed">Sheikh Zayed Compounds</option>
                <option value="Alexandria">Alexandria (Stanley Beachfront)</option>
              </select>
            </div>

            {/* Bedrooms Selector */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
                <Building2 className="w-3.5 h-3.5 text-cyan-400" />
                <span>Property Type & Size</span>
              </label>
              <select
                value={selectedBeds}
                onChange={(e) => setSelectedBeds(e.target.value)}
                className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="all">All Sizes (1 - 4+ Bedrooms)</option>
                <option value="1">1 Bedroom Suites</option>
                <option value="2">2 Bedroom Luxury Residences</option>
                <option value="3">3 Bedroom Panoramic Homes</option>
                <option value="4">4+ Bedroom Penthouses & Villas</option>
              </select>
            </div>

            {/* Monthly Budget */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
                <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
                <span>Max Monthly Budget (EGP)</span>
              </label>
              <select
                value={maxBudget}
                onChange={(e) => setMaxBudget(e.target.value)}
                className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="30000">Up to 30,000 EGP / mo</option>
                <option value="45000">Up to 45,000 EGP / mo</option>
                <option value="60000">Up to 60,000 EGP / mo</option>
                <option value="100000">100,000+ EGP (High-Value)</option>
              </select>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800/80">
            <div className="flex items-center space-x-3 text-[11px] text-slate-400">
              <span className="flex items-center gap-1"><ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Verified Legal Titles</span>
              <span className="hidden sm:inline">•</span>
              <span className="hidden sm:inline">24/7 Digital Concierge</span>
            </div>

            <div className="flex items-center space-x-2 w-full sm:w-auto">
              <button
                onClick={() => onOpenScheduleModal()}
                className="flex-1 sm:flex-none px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center justify-center space-x-1.5 transition-all"
              >
                <Calendar className="w-3.5 h-3.5 text-amber-400" />
                <span>Book Private Tour</span>
              </button>

              <button
                onClick={handleSearch}
                className="flex-1 sm:flex-none px-6 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white shadow-lg shadow-indigo-600/30 flex items-center justify-center space-x-1.5 transition-all"
              >
                <Search className="w-3.5 h-3.5" />
                <span>Search Residences</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
