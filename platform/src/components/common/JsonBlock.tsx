import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';

interface JsonBlockProps {
  data: any;
  title?: string;
  maxHeight?: string;
}

export const JsonBlock: React.FC<JsonBlockProps> = ({
  data,
  title,
  maxHeight = 'max-h-56',
}) => {
  const [copied, setCopied] = useState(false);
  const formatted = typeof data === 'string' ? data : JSON.stringify(data, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(formatted);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-xl bg-slate-950/80 border border-slate-800/80 overflow-hidden font-mono text-xs">
      {title && (
        <div className="flex items-center justify-between px-3 py-1.5 bg-slate-900/60 border-b border-slate-800/80 text-[10px] text-slate-400 font-semibold uppercase">
          <span>{title}</span>
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 text-slate-400 hover:text-slate-200 transition-colors"
            title="Copy JSON"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      )}
      <pre className={`p-3 text-slate-300 overflow-x-auto ${maxHeight} text-[11px] leading-relaxed select-text`}>
        {formatted}
      </pre>
    </div>
  );
};
