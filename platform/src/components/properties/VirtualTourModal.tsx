import React from 'react';
import { X, Maximize2, Sparkles, ExternalLink } from 'lucide-react';

interface VirtualTourModalProps {
  isOpen: boolean;
  onClose: () => void;
  tourUrl?: string;
  propertyTitle?: string;
}

export const VirtualTourModal: React.FC<VirtualTourModalProps> = ({
  isOpen,
  onClose,
  tourUrl,
  propertyTitle
}) => {
  if (!isOpen || !tourUrl) return null;

  // Convert discover or standard matterport link to embed link if needed
  let embedUrl = tourUrl;
  if (tourUrl.includes('discover.matterport.com/space/')) {
    const spaceId = tourUrl.split('/space/')[1]?.split('?')[0];
    embedUrl = `https://my.matterport.com/show/?m=${spaceId}&play=1&qs=1&title=0`;
  } else if (tourUrl.includes('my.matterport.com/show/?m=')) {
    embedUrl = tourUrl.includes('&play=1') ? tourUrl : `${tourUrl}&play=1&qs=1&title=0`;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-6 bg-slate-950/90 backdrop-blur-xl animate-in fade-in duration-200">
      <div className="glass-card w-full max-w-6xl h-[88vh] rounded-3xl border-slate-700 shadow-2xl flex flex-col overflow-hidden relative">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-[10px] font-extrabold px-2 py-0.5 rounded bg-indigo-600/80 text-white uppercase tracking-wider">
                  Interactive Matterport 3D Tour
                </span>
                <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                  Live Digital Twin
                </span>
              </div>
              <h3 className="text-base font-bold text-white mt-0.5 truncate max-w-md">
                {propertyTitle || 'Luxury Property 3D Walkthrough'}
              </h3>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <a
              href={tourUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
              title="Open full screen in new tab"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
            <button
              onClick={onClose}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* 3D Iframe Viewer */}
        <div className="flex-1 w-full h-full bg-black relative">
          <iframe
            src={embedUrl}
            title={propertyTitle || 'Matterport 3D Tour'}
            className="w-full h-full border-0"
            allowFullScreen
            allow="xr-spatial-tracking; gyroscope; accelerometer"
          />
        </div>
      </div>
    </div>
  );
};
