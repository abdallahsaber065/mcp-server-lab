import React from 'react';
import { Star, Quote, CheckCircle2 } from 'lucide-react';

export const TestimonialSection: React.FC = () => {
  const testimonials = [
    {
      name: 'Ambassador Jean-Luc Picard',
      role: 'Diplomatic Resident • Nile Plaza Luxury Residences',
      quote:
        'The security, uninterrupted Nile vistas, and discreet concierge service at Nile Plaza exceed international diplomatic standards. Any maintenance or service requirement is resolved autonomously within the hour.',
      rating: 5,
      avatar: 'JP'
    },
    {
      name: 'Laila Soliman',
      role: 'Art Director • Zamalek Royal Heritage Suites',
      quote:
        'Living in the historic heart of Zamalek with high ceilings and restored French moldings has been breathtaking. Cornerstone’s digital tenant portal and transparent lease governance make leasing completely seamless.',
      rating: 5,
      avatar: 'LS'
    },
    {
      name: 'Tarek Mahmoud',
      role: 'Managing Director • Apex Middle East Holding',
      quote:
        'Our regional corporate headquarters at Cornerstone Financial Park gives us LEED Gold efficiency and enterprise fiber reliability. The autonomous facility management infrastructure is first-class.',
      rating: 5,
      avatar: 'TM'
    }
  ];

  return (
    <section className="space-y-6">
      <div className="text-center max-w-2xl mx-auto space-y-2">
        <div className="inline-flex items-center space-x-1.5 text-xs font-bold text-amber-400 uppercase tracking-wider">
          <Star className="w-3.5 h-3.5 fill-amber-400" />
          <span>Resident & Investor Trust</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Trusted by Discerning Residents & Corporate Leaders
        </h2>
        <p className="text-xs sm:text-sm text-slate-400">
          Hear from high-profile diplomats, executives, and families who call Cornerstone properties home.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {testimonials.map((t, i) => (
          <div
            key={i}
            className="glass-card p-6 rounded-2xl border-slate-800 space-y-4 flex flex-col justify-between shadow-lg relative"
          >
            <Quote className="w-8 h-8 text-indigo-500/20 absolute top-4 right-4" />

            <div className="space-y-3">
              <div className="flex items-center space-x-1">
                {[...Array(t.rating)].map((_, idx) => (
                  <Star key={idx} className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                ))}
              </div>
              <p className="text-xs text-slate-300 leading-relaxed italic">
                "{t.quote}"
              </p>
            </div>

            <div className="pt-4 border-t border-slate-800 flex items-center space-x-3">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-xs text-white shadow-md">
                {t.avatar}
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-100 flex items-center gap-1">
                  {t.name}
                  <CheckCircle2 className="w-3 h-3 text-emerald-400 inline" />
                </h4>
                <p className="text-[10px] text-slate-400">{t.role}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
