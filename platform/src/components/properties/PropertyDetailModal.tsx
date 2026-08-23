import React, { useEffect, useState } from 'react';
import {
  X,
  MapPin,
  CheckCircle2,
  Calendar,
  Bed,
  Bath,
  Maximize2,
  Phone,
  Video,
  ChevronLeft,
  ChevronRight,
  Send,
  Compass,
  MessageSquareQuote,
  Sparkles
} from 'lucide-react';
import { apiClient } from '../../services/api';
import { useAppStore } from '../../stores/useAppStore';
import { useAuthStore } from '../../stores/useAuthStore';
import { VirtualTourModal } from './VirtualTourModal';
import { generateApplyPrompt, generateTourPrompt } from '../../utils/propertyPrompts';

interface PropertyDetailModalProps {
  propertyId: number | null;
  onClose: () => void;
  onOpenScheduleModal?: (propertyId: number) => void;
}

export const PropertyDetailModal: React.FC<PropertyDetailModalProps> = ({
  propertyId,
  onClose
}) => {
  const { navigateToChatWithPrompt } = useAppStore();
  const { role } = useAuthStore();
  const isManagerOrAdmin = role === 'property_manager' || role === 'executive_admin';

  const [property, setProperty] = useState<any>(null);
  const [activeImageIndex, setActiveImageIndex] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // 3D Tour Modal state
  const [is3DOpen, setIs3DOpen] = useState(false);
  const [current3DUrl, setCurrent3DUrl] = useState<string>('');
  const [current3DTitle, setCurrent3DTitle] = useState<string>('');

  useEffect(() => {
    if (!propertyId) return;
    async function loadDetail() {
      setIsLoading(true);
      try {
        const res = await apiClient<{ property: any }>(`/api/properties/${propertyId}`, { skipAuth: true });
        setProperty(res.property);
        setActiveImageIndex(0);
      } catch (err) {
        console.error('Failed to load property details:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadDetail();
  }, [propertyId]);

  if (!propertyId) return null;

  const images = property?.images?.length ? property.images : [property?.image_url || '/images/properties/nile_tower_ext.jpg'];

  const handleNextImage = () => {
    setActiveImageIndex((prev) => (prev + 1) % images.length);
  };

  const handlePrevImage = () => {
    setActiveImageIndex((prev) => (prev - 1 + images.length) % images.length);
  };

  const handleApplyViaAssistant = (unit: any) => {
    onClose();
    navigateToChatWithPrompt(generateApplyPrompt(property, unit));
  };

  const handleScheduleTourViaAssistant = () => {
    onClose();
    navigateToChatWithPrompt(generateTourPrompt(property));
  };

  const open3DTour = (url: string, title: string) => {
    setCurrent3DUrl(url);
    setCurrent3DTitle(title);
    setIs3DOpen(true);
  };

  return (
    <>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-950/85 backdrop-blur-lg animate-in fade-in duration-200">
        <div className="glass-card w-full max-w-5xl rounded-3xl border-slate-700 shadow-2xl relative max-h-[92vh] flex flex-col overflow-hidden">
          {/* Modal Header */}
          <div className="p-4 sm:p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
            <div className="space-y-0.5">
              <div className="flex items-center space-x-2">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase">
                  {property?.property_type?.replace('_', ' ')}
                </span>
                <span className="text-xs text-slate-400 font-medium flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-indigo-400" />
                  {property?.neighborhood || property?.city}
                </span>
              </div>
              <h2 className="text-xl sm:text-2xl font-extrabold text-white leading-tight">
                {property?.name || 'Property Details'}
              </h2>
            </div>

            <button
              onClick={onClose}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Modal Body */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
            {isLoading ? (
              <div className="py-20 text-center space-y-3">
                <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
                <p className="text-xs text-slate-400">Loading comprehensive property portfolio...</p>
              </div>
            ) : (
              <>
                {/* 1. Main Media Carousel & Quick Meta */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                  <div className="lg:col-span-7 space-y-3">
                    <div className="relative h-72 sm:h-84 rounded-2xl overflow-hidden bg-slate-950 border border-slate-800 group">
                      <img
                        src={images[activeImageIndex]}
                        alt={property?.name}
                        onError={(e) => {
                          e.currentTarget.src = '/images/properties/nile_tower_ext.jpg';
                        }}
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-slate-950/60 via-transparent to-transparent" />

                      {/* 3D Tour Overlay Action Button */}
                      {property?.virtual_tour_url && (
                        <button
                          onClick={() => open3DTour(property.virtual_tour_url, `${property.name} - Master 3D Tour`)}
                          className="absolute top-4 right-4 px-3.5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold shadow-xl shadow-cyan-600/30 flex items-center space-x-1.5 backdrop-blur-md transition-all hover:scale-105"
                        >
                          <Compass className="w-4 h-4" />
                          <span>Explore Matterport 3D Tour</span>
                        </button>
                      )}

                      {images.length > 1 && (
                        <div className="absolute inset-y-0 inset-x-2 flex items-center justify-between">
                          <button
                            onClick={handlePrevImage}
                            className="p-2 rounded-full bg-slate-950/70 hover:bg-slate-900 text-white border border-slate-700/80 backdrop-blur-md"
                          >
                            <ChevronLeft className="w-4 h-4" />
                          </button>
                          <button
                            onClick={handleNextImage}
                            className="p-2 rounded-full bg-slate-950/70 hover:bg-slate-900 text-white border border-slate-700/80 backdrop-blur-md"
                          >
                            <ChevronRight className="w-4 h-4" />
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Thumbnail Strip */}
                    {images.length > 1 && (
                      <div className="flex space-x-2 overflow-x-auto pb-1">
                        {images.map((img: string, idx: number) => (
                          <button
                            key={idx}
                            onClick={() => setActiveImageIndex(idx)}
                            className={`w-16 h-12 rounded-xl overflow-hidden border-2 shrink-0 transition-all ${
                              activeImageIndex === idx ? 'border-indigo-500 scale-105' : 'border-slate-800 opacity-60'
                            }`}
                          >
                            <img
                              src={img}
                              alt="thumb"
                              onError={(e) => {
                                e.currentTarget.src = '/images/properties/nile_tower_ext.jpg';
                              }}
                              className="w-full h-full object-cover"
                            />
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Summary Card */}
                  <div className="lg:col-span-5 glass-card p-5 rounded-2xl border-slate-800 space-y-4">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider">
                        Address & Location
                      </span>
                      <p className="text-sm font-semibold text-white mt-0.5">{property?.address}</p>
                      <p className="text-xs text-slate-400">{property?.city}, Egypt</p>
                    </div>

                    <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-800">
                      <div>
                        <span className="text-[10px] text-slate-400">Total Units</span>
                        <div className="text-sm font-bold text-white">{property?.total_units} Suites</div>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400">Built Year</span>
                        <div className="text-sm font-bold text-white">{property?.year_built || 2024}</div>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-slate-800 space-y-2">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold">Lease Inquiry Hotline</span>
                      <div className="flex items-center space-x-2 text-xs text-emerald-400 font-semibold">
                        <Phone className="w-3.5 h-3.5" />
                        <span>+20 (2) 2795-8800 (24/7 VIP Concierge)</span>
                      </div>
                    </div>

                    <div className="pt-2">
                      <button
                        onClick={handleScheduleTourViaAssistant}
                        className="w-full py-3 rounded-xl text-xs font-bold bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white shadow-xl shadow-indigo-600/30 flex items-center justify-center space-x-2 transition-all"
                        title="Open Assistant to schedule viewing"
                      >
                        <Calendar className="w-4 h-4 text-amber-300" />
                        <span>Schedule Tour with Assistant</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* 2. Description and Amenities */}
                <div className="space-y-4 pt-2">
                  <div>
                    <h3 className="text-base font-bold text-white">Architectural Overview</h3>
                    <p className="text-xs text-slate-300 mt-1 leading-relaxed">{property?.description}</p>
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-white mb-2">Curated Amenities & Services</h3>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                      {(property?.amenities || []).map((amenity: string, i: number) => (
                        <div key={i} className="flex items-center space-x-2 text-xs text-slate-300">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                          <span>{amenity}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* 3. Available Units Table */}
                <div className="space-y-4 pt-4 border-t border-slate-800">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-base font-bold text-white">Available Suites & Floor Plans</h3>
                      <p className="text-xs text-slate-400">Select a unit to launch tenancy application workflow with the AI Assistant.</p>
                    </div>
                    <span className="px-3 py-1 rounded-lg text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      {property?.available_units || property?.units?.length} Units Ready
                    </span>
                  </div>

                  <div className="space-y-3">
                    {(property?.units || []).map((unit: any) => (
                      <div
                        key={unit.unit_id}
                        className="p-4 rounded-2xl bg-slate-900/80 hover:bg-slate-900 border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-all"
                      >
                        <div className="flex items-center space-x-4">
                          <img
                            src={unit.image_url || property?.image_url || '/images/properties/nile_tower_penthouse.jpg'}
                            alt={unit.title}
                            onError={(e) => {
                              e.currentTarget.src = '/images/properties/nile_tower_penthouse.jpg';
                            }}
                            className="w-16 h-16 rounded-xl object-cover border border-slate-700 shrink-0"
                          />
                          <div className="space-y-1">
                            <div className="flex items-center space-x-2">
                              <span className="font-mono text-xs font-bold text-indigo-300">{unit.unit_number}</span>
                              {unit.is_high_value && (
                                <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                                  High-Value
                                </span>
                              )}
                              <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${
                                unit.status === 'available' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-800 text-slate-400'
                              }`}>
                                {unit.status}
                              </span>
                            </div>
                            <h4 className="text-xs sm:text-sm font-bold text-white">{unit.title}</h4>
                            <div className="flex items-center space-x-3 text-[11px] text-slate-400">
                              <span className="flex items-center gap-1"><Bed className="w-3 h-3 text-indigo-400" /> {unit.bedrooms} Bed</span>
                              <span>•</span>
                              <span className="flex items-center gap-1"><Bath className="w-3 h-3 text-cyan-400" /> {unit.bathrooms} Bath</span>
                              <span>•</span>
                              <span className="flex items-center gap-1"><Maximize2 className="w-3 h-3 text-amber-400" /> {unit.square_feet} m²</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center justify-between sm:justify-end w-full sm:w-auto gap-4 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-800">
                          <div className="text-left sm:text-right">
                            <div className="text-[10px] text-slate-400 uppercase font-medium">Monthly Lease</div>
                            <div className="text-sm sm:text-base font-extrabold text-emerald-400 font-mono">
                              {unit.monthly_rent?.toLocaleString()} <span className="text-[10px] font-normal text-slate-400">EGP</span>
                            </div>
                          </div>

                          <div className="flex items-center space-x-2">
                            {unit.virtual_tour_url && (
                              <button
                                onClick={() => open3DTour(unit.virtual_tour_url, `${property.name} - Suite ${unit.unit_number}`)}
                                className="p-2 rounded-xl bg-cyan-950/60 hover:bg-cyan-900/80 text-cyan-300 border border-cyan-700/50 flex items-center space-x-1 text-xs font-semibold"
                                title="Open 3D Virtual Tour"
                              >
                                <Compass className="w-4 h-4 text-cyan-400 animate-spin-slow" />
                                <span className="hidden sm:inline">3D View</span>
                              </button>
                            )}
                            <button
                              onClick={() => handleApplyViaAssistant(unit)}
                              disabled={unit.status !== 'available'}
                              className="px-3.5 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white transition-all shadow-md flex items-center space-x-1.5"
                            >
                              <MessageSquareQuote className="w-3.5 h-3.5" />
                              <span>Apply in Chat</span>
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* 3D Virtual Tour Modal */}
      <VirtualTourModal
        isOpen={is3DOpen}
        onClose={() => setIs3DOpen(false)}
        tourUrl={current3DUrl}
        propertyTitle={current3DTitle}
      />
    </>
  );
};
