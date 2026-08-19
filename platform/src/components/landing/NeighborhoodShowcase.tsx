import React from 'react';
import { MapPin, Compass, ArrowRight } from 'lucide-react';
import { useAppStore } from '../../stores/useAppStore';

export const NeighborhoodShowcase: React.FC = () => {
  const { setCurrentPage } = useAppStore();

  const neighborhoods = [
    {
      name: 'Zamalek & Garden City',
      city: 'Cairo',
      tag: 'Waterfront & Diplomatic Quarter',
      image: '/images/properties/zamalek_ext.jpg',
      description: 'Cosmopolitan island elegance, tree-lined diplomatic boulevards, Belle Époque architecture, and private yacht docks.',
      count: '3 Available Units'
    },
    {
      name: 'Fifth Settlement & City Center',
      city: 'New Cairo',
      tag: 'Financial & Modern Corporate Enclave',
      image: '/images/properties/new_cairo_ext.jpg',
      description: 'Egypt’s premier commercial and modern residential corridor with Grade-A smart towers, international schools, and private golf compounds.',
      count: '2 Available Suites'
    },
    {
      name: 'Stanley Beach & Mediterranean Corniche',
      city: 'Alexandria',
      tag: 'Mediterranean Seaside Living',
      image: '/images/properties/alexandria_ext.jpg',
      description: 'Iconic panoramic vistas of Stanley Bridge, direct private beach cabanas, saltwater infinity pools, and marine berthing.',
      count: '1 Seafront Penthouse'
    },
    {
      name: 'Pyramids Vista & Dokki Heights',
      city: 'Giza',
      tag: 'Grand Landmark Horizons',
      image: '/images/properties/giza_ext.jpg',
      description: 'Contemporary elevated residences with direct unobstructed sunset sightlines overlooking the Great Pyramids of Giza.',
      count: '2 Sky Apartments'
    }
  ];

  const handleSelectNeighborhood = (city: string) => {
    const params = new URLSearchParams();
    params.set('city', city);
    window.history.replaceState(null, '', `/properties?${params.toString()}`);
    setCurrentPage('properties');
  };

  return (
    <section className="space-y-6">
      <div>
        <div className="inline-flex items-center space-x-2 text-xs font-bold text-cyan-400 uppercase tracking-wider mb-1">
          <Compass className="w-3.5 h-3.5" />
          <span>Prime Destinations</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Explore Egypt's Most Sought-After Neighborhoods
        </h2>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Every district offers distinctive architectural heritage, concierge services, and lifestyle amenities.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {neighborhoods.map((n, i) => (
          <div
            key={i}
            onClick={() => handleSelectNeighborhood(n.city)}
            className="group relative h-80 rounded-2xl overflow-hidden cursor-pointer border border-slate-800 shadow-lg transition-all hover:scale-[1.02] hover:border-indigo-500/50"
          >
            <img
              src={n.image}
              alt={n.name}
              className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/60 to-transparent" />

            <div className="absolute top-3 left-3">
              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-950/80 text-cyan-300 border border-cyan-500/30 backdrop-blur-md">
                {n.tag}
              </span>
            </div>

            <div className="absolute bottom-4 left-4 right-4 space-y-2 text-white">
              <div className="flex items-center space-x-1.5 text-xs text-indigo-300 font-semibold">
                <MapPin className="w-3.5 h-3.5" />
                <span>{n.city}</span>
              </div>
              <h3 className="text-base font-bold text-white group-hover:text-cyan-300 transition-colors leading-tight">
                {n.name}
              </h3>
              <p className="text-[11px] text-slate-300 line-clamp-2 leading-relaxed opacity-90">
                {n.description}
              </p>
              <div className="pt-2 flex items-center justify-between text-[11px] font-bold text-emerald-400 border-t border-slate-700/60">
                <span>{n.count}</span>
                <span className="flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                  Explore <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
