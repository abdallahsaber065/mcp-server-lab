/**
 * Enterprise Properties & Available Units Directory (platform/src/pages/public/PropertyCatalogPage.tsx)
 * Features local image carousels, rich metadata, interactive filters, detail drawers, and admin listing tools.
 */

import React, { useEffect, useState, useMemo } from 'react';
import { PropertyHeroBanner } from '../../components/properties/PropertyHeroBanner';
import { PropertyFilterBar } from '../../components/properties/PropertyFilterBar';
import { PropertyCard } from '../../components/properties/PropertyCard';
import { PropertyDetailModal } from '../../components/properties/PropertyDetailModal';
import { ScheduleTourModal } from '../../components/properties/ScheduleTourModal';
import { AdminListingModal } from '../../components/properties/AdminListingModal';
import { apiClient } from '../../services/api';

export const PropertyCatalogPage: React.FC = () => {
  const [properties, setProperties] = useState<any[]>([]);
  const [units, setUnits] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // URL Query Sync for City Filter
  const getInitialCity = (): string => {
    const params = new URLSearchParams(window.location.search);
    return params.get('city') || 'all';
  };

  const [selectedCity, setSelectedCityState] = useState<string>(getInitialCity);

  const setSelectedCity = (city: string) => {
    setSelectedCityState(city);
    const url = new URL(window.location.href);
    if (city === 'all') {
      url.searchParams.delete('city');
    } else {
      url.searchParams.set('city', city);
    }
    window.history.replaceState(null, '', url.toString());
  };

  // Filter States
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedBeds, setSelectedBeds] = useState<string>('all');
  const [maxRent, setMaxRent] = useState<number>(100000);
  const [selectedAmenity, setSelectedAmenity] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('featured');

  // Modal States
  const [detailPropertyId, setDetailPropertyId] = useState<number | null>(null);
  const [schedulePropertyId, setSchedulePropertyId] = useState<number | undefined>(undefined);
  const [isScheduleOpen, setIsScheduleOpen] = useState<boolean>(false);
  const [isAdminModalOpen, setIsAdminModalOpen] = useState<boolean>(false);

  const loadCatalogData = async () => {
    setIsLoading(true);
    try {
      const [propsRes, unitsRes] = await Promise.all([
        apiClient<{ properties: any[] }>('/api/properties', { skipAuth: true }),
        apiClient<{ units: any[] }>('/api/properties/units/available', { skipAuth: true })
      ]);
      setProperties(propsRes.properties || []);
      setUnits(unitsRes.units || []);
    } catch (err) {
      console.error('Failed to load properties catalog:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCatalogData();
  }, []);

  // Filter & Sort Logic
  const filteredProperties = useMemo(() => {
    return properties
      .filter((p) => {
        // City match
        const matchesCity =
          selectedCity === 'all' || p.city.toLowerCase() === selectedCity.toLowerCase();

        // Search match
        const term = searchTerm.toLowerCase();
        const matchesSearch =
          !searchTerm ||
          p.name.toLowerCase().includes(term) ||
          p.address.toLowerCase().includes(term) ||
          (p.neighborhood && p.neighborhood.toLowerCase().includes(term));

        // Amenity match
        const matchesAmenity =
          selectedAmenity === 'all' ||
          (p.amenities || []).some((a: string) => a.toLowerCase().includes(selectedAmenity.toLowerCase()));

        // Price match (starting rent <= maxRent)
        const matchesRent = (p.starting_rent || 0) <= maxRent;

        return matchesCity && matchesSearch && matchesAmenity && matchesRent;
      })
      .sort((a, b) => {
        if (sortBy === 'featured') {
          return (b.is_featured ? 1 : 0) - (a.is_featured ? 1 : 0);
        }
        if (sortBy === 'price_asc') {
          return (a.starting_rent || 0) - (b.starting_rent || 0);
        }
        if (sortBy === 'price_desc') {
          return (b.starting_rent || 0) - (a.starting_rent || 0);
        }
        if (sortBy === 'newest') {
          return (b.year_built || 0) - (a.year_built || 0);
        }
        return 0;
      });
  }, [properties, selectedCity, searchTerm, selectedAmenity, maxRent, sortBy]);

  const handleOpenSchedule = (propId?: number) => {
    setSchedulePropertyId(propId);
    setIsScheduleOpen(true);
  };

  return (
    <div className="space-y-8 pb-20">
      {/* 1. Hero Banner with Stats and Quick City Tabs */}
      <PropertyHeroBanner
        totalProperties={properties.length}
        totalUnits={units.length}
        selectedCity={selectedCity}
        onSelectCity={setSelectedCity}
        onOpenAdminModal={() => setIsAdminModalOpen(true)}
      />

      {/* 2. Dynamic Filter Bar */}
      <PropertyFilterBar
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        selectedBeds={selectedBeds}
        onBedsChange={setSelectedBeds}
        maxRent={maxRent}
        onMaxRentChange={setMaxRent}
        selectedAmenity={selectedAmenity}
        onAmenityChange={setSelectedAmenity}
        sortBy={sortBy}
        onSortChange={setSortBy}
      />

      {/* 3. Luxury Property Cards Grid */}
      {isLoading ? (
        <div className="py-24 text-center space-y-3">
          <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400 font-medium">Loading luxury property holdings and real-time availability...</p>
        </div>
      ) : filteredProperties.length === 0 ? (
        <div className="glass-card p-12 text-center rounded-3xl border-slate-800 space-y-3">
          <h3 className="text-base font-bold text-white">No Properties Found Matching Your Criteria</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Try adjusting your budget slider, resetting city filters, or searching for other prime areas like Zamalek or Garden City.
          </p>
          <button
            onClick={() => {
              setSelectedCity('all');
              setSearchTerm('');
              setSelectedAmenity('all');
              setMaxRent(100000);
            }}
            className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            Reset All Filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProperties.map((property) => (
            <PropertyCard
              key={property.property_id}
              property={property}
              onSelectProperty={(id) => setDetailPropertyId(id)}
              onOpenScheduleModal={handleOpenSchedule}
            />
          ))}
        </div>
      )}

      {/* 4. Modals */}
      <PropertyDetailModal
        propertyId={detailPropertyId}
        onClose={() => setDetailPropertyId(null)}
        onOpenScheduleModal={handleOpenSchedule}
      />

      <ScheduleTourModal
        isOpen={isScheduleOpen}
        onClose={() => setIsScheduleOpen(false)}
        propertyId={schedulePropertyId}
        properties={properties}
      />

      <AdminListingModal
        isOpen={isAdminModalOpen}
        onClose={() => setIsAdminModalOpen(false)}
        properties={properties}
        onRefresh={loadCatalogData}
      />
    </div>
  );
};
