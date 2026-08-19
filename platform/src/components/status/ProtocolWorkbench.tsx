import React from 'react';
import {
  Shield,
  Play,
  Bell,
  AlertTriangle,
  BookOpen,
  FileCode,
  Activity
} from 'lucide-react';

interface ProtocolWorkbenchProps {
  onRunTest: (testId: string) => Promise<void>;
  testOutputs: Record<string, any>;
  isProgressRunning: boolean;
  progressStep: number;
}

export const ProtocolWorkbench: React.FC<ProtocolWorkbenchProps> = ({
  onRunTest,
  testOutputs,
  isProgressRunning,
  progressStep
}) => {
  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Shield className="w-5 h-5 text-indigo-400" />
            <span>MCP Protocol — 8 Core Concerns Interactive Workbench</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Execute live protocol handshakes, notifications, human-in-the-loop elicitation, and progress streaming.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {/* 1. Capability Negotiation */}
        <div className="glass-card p-5 space-y-4 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-indigo-300">1. Capability Negotiation</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-indigo-500/20 text-indigo-300">initialize</span>
            </div>
            <p className="text-xs text-slate-400">
              Handshake negotiation declaring server capabilities, tool list notifications, and elicitation support.
            </p>
          </div>
          <button
            onClick={() => onRunTest('capabilities')}
            className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-indigo-600/80 hover:bg-indigo-600 text-white flex items-center justify-center space-x-1.5 transition-all shadow-md"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Test Capability Negotiation</span>
          </button>
          {testOutputs.capabilities && (
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] font-mono text-slate-300 overflow-x-auto max-h-48">
              {testOutputs.capabilities.loading ? (
                <div className="text-indigo-400">Executing capability negotiation...</div>
              ) : (
                <pre>{JSON.stringify(testOutputs.capabilities.data, null, 2)}</pre>
              )}
            </div>
          )}
        </div>

        {/* 2. Notifications */}
        <div className="glass-card p-5 space-y-4 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-cyan-300">2. Tool List Notifications</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-500/20 text-cyan-300">tools/list_changed</span>
            </div>
            <p className="text-xs text-slate-400">
              Dynamic notification push when persona changes to filter authorized tools for the Tenant role.
            </p>
          </div>
          <button
            onClick={() => onRunTest('notifications')}
            className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-cyan-600/80 hover:bg-cyan-600 text-white flex items-center justify-center space-x-1.5 transition-all shadow-md"
          >
            <Bell className="w-3.5 h-3.5" />
            <span>Trigger Role Switch Notification</span>
          </button>
          {testOutputs.notifications && (
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] font-mono text-slate-300 overflow-x-auto max-h-48">
              {testOutputs.notifications.loading ? (
                <div className="text-cyan-400">Dispatching notifications/tools/list_changed...</div>
              ) : (
                <pre>{JSON.stringify(testOutputs.notifications.data, null, 2)}</pre>
              )}
            </div>
          )}
        </div>

        {/* 3. Human Elicitation */}
        <div className="glass-card p-5 space-y-4 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-amber-300">3. Human Elicitation</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/20 text-amber-300">elicitation/create</span>
            </div>
            <p className="text-xs text-slate-400">
              Pauses execution when proposed lease discount exceeds 15% threshold for executive sign-off.
            </p>
          </div>
          <button
            onClick={() => onRunTest('elicitation')}
            className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-amber-600/80 hover:bg-amber-600 text-white flex items-center justify-center space-x-1.5 transition-all shadow-md"
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Test &gt;15% Discount Elicitation</span>
          </button>
          {testOutputs.elicitation && (
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] font-mono text-slate-300 overflow-x-auto max-h-48">
              {testOutputs.elicitation.loading ? (
                <div className="text-amber-400">Evaluating discount threshold...</div>
              ) : (
                <pre>{JSON.stringify(testOutputs.elicitation.data, null, 2)}</pre>
              )}
            </div>
          )}
        </div>

        {/* 4. Resources */}
        <div className="glass-card p-5 space-y-4 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-300">4. Static Resources</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-300">resources/read</span>
            </div>
            <p className="text-xs text-slate-400">
              Serves canonical policy URIs (`realty://policies/lease_terms`, `realty://sla/maintenance`).
            </p>
          </div>
          <button
            onClick={() => onRunTest('resources')}
            className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-emerald-600/80 hover:bg-emerald-600 text-white flex items-center justify-center space-x-1.5 transition-all shadow-md"
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Read MCP Resource URI</span>
          </button>
          {testOutputs.resources && (
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] font-mono text-slate-300 overflow-x-auto max-h-48">
              {testOutputs.resources.loading ? (
                <div className="text-emerald-400">Fetching resource payload...</div>
              ) : (
                <pre>{JSON.stringify(testOutputs.resources.data, null, 2)}</pre>
              )}
            </div>
          )}
        </div>

        {/* 5. Prompt Templates */}
        <div className="glass-card p-5 space-y-4 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-rose-300">5. Parameterized Prompts</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-rose-500/20 text-rose-300">prompts/get</span>
            </div>
            <p className="text-xs text-slate-400">
              Renders pre-engineered prompt workflows with tenant variables and policy constraints.
            </p>
          </div>
          <button
            onClick={() => onRunTest('prompts')}
            className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-rose-600/80 hover:bg-rose-600 text-white flex items-center justify-center space-x-1.5 transition-all shadow-md"
          >
            <FileCode className="w-3.5 h-3.5" />
            <span>Render Prompt Template</span>
          </button>
          {testOutputs.prompts && (
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] font-mono text-slate-300 overflow-x-auto max-h-48">
              {testOutputs.prompts.loading ? (
                <div className="text-rose-400">Rendering prompt template...</div>
              ) : (
                <pre>{JSON.stringify(testOutputs.prompts.data, null, 2)}</pre>
              )}
            </div>
          )}
        </div>

        {/* 6. Progress Tracking */}
        <div className="glass-card p-5 space-y-4 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-purple-300">6. Progress Tracking</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-500/20 text-purple-300">progressToken</span>
            </div>
            <p className="text-xs text-slate-400">
              Streams incremental progress notifications during long-running property audits.
            </p>
          </div>
          <button
            onClick={() => onRunTest('progress')}
            disabled={isProgressRunning}
            className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-purple-600/80 hover:bg-purple-600 text-white flex items-center justify-center space-x-1.5 transition-all shadow-md"
          >
            <Activity className={`w-3.5 h-3.5 ${isProgressRunning ? 'animate-spin' : ''}`} />
            <span>{isProgressRunning ? 'Auditing Units...' : 'Stream Audit Progress'}</span>
          </button>

          {isProgressRunning && (
            <div className="space-y-2 p-3 rounded-lg bg-slate-950/80 border border-slate-800">
              <div className="flex justify-between text-[11px] text-purple-300">
                <span>Audit Progress</span>
                <span>{progressStep * 20}%</span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-purple-500 h-full transition-all duration-300"
                  style={{ width: `${progressStep * 20}%` }}
                />
              </div>
              <div className="text-[10px] text-slate-400">
                {progressStep === 1 && 'Scanning 47 units across Cairo & Giza...'}
                {progressStep === 2 && 'Auditing active lease agreements & deposits...'}
                {progressStep === 3 && 'Cross-referencing open maintenance work orders...'}
                {progressStep === 4 && 'Computing portfolio occupancy rate (91.5%)...'}
                {progressStep === 5 && 'Audit complete: 0 compliance violations found.'}
              </div>
            </div>
          )}

          {testOutputs.progress && !isProgressRunning && (
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] font-mono text-slate-300 overflow-x-auto max-h-48">
              <pre>{JSON.stringify(testOutputs.progress.data, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};
