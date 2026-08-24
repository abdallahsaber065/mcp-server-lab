import React, { useRef, useState } from 'react';
import { Send, StopCircle, Image as ImageIcon, X, Loader2, FileSearch, Wrench, Scale } from 'lucide-react';
import { UserRole } from '../../types';
import { ChatMode } from './ChatHeader';
import { apiClient } from '../../services/api';

interface ChatInputBarProps {
  inputValue: string;
  onChangeInput: (val: string) => void;
  onSubmit: (e: React.FormEvent, attachedImages?: string[]) => void;
  isStreaming: boolean;
  onStopStream: () => void;
  onSelectPrompt?: (prompt: string) => void;
  role?: UserRole;
  chatMode?: ChatMode;
}

export const ChatInputBar: React.FC<ChatInputBarProps> = ({
  inputValue,
  onChangeInput,
  onSubmit,
  isStreaming,
  onStopStream,
  onSelectPrompt,
  role = 'property_manager',
  chatMode = 'standard',
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [attachedImages, setAttachedImages] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const getStandardPrompts = () => {
    switch (role) {
      case 'tenant':
        return [
          'What are my active lease terms and monthly rent?',
          'Submit repair request for kitchen plumbing leak',
          'Check building quiet hours and guest rules',
          'Lookup available 2-bedroom units in Cairo',
        ];
      case 'executive_admin':
        return [
          'Run portfolio occupancy and revenue audit',
          'Review pending high-value lease concessions',
          'Simulate multi-unit eviction & escrow state graph',
          'Emergency structural facade repair escalation',
        ];
      case 'property_manager':
      default:
        return [
          'Audit compliance for Property #1',
          'Lookup available 2-bedroom units in Cairo',
          'Emergency plumbing burst at Nile Tower',
          'Modify lease terms for Unit 101 rent discount',
        ];
    }
  };

  const getGraphPrompts = (): { label: string; prompts: string[]; icon: any } => {
    // One natural, tenant-tied prompt per specialized graph — generic user voice, not technical slot language
    // Triggers real state graph (Vision/LATS/ToT) via intent + slot filling without exposing internals
    switch (chatMode) {
      case 'lease_onboarding':
        return {
          label: 'Commercial Lease — Quick Prompts',
          prompts: [
            "Hi, I'm Dr. Tarek El-Mahdy — I'd like to lease Suite-301 in Giza Medical Tower at 48,000 EGP/mo. What are the terms?",
            "Here is my Banque Misr transfer receipt of 144,000 EGP for the escrow deposit of Suite-301.",
          ],
          icon: FileSearch,
        };
      case 'maintenance_tender':
        return {
          label: 'Emergency Maintenance — Quick Prompts',
          prompts: [
            "Hi, I'm Dr. Tarek El-Mahdy in Suite 301 at Nile Heights Tower — there is an urgent structural pipe leak causing flooding. Please dispatch emergency repair.",
            "I rate the completed plumbing repair 5 stars. Excellent and clean job.",
          ],
          icon: Wrench,
        };
      case 'arrears_mediation':
        return {
          label: 'Arrears Restructuring — Quick Prompts',
          prompts: [
            "Hi, I'm Dr. Tarek El-Mahdy — I have 2 months of unpaid rent totaling 90,000 EGP. Can we explore a debt restructuring plan?",
            "I accept Plan A for the 6-month installment schedule of 15,000 EGP/mo.",
          ],
          icon: Scale,
        };
      default:
        return { label: 'Standard', prompts: getStandardPrompts(), icon: FileSearch };
    }
  };

  const isGraphMode = chatMode !== 'standard';
  const graphPrompts = isGraphMode ? getGraphPrompts() : null;
  const quickPrompts = isGraphMode ? graphPrompts!.prompts : getStandardPrompts();

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    try {
      const formData = new FormData();
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }

      const res = await fetch('/api/chat/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (data.image_urls) {
        setAttachedImages((prev) => [...prev, ...data.image_urls]);
      }
    } catch (err) {
      console.error('Failed to upload image attachments', err);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleRemoveImage = (index: number) => {
    setAttachedImages((prev) => prev.filter((_, i) => i !== index));
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if ((inputValue.trim() || attachedImages.length > 0) && !isStreaming && !isUploading) {
      onSubmit(e, attachedImages);
      setAttachedImages([]);
    }
  };

  const placeholder = isGraphMode
    ? `Graph agent ${chatMode.replace('_', ' ')} — describe your request or upload receipt...`
    : `Ask anything as ${role?.replace('_', ' ')} or attach receipts/photos...`;

  return (
    <div className="p-3 sm:p-4 border-t border-slate-800/80 bg-slate-900/70 backdrop-blur-md shrink-0 space-y-2.5">
      {/* Quick Prompt Chips — organized per mode */}
      {onSelectPrompt && (
        <div className="max-w-4xl mx-auto space-y-1.5">
          <div />
          <div className="flex items-center gap-1.5 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            {quickPrompts.map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => onSelectPrompt(q)}
                className={`px-2.5 py-1 rounded-lg border text-left truncate shrink-0 text-[11px] transition-all ${isGraphMode ? 'bg-violet-950/30 hover:bg-violet-900/40 text-violet-200 border-violet-500/30 hover:border-violet-400/50' : 'bg-slate-800/70 hover:bg-indigo-600/30 text-slate-300 hover:text-indigo-200 border-slate-700/60 hover:border-indigo-500/40'}`}
                title={q}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Attached Images Preview Row */}
      {attachedImages.length > 0 && (
        <div className="max-w-4xl mx-auto flex items-center gap-2 overflow-x-auto pb-1">
          {attachedImages.map((url, idx) => (
            <div key={idx} className="relative group shrink-0">
              <img
                src={url}
                alt={`Upload ${idx + 1}`}
                className="w-14 h-14 object-cover rounded-lg border border-slate-700 shadow-md"
              />
              <button
                type="button"
                onClick={() => handleRemoveImage(idx)}
                className="absolute -top-1 -right-1 p-0.5 rounded-full bg-rose-600 text-white hover:bg-rose-500 shadow transition-all"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleFormSubmit} className="max-w-4xl mx-auto flex items-end space-x-2.5">
        {/* Hidden Multi-file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileChange}
          className="hidden"
        />

        {/* Attachment Button */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isStreaming || isUploading}
          className="p-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/80 transition-all shrink-0 disabled:opacity-50"
          title="Attach receipt or defect photos (Multiple supported)"
        >
          {isUploading ? (
            <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
          ) : (
            <ImageIcon className="w-4 h-4" />
          )}
        </button>

        <textarea
          rows={Math.min(4, Math.max(1, inputValue.split('\n').length))}
          value={inputValue}
          onChange={(e) => onChangeInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              if ((inputValue.trim() || attachedImages.length > 0) && !isStreaming && !isUploading) {
                handleFormSubmit(e);
              }
            }
          }}
          placeholder={placeholder}
          disabled={isStreaming}
          className="flex-1 px-4 py-2.5 rounded-xl bg-slate-950/90 border border-slate-700/80 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 transition-all resize-none leading-relaxed"
        />

        {isStreaming ? (
          <button
            type="button"
            onClick={onStopStream}
            className="px-4 py-3 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold flex items-center space-x-2 shadow-lg shadow-rose-600/30 transition-all shrink-0"
            title="Interrupt Generation"
          >
            <StopCircle className="w-4 h-4 animate-pulse" />
            <span>Stop</span>
          </button>
        ) : (
          <button
            type="submit"
            disabled={(!inputValue.trim() && attachedImages.length === 0) || isUploading}
            className="px-5 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white text-xs font-bold flex items-center space-x-2 shadow-lg shadow-indigo-600/30 border border-indigo-500/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">Send</span>
          </button>
        )}
      </form>
    </div>
  );
};
