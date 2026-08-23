import React, { useState } from 'react';
import {
  Building2,
  Bed,
  Bath,
  Maximize2,
  Compass,
  MessageSquareQuote,
  Calendar,
  ChevronRight,
  ChevronLeft,
  Eye,
  CheckCircle2
} from 'lucide-react';
import { VirtualTourModal } from '../properties/VirtualTourModal';
import { useAppStore } from '../../stores/useAppStore';
import { generateApplyPrompt, generateTourPrompt } from '../../utils/propertyPrompts';

export interface ShowcaseUnit {
  unit_id?: number;
  unit_number: string;
  title?: string;
  property_id?: number;
  property_name?: string;
  city?: string;
  address?: string;
  neighborhood?: string;
  bedrooms?: number;
  bathrooms?: number;
  square_feet?: number;
  monthly_rent: number;
  status?: string;
  image_url?: string;
  virtual_tour_url?: string;
  is_high_value?: boolean;
}

interface ChatUnitsShowcaseProps {
  units: ShowcaseUnit[];
  initialLimit?: number;
  title?: string;
  onDirectSend?: (prompt: string) => void;
  isStreaming?: boolean;
}

export const ChatUnitsShowcase: React.FC<ChatUnitsShowcaseProps> = ({
  units = [],
  initialLimit = 3,
  title = 'Available Luxury Residences',
  onDirectSend,
  isStreaming = false,
}) => {
  const { navigateToChatWithPrompt, addToast } = useAppStore();
  const [isExpanded, setIsExpanded] = useState(false);
  const [selected3DTour, setSelected3DTour] = useState<{ url: string; title: string } | null>(null);

  const handleAction = (prompt: string) => {
    if (isStreaming) {
      addToast('Please wait for the agent to finish its current response', 'info');
      return;
    }
    if (onDirectSend) {
      onDirectSend(prompt);
    } else {
      navigateToChatWithPrompt(prompt);
    }
  };

  if (!units || units.length === 0) return null;

  const displayUnits = isExpanded ? units : units.slice(0, initialLimit);
  const hasMore = units.length > initialLimit;

  return (
    <>
      <div className="p-3.5 sm:p-4 rounded-2xl bg-slate-950/90 border border-indigo-500/30 space-y-3 my-2 shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-indigo-500/20 text-indigo-400">
              <Building2 className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs sm:text-sm font-bold text-white leading-tight">{title}</h4>
              <span className="text-[10px] text-slate-400 font-medium">
                {units.length} verified available {units.length === 1 ? 'suite' : 'suites'}
              </span>
            </div>
          </div>

          {hasMore && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 transition-all flex items-center gap-1"
            >
              <span>{isExpanded ? 'Show Less' : `+${units.length - initialLimit} More`}</span>
            </button>
          )}
        </div>

        {/* Units Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-1">
          {displayUnits.map((unit, idx) => {
            const propContext = {
              property_id: unit.property_id || 1,
              name: unit.property_name || 'Cornerstone Residence',
              address: unit.address || 'Cairo Corniche',
              city: unit.city || 'Cairo',
              neighborhood: unit.neighborhood
            };

            return (
              <div
                key={idx}
                className="glass-card-hover rounded-xl overflow-hidden border border-slate-800/90 bg-slate-900/90 flex flex-col justify-between group"
              >
                {/* Image & Tour Badge */}
                <div className="relative h-28 overflow-hidden bg-slate-950">
                  <img
                    src={unit.image_url || '/images/properties/nile_tower_penthouse.jpg'}
                    alt={unit.title || unit.unit_number}
                    onError={(e) => {
                      e.currentTarget.src = '/images/properties/nile_tower_penthouse.jpg';
                    }}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent opacity-80" />

                  <div className="absolute top-2 inset-x-2 flex items-start justify-between gap-1 pointer-events-none">
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-slate-950/80 text-indigo-300 border border-indigo-500/30 backdrop-blur-md">
                      {unit.unit_number}
                    </span>
                    {unit.is_high_value && (
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-500/80 text-slate-950">
                        Trophy
                      </span>
                    )}
                  </div>

                  {unit.virtual_tour_url && (
                    <button
                      onClick={() =>
                        setSelected3DTour({
                          url: unit.virtual_tour_url!,
                          title: `${unit.property_name || 'Property'} — Suite ${unit.unit_number}`
                        })
                      }
                      className="absolute bottom-2 right-2 px-2 py-0.5 rounded-lg bg-cyan-600/90 hover:bg-cyan-500 text-white text-[10px] font-bold shadow-md flex items-center space-x-1 backdrop-blur-md transition-all hover:scale-105"
                      title="Open 3D Virtual Tour"
                    >
                      <Compass className="w-3 h-3" />
                      <span>3D View</span>
                    </button>
                  )}
                </div>

                {/* Details */}
                <div className="p-3 space-y-2 flex-1 flex flex-col justify-between">
                  <div>
                    <h5 className="text-xs font-bold text-white truncate">
                      {unit.title || `Suite ${unit.unit_number}`}
                    </h5>
                    <p className="text-[10px] text-slate-400 truncate">
                      {unit.property_name || unit.city || 'Cairo, Egypt'}
                    </p>

                    {/* Specs */}
                    <div className="flex items-center space-x-2 text-[10px] text-slate-300 pt-1">
                      <span className="flex items-center gap-0.5">
                        <Bed className="w-3 h-3 text-indigo-400" /> {unit.bedrooms || 1}
                      </span>
                      <span>•</span>
                      <span className="flex items-center gap-0.5">
                        <Bath className="w-3 h-3 text-cyan-400" /> {unit.bathrooms || 1}
                      </span>
                      <span>•</span>
                      <span className="flex items-center gap-0.5">
                        <Maximize2 className="w-3 h-3 text-amber-400" /> {unit.square_feet || 150}m²
                      </span>
                    </div>
                  </div>

                  {/* Pricing & Assistant Actions */}
                  <div className="pt-2 border-t border-slate-800/80 space-y-1.5">
                    <div className="flex items-baseline justify-between">
                      <span className="text-[9px] text-slate-400 uppercase font-medium">Monthly</span>
                      <span className="text-xs font-extrabold text-emerald-400 font-mono">
                        {unit.monthly_rent?.toLocaleString()} <span className="text-[9px] font-normal text-slate-400">EGP</span>
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-1.5 pt-0.5">
                      <button
                        onClick={() => handleAction(generateTourPrompt(propContext, unit))}
                        disabled={isStreaming}
                        className={`py-1 px-1.5 rounded-lg text-[10px] font-semibold flex items-center justify-center space-x-1 transition-all ${
                          isStreaming
                            ? 'bg-slate-900 text-slate-500 border border-slate-800 cursor-not-allowed'
                            : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
                        }`}
                        title="Book private viewing tour"
                      >
                        <Calendar className="w-3 h-3 text-amber-400" />
                        <span>Tour</span>
                      </button>

                      <button
                        onClick={() => handleAction(generateApplyPrompt(propContext, unit))}
                        disabled={isStreaming}
                        className={`py-1 px-1.5 rounded-lg text-[10px] font-bold flex items-center justify-center space-x-1 transition-all shadow-sm ${
                          isStreaming
                            ? 'bg-indigo-950 text-indigo-400/50 cursor-not-allowed'
                            : 'bg-indigo-600 hover:bg-indigo-500 text-white'
                        }`}
                        title="Submit digital lease application"
                      >
                        <MessageSquareQuote className="w-3 h-3" />
                        <span>Apply</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3D Virtual Tour Modal */}
      <VirtualTourModal
        isOpen={!!selected3DTour}
        onClose={() => setSelected3DTour(null)}
        tourUrl={selected3DTour?.url}
        propertyTitle={selected3DTour?.title}
      />
    </>
  );
};
