import React from 'react';
import { Sliders } from 'lucide-react';
import { Card, SectionHeader } from '../common/Card';

export const ContextBenchmarks: React.FC = () => {
  return (
    <Card className="p-6 space-y-4">
      <SectionHeader
        icon={Sliders}
        title="Context Window Management (Week 3)"
        subtitle="4 pruning strategies across 40-turn dialogue test suite"
        iconColor="text-amber-400 bg-amber-500/10 border-amber-500/20"
      />

      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left text-xs border-collapse font-mono">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 bg-slate-950/70">
              <th className="p-2.5">Strategy</th>
              <th className="p-2.5">Recall</th>
              <th className="p-2.5">Input Tokens</th>
              <th className="p-2.5">Output Tokens</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            <tr className="text-slate-400">
              <td className="p-2.5">Sliding Window (10)</td>
              <td className="p-2.5 text-rose-400">0/10 (0%)</td>
              <td className="p-2.5">2,365</td>
              <td className="p-2.5">120</td>
            </tr>
            <tr className="bg-indigo-600/10 text-slate-200 font-bold border-l-2 border-indigo-500">
              <td className="p-2.5 text-indigo-300">Observation Masking</td>
              <td className="p-2.5 text-emerald-400">10/10 (100%)</td>
              <td className="p-2.5 text-emerald-400">1,984</td>
              <td className="p-2.5">200</td>
            </tr>
            <tr className="text-slate-400">
              <td className="p-2.5">Recursive Summary</td>
              <td className="p-2.5">4/10 (40%)</td>
              <td className="p-2.5">2,281</td>
              <td className="p-2.5">152</td>
            </tr>
            <tr className="text-slate-400">
              <td className="p-2.5">Zone-Based Pruning</td>
              <td className="p-2.5 text-rose-400">0/10 (0%)</td>
              <td className="p-2.5">2,623</td>
              <td className="p-2.5">120</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p className="text-[11px] text-slate-400 leading-normal">
        <strong className="text-emerald-400">Key Insight:</strong> Observation Masking achieves 100% recall at lowest
        token cost because tool JSON payload is the primary context bloat — not conversational dialogue.
      </p>
    </Card>
  );
};
