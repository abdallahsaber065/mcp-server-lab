import { Handle, Position, type NodeProps } from '@xyflow/react';
import { motion } from 'framer-motion';
import { CheckCircle2, PauseCircle, Clock, AlertTriangle, Zap, FileSearch, ScanSearch, Users, Scale } from 'lucide-react';

const statusConfig: Record<string, { bg: string; border: string; glow: string; icon: any }> = {
  completed: { bg: 'bg-emerald-950/40', border: 'border-emerald-500/60', glow: 'shadow-emerald-500/20', icon: CheckCircle2 },
  running: { bg: 'bg-indigo-950/50', border: 'border-indigo-500/80', glow: 'shadow-indigo-500/30', icon: Zap },
  paused_hitl: { bg: 'bg-amber-950/50', border: 'border-amber-500/80', glow: 'shadow-amber-500/30', icon: PauseCircle },
  awaiting_webhook: { bg: 'bg-cyan-950/40', border: 'border-cyan-500/60', glow: 'shadow-cyan-500/20', icon: Clock },
  failed: { bg: 'bg-rose-950/40', border: 'border-rose-500/60', glow: 'shadow-rose-500/20', icon: AlertTriangle },
  idle: { bg: 'bg-slate-900/60', border: 'border-slate-700/60', glow: 'shadow-black/0', icon: Clock },
};

function NodeShell({ id, data, label, desc, step, llmTag }: NodeProps & { label: string; desc: string; step: number; llmTag?: string }) {
  const d: any = data as any;
  const status: string = d.status || 'idle';
  const cfg = statusConfig[status] || statusConfig.idle;
  const Icon = cfg.icon;
  const isActive = status === 'running' || status === 'paused_hitl' || status === 'awaiting_webhook';
  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: (d.idx || 0) * 0.06, type: 'spring', stiffness: 260, damping: 20 }}
      className={`min-w-[220px] max-w-[260px] rounded-2xl border backdrop-blur-xl p-4 shadow-lg ${cfg.bg} ${cfg.border} ${cfg.glow} ${isActive ? 'shadow-xl' : ''} relative`}
    >
      {/* Handles for controlled edge directions */}
      <Handle type="target" position={Position.Top} id="top" style={{ opacity: 0, width: 8, height: 8, top: -4 }} isConnectable={false} />
      <Handle type="target" position={Position.Left} id="left" style={{ opacity: 0, width: 8, height: 8, left: -4 }} isConnectable={false} />
      <Handle type="target" position={Position.Right} id="right" style={{ opacity: 0, width: 8, height: 8, right: -4 }} isConnectable={false} />
      <Handle type="source" position={Position.Bottom} id="bottom" style={{ opacity: 0, width: 8, height: 8, bottom: -4 }} isConnectable={false} />
      <Handle type="source" position={Position.Right} id="right-source" style={{ opacity: 0, width: 8, height: 8, right: -4 }} isConnectable={false} />
      <Handle type="source" position={Position.Left} id="left-source" style={{ opacity: 0, width: 8, height: 8, left: -4 }} isConnectable={false} />
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[10px] font-bold tracking-wider text-slate-400">STEP {step}</span>
        <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold ${status === 'completed' ? 'bg-emerald-500/20 text-emerald-300' : status === 'running' ? 'bg-indigo-500/20 text-indigo-300' : status === 'paused_hitl' ? 'bg-amber-500/20 text-amber-300' : status === 'awaiting_webhook' ? 'bg-cyan-500/20 text-cyan-300' : 'bg-slate-800 text-slate-400'}`}>
          {status.toUpperCase()}
        </span>
      </div>
      <div className="flex items-center gap-2 mb-1">
        <div className={`w-7 h-7 rounded-xl flex items-center justify-center border ${status === 'running' ? 'bg-indigo-500/20 border-indigo-500/30' : 'bg-slate-800/60 border-slate-700/50'}`}>
          <Icon className={`w-3.5 h-3.5 ${status === 'completed' ? 'text-emerald-400' : status === 'running' ? 'text-indigo-400 animate-pulse' : status === 'paused_hitl' ? 'text-amber-400 animate-pulse' : status === 'awaiting_webhook' ? 'text-cyan-400' : 'text-slate-500'}`} />
        </div>
        <div className="font-bold text-xs text-slate-100 leading-tight">{label}</div>
      </div>
      <div className="text-[11px] text-slate-400 leading-snug">{desc}</div>
      {llmTag && <div className="mt-2 text-[9px] px-2 py-1 rounded-full bg-violet-500/15 border border-violet-500/30 text-violet-300 inline-block">{llmTag}</div>}
      {d.message && <div className="mt-2 text-[10px] text-slate-300/80 bg-slate-950/50 rounded-lg p-2 border border-slate-800">{String(d.message).slice(0, 120)}</div>}
    </motion.div>
  );
}

export function GlassNode(props: NodeProps) {
  const d: any = props.data as any;
  return <NodeShell {...props} label={d.label} desc={d.description} step={d.step} llmTag={d.llmTag} />;
}
export function HitlNode(props: NodeProps) {
  const d: any = props.data as any;
  return <NodeShell {...props} label={d.label} desc={d.description} step={d.step} llmTag={d.llmTag} />;
}
export function WebhookNode(props: NodeProps) {
  const d: any = props.data as any;
  return <NodeShell {...props} label={d.label} desc={d.description} step={d.step} llmTag={d.llmTag} />;
}
export function TicketNode(props: NodeProps) {
  const d: any = props.data as any;
  return <NodeShell {...props} label={d.label} desc={d.description} step={d.step} llmTag={d.llmTag} />;
}

// Icon helpers for catalog labels
export const catalogIcons: Record<string, any> = {
  decompose: FileSearch,
  audit: ScanSearch,
  vision: ScanSearch,
  accountant: Users,
  escrow: Scale,
  retrieve: FileSearch,
  lats: Zap,
  engineer: Users,
  rating: Users,
  arrears: FileSearch,
  react: ScanSearch,
  tot: Zap,
  choice: Users,
  counsel: Scale,
};
