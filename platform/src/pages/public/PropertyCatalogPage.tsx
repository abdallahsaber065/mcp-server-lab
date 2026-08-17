/**
 * Searchable Property & Unit Catalog (platform/src/pages/public/PropertyCatalogPage.tsx)
 */

import React, { useEffect, useState } from 'react';
import { Building, MapPin, DollarSign, Filter, Search, Tag, CheckCircle2 } from 'lucide-react';
import { Property, Unit } from '../../types';
import { apiClient } from '../../services/api';

export const PropertyCatalogPage: React.FC = () => {
  const [properties, setProperties] = useState<Property[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [selectedCity, setSelectedCity] = useState<string>('all');
  const [maxRent, setMaxRent] = useState<number>(50000);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const propsRes = await apiClient<{ properties: Property[] }>('/api/properties', { skipAuth: true });
        setProperties(propsRes.properties || []);

        const unitsRes = await apiClient<{ units: Unit[] }>('/api/properties/units/available', { skipAuth: true });
        setUnits(unitsRes.units || []);
      } catch (err) {
        console.error('Failed to load catalog data:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  const filteredProperties = properties.filter((p) => {
    const matchesCity = selectedCity === 'all' || p.city.toLowerCase() === selectedCity.toLowerCase();
    const matchesSearch =
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.address.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCity && matchesSearch;
  });

  const filteredUnits = units.filter((u) => {
    const matchesCity = selectedCity === 'all' || u.city.toLowerCase() === selectedCity.toLowerCase();
    const matchesRent = u.monthly_rent <= maxRent;
    const matchesSearch =
      u.property_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.unit_number.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCity && matchesRent && matchesSearch;
  });

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Properties & Available Units Directory</h1>
        <p className="text-xs text-slate-400 mt-1">
          Explore Cornerstone Realty residential and commercial holdings across Greater Cairo and Alexandria.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="glass-card p-4 flex flex-wrap gap-4 items-center justify-between">
        <div className="flex-1 min-w-[200px] relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by property name or address..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950/70 border border-slate-700/80 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          />
        </div>

        {/* City Filter */}
        <div className="flex items-center space-x-2">
          <MapPin className="w-4 h-4 text-indigo-400" />
          <select
            value={selectedCity}
            onChange={(e) => setSelectedCity(e.target.value)}
            className="bg-slate-950/70 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Cities</option>
            <option value="Cairo">Cairo (Zamalek / Downtown)</option>
            <option value="New Cairo">New Cairo (Tagamoa)</option>
            <option value="Giza">Giza (Dokki)</option>
            <option value="Sheikh Zayed">Sheikh Zayed</option>
            <option value="Alexandria">Alexandria</option>
          </select>
        </div>

        {/* Rent Budget Slider */}
        <div className="flex items-center space-x-3">
          <DollarSign className="w-4 h-4 text-emerald-400" />
          <div className="text-xs text-slate-300">
            Max Rent: <span className="font-bold text-emerald-400">{maxRent.toLocaleString()} EGP</span>
          </div>
          <input
            type="range"
            min="10000"
            max="60000"
            step="2500"
            value={maxRent}
            onChange={(e) => setMaxRent(Number(e.target.value))}
            className="w-28 accent-indigo-500"
          />
        </div>
      </div>

      {/* Available Units Grid */}
      <section className="space-y-4">
        <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
          <span>Vacant & Available Units</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            {filteredUnits.length} Available
          </span>
        </h2>

        {filteredUnits.length === 0 ? (
          <div className="p-8 text-center glass-card text-slate-400 text-xs">
            No units match your selected city and rent filter criteria.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
            {filteredUnits.map((unit) => (
              <div key={unit.unit_id} className="glass-card-hover p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-100">{unit.property_name}</span>
                  {unit.is_high_value ? (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      High Value
                    </span>
                  ) : (
                    <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      Standard
                    </span>
                  )}
                </div>

                <div className="text-xs text-slate-400 flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-indigo-400" />
                  <span>{unit.city}</span>
                  <span>•</span>
                  <span>Unit {unit.unit_number}</span>
                  <span>•</span>
                  <span>{unit.bedrooms} BR</span>
                </div>

                <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
                  <div>
                    <div className="text-[10px] text-slate-400 uppercase">Monthly Rent</div>
                    <div className="text-sm font-extrabold text-emerald-400">
                      {unit.monthly_rent.toLocaleString()} EGP
                    </div>
                  </div>
                  <span className="text-[10px] px-2 py-1 rounded bg-emerald-500/10 text-emerald-400 font-semibold border border-emerald-500/20">
                    Ready to Lease
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Properties Summary */}
      <section className="space-y-4 pt-6">
        <h2 className="text-lg font-bold text-slate-200">Portfolio Holdings</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
          {filteredProperties.map((prop) => (
            <div key={prop.property_id} className="glass-card p-5 space-y-2.5">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-100">{prop.name}</h3>
                <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {prop.property_type}
                </span>
              </div>
              <p className="text-xs text-slate-400">{prop.address}, {prop.city}</p>
              <div className="pt-2 flex items-center justify-between text-xs text-slate-300">
                <span>Total Units: <strong>{prop.total_units}</strong></span>
                <span>Occupancy: <strong>{(prop.occupancy_rate * 100).toFixed(0)}%</strong></span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
