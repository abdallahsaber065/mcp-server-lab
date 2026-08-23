import React from 'react';
import { Bot, ShieldCheck, Zap, FileText, Headphones, Key } from 'lucide-react';
import { useAppStore } from '../../stores/useAppStore';

export const ConciergeServices: React.FC = () => {
  const { setCurrentPage } = useAppStore();

  const services = [
    {
      icon: Bot,
      title: 'Autonomous Digital Concierge',
      color: 'text-indigo-400',
      border: 'border-indigo-500/20',
      description: '24/7 intelligent resident assistant capable of answering legal lease inquiries, booking amenities, and dispatching contractors in seconds.'
    },
    {
      icon: ShieldCheck,
      title: 'Grounded Egyptian Law 4/1996 Compliance',
      color: 'text-emerald-400',
      border: 'border-emerald-500/20',
      description: 'Zero-hallucination verification engine ensuring all lease terms, security deposits, and emergency SLA guidelines strictly adhere to national standards.'
    },
    {
      icon: FileText,
      title: 'Instant Verified Digital Leases',
      color: 'text-cyan-400',
      border: 'border-cyan-500/20',
      description: 'Streamlined online application and automated credit verification with high-value executive signoffs handled securely in real-time.'
    },
    {
      icon: Key,
      title: 'VIP Private Accompanied Viewings',
      color: 'text-amber-400',
      border: 'border-amber-500/20',
      description: 'Schedule in-person or high-resolution 3D virtual walkthroughs with dedicated licensed property specialists at your preferred time.'
    }
  ];

  return (
    <section className="glass-card p-8 sm:p-12 rounded-3xl border-slate-800 space-y-8 shadow-xl">
      <div className="max-w-3xl space-y-2">
        <div className="inline-flex items-center space-x-2 text-xs font-bold text-indigo-400 uppercase tracking-wider">
          <Zap className="w-3.5 h-3.5" />
          <span>The Cornerstone Advantage</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Enterprise Property Management & Autonomous AI Care
        </h2>
        <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
          Combining bespoke five-star hospitality with state-of-the-art cognitive agent architecture to deliver effortless tenancy and asset management.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {services.map((s, i) => {
          const Icon = s.icon;
          return (
            <div
              key={i}
              className={`p-6 rounded-2xl bg-slate-900/60 border ${s.border} space-y-3 hover:bg-slate-900 transition-all shadow-md`}
            >
              <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center">
                <Icon className={`w-5 h-5 ${s.color}`} />
              </div>
              <h3 className="text-sm font-bold text-slate-100">{s.title}</h3>
              <p className="text-xs text-slate-400 leading-relaxed">{s.description}</p>
            </div>
          );
        })}
      </div>

      <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-slate-900 border border-indigo-500/30 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center shrink-0">
            <Headphones className="w-6 h-6 text-indigo-300" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-white">Experience our Autonomous Concierge Assistant</h4>
            <p className="text-xs text-slate-400">Ask about available penthouse terms, lease discounts, or Egyptian real estate regulations.</p>
          </div>
        </div>

        <button
          onClick={() => setCurrentPage('chat')}
          className="px-5 py-2.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30 transition-all shrink-0 flex items-center space-x-2"
        >
          <Bot className="w-4 h-4" />
          <span>Chat with Concierge</span>
        </button>
      </div>
    </section>
  );
};
