import React, { useEffect, useState } from 'react';
import { Building2, MapPin, Bed, Bath, ArrowRight, Eye, Calendar, Sparkles, MessageSquareQuote } from 'lucide-react';
import { apiClient } from '../../services/api';
import { useAppStore } from '../../stores/useAppStore';
import { generateTourPrompt } from '../../utils/propertyPrompts';

interface FeaturedPropertiesProps {
  onSelectProperty: (propertyId: number) => void;
  onOpenScheduleModal?: (propertyId: number) => void;
}

export const FeaturedProperties: React.FC<FeaturedPropertiesProps> = ({
  onSelectProperty
}) => {
  const { setCurrentPage, navigateToChatWithPrompt } = useAppStore();
  const [featured, setFeatured] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadFeatured() {
      try {
        const res = await apiClient<{ featured: any[] }>('/api/properties/featured', { skipAuth: true });
        setFeatured(res.featured || []);
      } catch (err) {
        console.error('Failed to load featured properties:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadFeatured();
  }, []);

  return (
    <section className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
        <div>
          <div className="inline-flex items-center space-x-2 text-xs font-bold text-indigo-400 uppercase tracking-wider mb-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Curated Portfolio</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Featured Luxury Residences
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Handpicked trophy real estate holdings available for immediate private leasing.
          </p>
        </div>

        <button
          onClick={() => setCurrentPage('properties')}
          className="self-start sm:self-auto px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center space-x-2 transition-all group"
        >
          <span>View All Units</span>
          <ArrowRight className="w-3.5 h-3.5 text-indigo-400 group-hover:translate-x-1 transition-transform" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {featured.map((prop) => (
          <div
            key={prop.property_id}
            className="glass-card-hover rounded-2xl overflow-hidden border border-slate-800 flex flex-col justify-between group shadow-lg"
          >
            {/* Property Image with Badge & Hover Action */}
            <div className="relative h-56 overflow-hidden bg-slate-900 cursor-pointer" onClick={() => onSelectProperty(prop.property_id)}>
              <img
                src={prop.image_url || '/images/properties/nile_tower_ext.jpg'}
                alt={prop.name}
                onError={(e) => {
                  e.currentTarget.src = '/images/properties/nile_tower_ext.jpg';
                }}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent opacity-80" />

              {/* Top Non-Overlapping Badges Bar */}
              <div className="absolute top-3 inset-x-3 flex items-start justify-between gap-2 pointer-events-none z-10">
                <span className="px-2 py-0.5 rounded-md text-[10px] font-extrabold bg-indigo-600/90 text-white backdrop-blur-md shadow-md uppercase tracking-wider">
                  Verified Luxury
                </span>
                <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold bg-slate-950/85 text-emerald-300 border border-emerald-500/40 backdrop-blur-md shadow-md">
                  {prop.available_units || 2} Units
                </span>
              </div>

              <div className="absolute bottom-3 left-3 right-3 flex items-end justify-between text-white">
                <div>
                  <div className="text-[11px] text-slate-300 flex items-center gap-1 font-medium">
                    <MapPin className="w-3.5 h-3.5 text-indigo-400" />
                    <span>{prop.neighborhood || prop.city}</span>
                  </div>
                  <h3 className="text-base font-bold text-white leading-tight mt-0.5">{prop.name}</h3>
                </div>
              </div>
            </div>

            {/* Content & Specs */}
            <div className="p-5 space-y-4 flex-1 flex flex-col justify-between">
              <div className="space-y-2.5">
                <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                  {prop.description}
                </p>

                {/* Amenities Badges */}
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {(prop.amenities || []).slice(0, 3).map((amenity: string, i: number) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded-md text-[10px] bg-slate-800/80 text-slate-300 border border-slate-700/60"
                    >
                      {amenity}
                    </span>
                  ))}
                  {(prop.amenities || []).length > 3 && (
                    <span className="px-2 py-0.5 rounded-md text-[10px] bg-slate-900 text-slate-500">
                      +{prop.amenities.length - 3} more
                    </span>
                  )}
                </div>
              </div>

              {/* Price and CTA Buttons */}
              <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between gap-2">
                <div>
                  <span className="text-[10px] text-slate-400 block font-medium uppercase">Starting from</span>
                  <span className="text-base font-extrabold text-emerald-400 font-mono">
                    {prop.starting_rent?.toLocaleString()} <span className="text-xs font-normal text-slate-400">EGP / mo</span>
                  </span>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => navigateToChatWithPrompt(generateTourPrompt(prop))}
                    title="Book Viewing with AI Assistant"
                    className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all flex items-center gap-1 text-xs"
                  >
                    <Calendar className="w-4 h-4 text-amber-400" />
                  </button>

                  <button
                    onClick={() => onSelectProperty(prop.property_id)}
                    className="px-3.5 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white flex items-center space-x-1 transition-all shadow-md shadow-indigo-600/20"
                  >
                    <Eye className="w-3.5 h-3.5 mr-1" />
                    <span>Inspect</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
