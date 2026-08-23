import React from 'react';
import { BookOpen, Search } from 'lucide-react';

interface RagDocBrowserProps {
  ragDocs: any[];
  searchQuery: string;
  onSearchChange: (q: string) => void;
}

export const RagDocBrowser: React.FC<RagDocBrowserProps> = ({
  ragDocs,
  searchQuery,
  onSearchChange
}) => {
  const filteredDocs = ragDocs.filter((d) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      d.title?.toLowerCase().includes(q) ||
      d.content?.toLowerCase().includes(q) ||
      d.section_id?.toLowerCase().includes(q)
    );
  });

  return (
    <section className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-cyan-400" />
            <span>RAG Knowledge Store & Policy Binder Browser</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Live index of {ragDocs.length} policy sections ingested across Naive, Hybrid, Agentic, Graph, and PGVector stores.
          </p>
        </div>

        <div className="relative min-w-[260px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search policy binder (e.g. deposit, SLA)..."
            className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredDocs.map((doc, idx) => (
          <div key={idx} className="glass-card-hover p-4 space-y-2 border-slate-800/80 flex flex-col justify-between">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[10px]">
                <span className="font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                  {doc.section_id || `Section ${idx + 1}`}
                </span>
                <span className="capitalize text-slate-400">{doc.metadata?.doc_type || 'Policy'}</span>
              </div>
              <h3 className="text-xs font-bold text-slate-200">{doc.title}</h3>
              <p className="text-[11px] text-slate-400 leading-relaxed line-clamp-3">{doc.content}</p>
            </div>

            <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-500">
              <span>City: {doc.metadata?.city || 'All'}</span>
              <span>Role: {doc.metadata?.role || 'All'}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
