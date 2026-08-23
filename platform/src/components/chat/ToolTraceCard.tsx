import React, { useState } from 'react';
import { Wrench, ChevronDown, CheckCircle2, AlertCircle } from 'lucide-react';
import { JsonBlock } from '../common/JsonBlock';

interface ToolTraceItem {
  tool: string;
  args: any;
  result: any;
  status?: string;
}

interface ToolTraceCardProps {
  trace: ToolTraceItem;
}

export const ToolTraceCard: React.FC<ToolTraceCardProps> = ({ trace }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const isError = trace.status === 'error';

  return (
    <div
      className={`rounded-xl border overflow-hidden text-xs transition-all ${
        isError ? 'bg-rose-950/20 border-rose-500/30' : 'bg-slate-950/70 border-slate-800/80'
      }`}
    >
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="p-2.5 flex items-center justify-between cursor-pointer hover:bg-slate-900/60 transition-colors select-none"
      >
        <div className="flex items-center space-x-2 truncate">
          <Wrench className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
          <span className="font-mono font-bold text-slate-200 truncate">{trace.tool}</span>
          <span
            className={`px-1.5 py-0.2 rounded text-[9px] font-bold border ${
              isError
                ? 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
            }`}
          >
            {isError ? 'ERROR' : 'SUCCESS'}
          </span>
        </div>
        <ChevronDown
          className={`w-3.5 h-3.5 text-slate-500 transition-transform duration-200 shrink-0 ml-2 ${
            isExpanded ? 'rotate-180' : ''
          }`}
        />
      </div>

      {isExpanded && (
        <div className="p-3 bg-slate-950/95 border-t border-slate-800/80 space-y-3 font-mono text-[11px]">
          {/* Custom Property Audit Scorecard Visual Widget */}
          {trace.tool === 'run_property_audit' && trace.result && (
            <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 space-y-2.5">
              <div className="flex items-center justify-between text-xs font-bold text-slate-200">
                <span>Property #{trace.args?.property_id || 1} Compliance Audit</span>
                <span className="text-emerald-400 font-mono">
                  {trace.result.occupancy_rate || '100%'} Occupied
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center text-[10px]">
                <div className="p-1.5 rounded-lg bg-slate-900 border border-slate-800">
                  <div className="text-slate-500">Total Units</div>
                  <div className="font-bold text-slate-200 text-xs">{trace.result.total_units || 6}</div>
                </div>
                <div className="p-1.5 rounded-lg bg-slate-900 border border-slate-800">
                  <div className="text-slate-500">Occupied</div>
                  <div className="font-bold text-emerald-400 text-xs">{trace.result.occupied_units || 5}</div>
                </div>
                <div className="p-1.5 rounded-lg bg-slate-900 border border-slate-800">
                  <div className="text-slate-500">Available</div>
                  <div className="font-bold text-cyan-400 text-xs">
                    {(trace.result.total_units || 6) - (trace.result.occupied_units || 5)}
                  </div>
                </div>
              </div>
            </div>
          )}

          <JsonBlock data={trace.args} title="Input Arguments" />
          <JsonBlock data={trace.result} title="Output Result" />
        </div>
      )}
    </div>
  );
};
