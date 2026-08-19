import React, { useState } from 'react';
import {
  MapPin,
  Calendar,
  Eye,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Settings,
  Compass,
  MessageSquareQuote
} from 'lucide-react';
import { useAuthStore } from '../../stores/useAuthStore';
import { useAppStore } from '../../stores/useAppStore';
import { VirtualTourModal } from './VirtualTourModal';
import {
  generateTourPrompt,
  generateManagerUnitsPrompt,
  generateManagerToursPrompt
} from '../../utils/propertyPrompts';

interface PropertyCardProps {
  property: any;
  onSelectProperty: (propertyId: number) => void;
  onOpenScheduleModal?: (propertyId: number) => void;
}

export const PropertyCard: React.FC<PropertyCardProps> = ({
  property,
  onSelectProperty,
}) => {
  const { role } = useAuthStore();
  const { navigateToChatWithPrompt } = useAppStore();
  const isManagerOrAdmin = role === 'property_manager' || role === 'executive_admin';

  const images = property?.images?.length ? property.images : [property?.image_url || '/images/properties/nile_tower_ext.jpg'];
  const [currentImgIndex, setCurrentImgIndex] = useState(0);
  const [is3DModalOpen, setIs3DModalOpen] = useState(false);

  const handleNext = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCurrentImgIndex((prev) => (prev + 1) % images.length);
  };

  const handlePrev = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCurrentImgIndex((prev) => (prev - 1 + images.length) % images.length);
  };

  return (
    <>
      <div className="glass-card-hover rounded-3xl overflow-hidden border border-slate-800 flex flex-col justify-between group shadow-xl transition-all duration-300">
        {/* 1. Image Carousel Container */}
        <div
          className="relative h-64 overflow-hidden bg-slate-950 cursor-pointer"
          onClick={() => onSelectProperty(property.property_id)}
        >
          <img
            src={images[currentImgIndex]}
            alt={property.name}
            onError={(e) => {
              e.currentTarget.src = '/images/properties/nile_tower_ext.jpg';
            }}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/20 to-transparent opacity-85 pointer-events-none" />

          {/* Top Non-Overlapping Badges Bar */}
          <div className="absolute top-3 inset-x-3 flex items-start justify-between gap-2 pointer-events-none z-10">
            {/* Left Badge Group */}
            <div className="flex flex-wrap items-center gap-1.5 max-w-[65%]">
              <span className="px-2 py-0.5 rounded-md text-[10px] font-extrabold bg-indigo-600/90 text-white backdrop-blur-md shadow-md uppercase tracking-wider">
                Verified Luxury
              </span>
              {property.is_featured && (
                <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-500/90 text-slate-950 backdrop-blur-md shadow-md flex items-center gap-1">
                  <Sparkles className="w-3 h-3 fill-slate-950" />
                  <span>Trophy</span>
                </span>
              )}
            </div>

            {/* Right Available Units Badge */}
            <div className="shrink-0">
              <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold bg-slate-950/85 text-emerald-300 border border-emerald-500/40 backdrop-blur-md shadow-md">
                {property.available_units || property.total_units} Units
              </span>
            </div>
          </div>

          {/* 3D Virtual Tour Badge Pill */}
          {property.virtual_tour_url && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIs3DModalOpen(true);
              }}
              className="absolute bottom-3 right-3 px-3 py-1.5 rounded-xl bg-cyan-600/90 hover:bg-cyan-500 text-white text-xs font-bold backdrop-blur-md shadow-lg flex items-center space-x-1.5 transition-all z-20 hover:scale-105"
            >
              <Compass className="w-3.5 h-3.5 animate-spin-slow" />
              <span>3D Tour</span>
            </button>
          )}

          {/* Carousel Next / Prev Controls */}
          {images.length > 1 && (
            <div className="absolute inset-y-0 inset-x-2 flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity z-10">
              <button
                onClick={handlePrev}
                className="p-1.5 rounded-full bg-slate-950/70 hover:bg-slate-900 text-white border border-slate-700/80 backdrop-blur-md shadow-md"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={handleNext}
                className="p-1.5 rounded-full bg-slate-950/70 hover:bg-slate-900 text-white border border-slate-700/80 backdrop-blur-md shadow-md"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Dot Indicators */}
          {images.length > 1 && (
            <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex space-x-1.5 z-10 pointer-events-none">
              {images.map((_: any, idx: number) => (
                <div
                  key={idx}
                  className={`w-1.5 h-1.5 rounded-full transition-all ${
                    currentImgIndex === idx ? 'bg-white w-4' : 'bg-white/40'
                  }`}
                />
              ))}
            </div>
          )}
        </div>

        {/* 2. Property Information */}
        <div className="p-5 sm:p-6 space-y-4 flex-1 flex flex-col justify-between">
          <div className="space-y-2.5">
            <div className="flex items-center space-x-1.5 text-xs text-indigo-400 font-semibold">
              <MapPin className="w-3.5 h-3.5" />
              <span>{property.neighborhood || property.city}, Egypt</span>
            </div>

            <h3
              onClick={() => onSelectProperty(property.property_id)}
              className="text-lg font-extrabold text-white group-hover:text-cyan-300 transition-colors cursor-pointer leading-tight"
            >
              {property.name}
            </h3>

            <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
              {property.description}
            </p>

            {/* Amenities Chips */}
            <div className="flex flex-wrap gap-1.5 pt-1">
              {(property.amenities || []).slice(0, 3).map((amenity: string, idx: number) => (
                <span
                  key={idx}
                  className="px-2.5 py-0.5 rounded-md text-[10px] font-medium bg-slate-900 border border-slate-800 text-slate-300"
                >
                  {amenity}
                </span>
              ))}
              {(property.amenities || []).length > 3 && (
                <span className="px-2 py-0.5 rounded-md text-[10px] bg-slate-900 text-slate-500 font-medium">
                  +{property.amenities.length - 3}
                </span>
              )}
            </div>
          </div>

          {/* 3. Pricing and Assistant Prompts / Actions Footer */}
          <div className="pt-4 border-t border-slate-800/80 space-y-3">
            <div className="flex items-end justify-between">
              <div>
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Starting Monthly Lease
                </span>
                <div className="text-lg font-extrabold text-emerald-400 font-mono">
                  {property.starting_rent?.toLocaleString() || '24,000'}{' '}
                  <span className="text-xs font-normal text-slate-400 font-sans">EGP / mo</span>
                </div>
              </div>

              <span className="text-[11px] text-slate-400">
                Built <strong className="text-slate-200">{property.year_built || 2024}</strong>
              </span>
            </div>

            {/* AI Agent-Driven Action Prompts */}
            {isManagerOrAdmin ? (
              /* Admin / Property Manager Assistant Actions */
              <div className="grid grid-cols-2 gap-2 pt-1">
                <button
                  onClick={() => navigateToChatWithPrompt(generateManagerUnitsPrompt(property))}
                  className="py-2.5 px-3 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700/80 flex items-center justify-center space-x-1.5 transition-all group"
                  title="Ask Assistant to audit and control unit inventory"
                >
                  <Settings className="w-3.5 h-3.5 text-indigo-400 group-hover:rotate-45 transition-transform" />
                  <span>Audit Units</span>
                </button>

                <button
                  onClick={() => navigateToChatWithPrompt(generateManagerToursPrompt(property))}
                  className="py-2.5 px-3 rounded-xl text-xs font-bold bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 border border-amber-500/30 flex items-center justify-center space-x-1.5 transition-all"
                  title="Ask Assistant to list and manage tour appointments"
                >
                  <Calendar className="w-3.5 h-3.5 text-amber-400" />
                  <span>Tour Schedule</span>
                </button>
              </div>
            ) : (
              /* Tenant / Public Prospect Assistant Actions */
              <div className="grid grid-cols-2 gap-2 pt-1">
                <button
                  onClick={() => navigateToChatWithPrompt(generateTourPrompt(property))}
                  className="py-2.5 px-3 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700/80 flex items-center justify-center space-x-1.5 transition-all"
                  title="Ask AI Assistant to schedule a viewing appointment"
                >
                  <Calendar className="w-3.5 h-3.5 text-amber-400" />
                  <span>Book Tour</span>
                </button>

                <button
                  onClick={() => onSelectProperty(property.property_id)}
                  className="py-2.5 px-3 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20 flex items-center justify-center space-x-1.5 transition-all"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Inspect Units</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 3D Virtual Tour Modal */}
      <VirtualTourModal
        isOpen={is3DModalOpen}
        onClose={() => setIs3DModalOpen(false)}
        tourUrl={property.virtual_tour_url}
        propertyTitle={property.name}
      />
    </>
  );
};
