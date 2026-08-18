import React from 'react';
import { MessageSquare, Cpu, Database } from 'lucide-react';

interface ChatHeaderProps {
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
  selectedModel: string;
  onChangeModel: (model: string) => void;
  selectedRag: string;
  onChangeRag: (rag: any) => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  isSidebarOpen,
  onToggleSidebar,
  selectedModel,
  onChangeModel,
  selectedRag,
  onChangeRag,
}) => {
  return (
    <div className="h-14 border-b border-slate-800/80 px-4 flex items-center justify-between bg-slate-900/70 backdrop-blur-md shrink-0 select-none">
      <div className="flex items-center space-x-3">
        <button
          onClick={onToggleSidebar}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors"
          title="Toggle Sessions Sidebar"
        >
          <MessageSquare className="w-4 h-4" />
        </button>

        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-bold text-slate-200">Cornerstone Autonomous Agent Studio</span>
        </div>
      </div>

      {/* Model & RAG Selectors */}
      <div className="flex items-center space-x-2.5">
        {/* Model Selector */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-300">
          <Cpu className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
          <select
            value={selectedModel}
            onChange={(e) => onChangeModel(e.target.value)}
            className="bg-transparent text-xs text-slate-200 focus:outline-none cursor-pointer"
          >
            <option value="gemini/gemini-3.1-flash-lite" className="bg-slate-900">Gemini 3.1 Flash-Lite (Default)</option>
            <option value="gemini/gemini-3.5-flash" className="bg-slate-900">Gemini 3.5 Flash</option>
            <option value="gemini/gemini-2.5-flash" className="bg-slate-900">Gemini 2.5 Flash</option>
            <option value="gemini/gemini-2.5-flash-lite" className="bg-slate-900">Gemini 2.5 Flash-Lite</option>
            <option value="gemini/gemma-4-26b-a4b-it" className="bg-slate-900">Gemma 4 26B A4B IT</option>
            <option value="mistral/mistral-small-latest" className="bg-slate-900">Mistral Small Latest</option>
            <option value="mistral/open-mistral-7b" className="bg-slate-900">Open Mistral 7B</option>
            <option value="mistral/open-mixtral-8x7b" className="bg-slate-900">Open Mixtral 8x7B</option>
            <option value="mistral/codestral-latest" className="bg-slate-900">CodeStral Latest</option>
            <option value="mistral/mistral-large-latest" className="bg-slate-900">Mistral Large Latest</option>
          </select>
        </div>

        {/* RAG Selector */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-300">
          <Database className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
          <select
            value={selectedRag}
            onChange={(e) => onChangeRag(e.target.value)}
            className="bg-transparent text-xs text-slate-200 focus:outline-none cursor-pointer"
          >
            <option value="agentic" className="bg-slate-900">Agentic (Multi-Hop)</option>
            <option value="hybrid" className="bg-slate-900">Hybrid (BM25+RRF)</option>
            <option value="naive" className="bg-slate-900">Naive RAG</option>
            <option value="graph" className="bg-slate-900">Graph (Entities)</option>
          </select>
        </div>
      </div>
    </div>
  );
};
