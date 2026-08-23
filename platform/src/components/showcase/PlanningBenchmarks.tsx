import React from 'react';
import { Cpu, Shield, GitBranch, Sliders, CheckCircle2 } from 'lucide-react';
import { Card, SectionHeader } from '../common/Card';
import { Badge } from '../common/Badge';

export const PlanningBenchmarks: React.FC = () => {
  return (
    <Card className="p-6 sm:p-8 space-y-6">
      <SectionHeader
        icon={Cpu}
        title="Autonomous Planning & MCTS Search Engine (Week 4)"
        subtitle="Multi-algorithm planning and tree search benchmarked across enterprise property management workflows"
        iconColor="text-purple-400 bg-purple-500/10 border-purple-500/20"
      />

      {/* Enterprise Incident Scenario Banner */}
      <div className="p-4.5 rounded-2xl bg-indigo-500/5 border border-indigo-500/20 space-y-2">
        <div className="flex items-center space-x-2">
          <span className="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-gradient-to-r from-pink-500 to-purple-600 text-white">
            Enterprise Incident
          </span>
          <span className="text-xs font-bold text-slate-200">
            Nile Plaza Cairo — Plumbing Riser Burst & Multi-Unit Relocation
          </span>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          Requires coordinated multi-contractor dispatch under strict{' '}
          <strong className="text-slate-200">Egyptian Tenancy Law 4/1996 (Clause 8.1c 4-hour SLA)</strong>, habitability
          verification, and candidate tenant relocation escrow adjustments. Demonstrates why autonomous planning and
          tree search outperform single-shot generation on high-branching, failure-prone real estate workflows.
        </p>
      </div>

      {/* 4 Algorithm Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2 hover:border-slate-700 transition-all">
          <div className="text-xs font-bold text-slate-300">Plan-and-Solve (PS)</div>
          <div className="text-2xl font-black text-slate-200 font-mono">60.0%</div>
          <div className="text-[10px] text-slate-400 leading-normal">
            Single-pass linear execution — O(K) latency, best for simple deterministic notices.
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2 hover:border-indigo-500/40 transition-all">
          <div className="text-xs font-bold text-slate-300">Tree of Thoughts (ToT)</div>
          <div className="text-2xl font-black text-indigo-400 font-mono">85.0%</div>
          <div className="text-[10px] text-slate-400 leading-normal">
            Multi-branch Beam Search with heuristic state evaluation — ideal for candidate vendor ranking.
          </div>
        </div>

        <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-500/40 space-y-2 ring-1 ring-indigo-500/20 hover:border-indigo-400 transition-all">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold text-indigo-300">LATS (Grounded Env)</div>
            <Badge variant="indigo" size="sm">BEST</Badge>
          </div>
          <div className="text-2xl font-black text-emerald-400 font-mono">90.0%</div>
          <div className="text-[10px] text-slate-300 leading-normal">
            MCTS + Grounded DB & Law 4/1996 checks (+40% accuracy over ungrounded self-critique).
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2 hover:border-cyan-500/40 transition-all">
          <div className="text-xs font-bold text-slate-300">Dynamic DAG Planner</div>
          <div className="text-2xl font-black text-cyan-400 font-mono">90.0%</div>
          <div className="text-[10px] text-slate-400 leading-normal">
            Interleaved execution dynamically reshaping topological plan on intermediate observation failure.
          </div>
        </div>
      </div>

      {/* Master Planning Benchmark Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left text-xs border-collapse font-mono">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 bg-slate-950/70">
              <th className="p-3">Sub-task / Concern</th>
              <th className="p-3">Planning Method</th>
              <th className="p-3">Task Success Rate</th>
              <th className="p-3">Avg LLM Calls</th>
              <th className="p-3">Avg Tokens</th>
              <th className="p-3">Latency (s)</th>
              <th className="p-3">Est. Cost</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            <tr className="text-slate-400 hover:bg-slate-900/40">
              <td className="p-3">Top-level Request</td>
              <td className="p-3">Decomposition-First (Static)</td>
              <td className="p-3">14/20 (70.0%)</td>
              <td className="p-3">1 plan + 4 nodes</td>
              <td className="p-3">6,200</td>
              <td className="p-3">3.2s</td>
              <td className="p-3">$0.04</td>
            </tr>
            <tr className="bg-indigo-600/10 text-slate-200 font-semibold border-l-2 border-indigo-500">
              <td className="p-3">Top-level Request</td>
              <td className="p-3 text-indigo-300 font-bold">Dynamic Decomposition</td>
              <td className="p-3 text-emerald-400 font-bold">18/20 (90.0%)</td>
              <td className="p-3">~7 (adaptive)</td>
              <td className="p-3">8,900</td>
              <td className="p-3">5.1s</td>
              <td className="p-3">$0.06</td>
            </tr>
            <tr className="text-slate-400 hover:bg-slate-900/40">
              <td className="p-3">Task 1: Vendor Ranking</td>
              <td className="p-3">Plan-and-Solve (PS)</td>
              <td className="p-3">12/20 (60.0%)</td>
              <td className="p-3">1</td>
              <td className="p-3">1,500</td>
              <td className="p-3">0.9s</td>
              <td className="p-3">$0.01</td>
            </tr>
            <tr className="bg-indigo-600/10 text-slate-200 font-semibold border-l-2 border-indigo-500">
              <td className="p-3">Task 1: Vendor Ranking</td>
              <td className="p-3 text-indigo-300 font-bold">Tree of Thoughts (ToT Beam)</td>
              <td className="p-3 text-emerald-400 font-bold">17/20 (85.0%)</td>
              <td className="p-3">8</td>
              <td className="p-3">5,400</td>
              <td className="p-3">3.6s</td>
              <td className="p-3">$0.04</td>
            </tr>
            <tr className="text-slate-400 hover:bg-slate-900/40">
              <td className="p-3">Task 2: Relocation Plan</td>
              <td className="p-3">LATS (Ungrounded Env)</td>
              <td className="p-3">10/20 (50.0%)</td>
              <td className="p-3">10</td>
              <td className="p-3">7,400</td>
              <td className="p-3">5.8s</td>
              <td className="p-3">$0.05</td>
            </tr>
            <tr className="bg-indigo-600/10 text-slate-200 font-semibold border-l-2 border-indigo-500">
              <td className="p-3">Task 2: Relocation Plan</td>
              <td className="p-3 text-indigo-300 font-bold">LATS (Grounded Env)</td>
              <td className="p-3 text-emerald-400 font-bold">18/20 (90.0%)</td>
              <td className="p-3">12</td>
              <td className="p-3">8,200</td>
              <td className="p-3">6.5s</td>
              <td className="p-3">$0.07</td>
            </tr>
            <tr className="text-slate-400 hover:bg-slate-900/40">
              <td className="p-3">Sub-task Revision</td>
              <td className="p-3">Self-Refine (Rubric Critique)</td>
              <td className="p-3">15/20 (75.0%)</td>
              <td className="p-3">3</td>
              <td className="p-3">3,100</td>
              <td className="p-3">2.4s</td>
              <td className="p-3">$0.02</td>
            </tr>
            <tr className="bg-indigo-600/10 text-slate-200 font-semibold border-l-2 border-indigo-500">
              <td className="p-3">Sub-task Revision</td>
              <td className="p-3 text-indigo-300 font-bold">Reflexion (Episodic Buffer)</td>
              <td className="p-3 text-emerald-400 font-bold">19/20 (95.0%)</td>
              <td className="p-3">6</td>
              <td className="p-3">6,800</td>
              <td className="p-3">4.8s</td>
              <td className="p-3">$0.05</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Grounded vs Ungrounded Callouts */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 space-y-1.5">
          <div className="text-xs font-bold text-rose-400 uppercase tracking-wider">
            ❌ Ungrounded Self-Critique (0.90 Pass)
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Model self-scoring gave a 24-hour plumbing dispatch a 90% score because the plan sounded complete and
            well-formatted. Resulted in an illegal tenant displacement lawsuit under Egyptian statutes.
          </p>
        </div>
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 space-y-1.5">
          <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
            ✅ Grounded Environment Feedback (0.10 Failed)
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Grounded evaluator verified DB scheduling and flagged:{' '}
            <em className="text-emerald-300 font-semibold">
              "LAW 4/1996 VIOLATION: Clause 8.1c requires emergency dispatch within 4 hours."
            </em>{' '}
            Triggered Reflexion retry to fix the schedule.
          </p>
        </div>
      </div>
    </Card>
  );
};
