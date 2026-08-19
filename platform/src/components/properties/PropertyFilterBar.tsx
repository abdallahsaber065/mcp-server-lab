import React from 'react';
import { Search, DollarSign, Bed, SlidersHorizontal, ArrowUpDown } from 'lucide-react';

interface PropertyFilterBarProps {
  searchTerm: string;
  onSearchChange: (val: string) => void;
  selectedBeds: string;
  onBedsChange: (val: string) => void;
  maxRent: number;
  onMaxRentChange: (val: number) => void;
  selectedAmenity: string;
  onAmenityChange: (val: string) => void;
  sortBy: string;
  onSortChange: (val: string) => void;
}

export const PropertyFilterBar: React.FC<PropertyFilterBarProps> = ({
  searchTerm,
  onSearchChange,
  selectedBeds,
  onBedsChange,
  maxRent,
  onMaxRentChange,
  selectedAmenity,
  onAmenityChange,
  sortBy,
  onSortChange
}) => {
  const amenitiesList = ['All Amenities', 'Nile View', 'Pool', 'Concierge', 'Parking', 'Security', 'Seafront'];

  return (
    <div className="glass-card p-4 sm:p-5 rounded-2xl border-slate-800 space-y-4 shadow-lg">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Search Input */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by property, district, or address..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700/80 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          />
        </div>

        {/* Bedrooms Filter */}
        <div className="flex items-center space-x-2">
          <Bed className="w-4 h-4 text-cyan-400 shrink-0" />
          <select
            value={selectedBeds}
            onChange={(e) => onBedsChange(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Bedroom Sizes</option>
            <option value="1">1 Bedroom</option>
            <option value="2">2 Bedrooms</option>
            <option value="3">3 Bedrooms</option>
            <option value="4">4+ Bedrooms / Penthouses</option>
          </select>
        </div>

        {/* Sort Order */}
        <div className="flex items-center space-x-2">
          <ArrowUpDown className="w-4 h-4 text-indigo-400 shrink-0" />
          <select
            value={sortBy}
            onChange={(e) => onSortChange(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="featured">Featured First</option>
            <option value="price_asc">Price: Low to High</option>
            <option value="price_desc">Price: High to Low</option>
            <option value="newest">Newest Holdings</option>
          </select>
        </div>

        {/* Price Slider */}
        <div className="space-y-1">
          <div className="flex justify-between text-[11px] text-slate-400">
            <span>Max Budget</span>
            <span className="text-emerald-400 font-mono font-bold">{maxRent.toLocaleString()} EGP</span>
          </div>
          <input
            type="range"
            min="20000"
            max="100000"
            step="5000"
            value={maxRent}
            onChange={(e) => onMaxRentChange(Number(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
          />
        </div>
      </div>

      {/* Amenity Filter Chips */}
      <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800/80">
        <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1 mr-1">
          <SlidersHorizontal className="w-3 h-3 text-slate-400" />
          <span>Filter by Amenity:</span>
        </span>
        {amenitiesList.map((amenity) => (
          <button
            key={amenity}
            onClick={() => onAmenityChange(amenity === 'All Amenities' ? 'all' : amenity)}
            className={`px-3 py-1 rounded-lg text-[11px] font-medium transition-all ${
              (amenity === 'All Amenities' && selectedAmenity === 'all') ||
              selectedAmenity.toLowerCase() === amenity.toLowerCase()
                ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/50'
                : 'bg-slate-900 text-slate-400 hover:text-slate-300 border border-slate-800'
            }`}
          >
            {amenity}
          </button>
        ))}
      </div>
    </div>
  );
};
