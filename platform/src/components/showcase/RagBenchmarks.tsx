import React from 'react';
import { Database, Sparkles, ShieldCheck } from 'lucide-react';
import { Card, SectionHeader } from '../common/Card';

export const RagBenchmarks: React.FC = () => {
  return (
    <Card className="p-6 space-y-4">
      <SectionHeader
        icon={Database}
        title="Multi-Architecture RAG Subsystem"
        subtitle="5 retrieval strategies benchmarked with Google Gemini Embeddings 2 and PostgreSQL pgvector"
        iconColor="text-cyan-400 bg-cyan-500/10 border-cyan-500/20"
      />

      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left text-xs border-collapse font-mono">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 bg-slate-950/70">
              <th className="p-2.5">Architecture</th>
              <th className="p-2.5">Accuracy</th>
              <th className="p-2.5">Tokens</th>
              <th className="p-2.5">Latency</th>
              <th className="p-2.5">Security Isolation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            <tr className="bg-cyan-950/30 text-slate-100 font-bold border-l-2 border-cyan-400">
              <td className="p-2.5 text-cyan-300 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                <span>PGVector (Gemini-2 + HNSW)</span>
              </td>
              <td className="p-2.5 text-emerald-400">12/12 (100.0%)</td>
              <td className="p-2.5">245</td>
              <td className="p-2.5">0.002s</td>
              <td className="p-2.5 text-emerald-400 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Role Pre-filtered</span>
              </td>
            </tr>
            <tr className="bg-indigo-600/10 text-slate-200 font-semibold border-l-2 border-indigo-500">
              <td className="p-2.5 text-indigo-300">Agentic RAG (Multi-Hop)</td>
              <td className="p-2.5 text-emerald-400">11/12 (91.7%)</td>
              <td className="p-2.5">391</td>
              <td className="p-2.5">0.001s</td>
              <td className="p-2.5 text-slate-400">Scope Tagged</td>
            </tr>
            <tr className="text-slate-400">
              <td className="p-2.5">Hybrid Search (BM25 + Dense)</td>
              <td className="p-2.5">9/12 (75.0%)</td>
              <td className="p-2.5">210</td>
              <td className="p-2.5">0.001s</td>
              <td className="p-2.5 text-slate-400">Standard</td>
            </tr>
            <tr className="text-slate-400">
              <td className="p-2.5">Naive Dense Vector</td>
              <td className="p-2.5">8/12 (66.7%)</td>
              <td className="p-2.5">175</td>
              <td className="p-2.5">&lt;0.001s</td>
              <td className="p-2.5 text-slate-400">Unfiltered</td>
            </tr>
            <tr className="text-slate-400">
              <td className="p-2.5">Graph RAG (Entity Paths)</td>
              <td className="p-2.5">2/12 (16.7%)</td>
              <td className="p-2.5">17</td>
              <td className="p-2.5">&lt;0.001s</td>
              <td className="p-2.5 text-slate-400">Entity Scoped</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p className="text-[11px] text-slate-400 leading-normal">
        <strong className="text-cyan-400">Production Highlight:</strong> PGVector with Google Gemini Embedding 2 MRL (768 dims) + HNSW cosine index achieves 100% retrieval precision with strict zero-leakage role permission pre-filtering.
      </p>
    </Card>
  );
};
