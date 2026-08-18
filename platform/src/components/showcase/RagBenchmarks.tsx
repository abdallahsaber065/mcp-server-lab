import React from 'react';
import { Database } from 'lucide-react';
import { Card, SectionHeader } from '../common/Card';

export const RagBenchmarks: React.FC = () => {
  return (
    <Card className="p-6 space-y-4">
      <SectionHeader
        icon={Database}
        title="Multi-Architecture RAG (Week 3)"
        subtitle="4 retrieval strategies benchmarked across 12 domain questions"
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
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            <tr className="text-slate-400">
              <td className="p-2.5">Naive RAG</td>
              <td className="p-2.5">8/12 (66.7%)</td>
              <td className="p-2.5">175</td>
              <td className="p-2.5">&lt;0.001s</td>
            </tr>
            <tr className="text-slate-400">
              <td className="p-2.5">Hybrid Search</td>
              <td className="p-2.5">9/12 (75.0%)</td>
              <td className="p-2.5">210</td>
              <td className="p-2.5">0.001s</td>
            </tr>
            <tr className="bg-indigo-600/10 text-slate-200 font-bold border-l-2 border-indigo-500">
              <td className="p-2.5 text-indigo-300">Agentic RAG</td>
              <td className="p-2.5 text-emerald-400">11/12 (91.7%)</td>
              <td className="p-2.5">391</td>
              <td className="p-2.5">0.001s</td>
            </tr>
            <tr className="text-slate-400">
              <td className="p-2.5">Graph RAG</td>
              <td className="p-2.5">2/12 (16.7%)</td>
              <td className="p-2.5">17</td>
              <td className="p-2.5">&lt;0.001s</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p className="text-[11px] text-slate-400 leading-normal">
        <strong className="text-indigo-400">Key Insight:</strong> Agentic RAG multi-hop query decomposition wins on
        complex cross-unit comparisons where naive semantic similarity suffers query embedding dilution.
      </p>
    </Card>
  );
};
