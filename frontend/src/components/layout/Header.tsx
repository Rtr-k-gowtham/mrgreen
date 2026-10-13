import React from 'react';
import { Settings, Plus } from 'lucide-react';

interface HeaderProps {
  isOnline: boolean;
  onNewChat?: () => void;
  onOpenHistory?: () => void;
  onOpenSettings: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  isOnline,
  onNewChat,
  onOpenSettings,
}) => {
  return (
    <header className="w-full bg-white border-b border-slate-100 px-4 sm:px-6 py-3 pt-safe-top transition-colors">
      <div className="flex items-center justify-between max-w-5xl mx-auto">
        {/* Left: Minimal Green MG Logo with Leaf Symbol */}
        <div className="flex items-center gap-2.5">
          <div className="relative w-8 h-8 rounded-xl bg-gradient-to-tr from-[#16A34A] to-[#22C55E] flex items-center justify-center text-white font-bold text-xs shadow-sm shadow-green-500/25">
            {/* Small Minimal Leaf Accent */}
            <svg
              className="absolute -top-1 -right-1 w-3.5 h-3.5 text-green-600"
              viewBox="0 0 24 24"
              fill="currentColor"
              aria-hidden="true"
            >
              <path d="M17 8C8 10 5.9 16.17 3.82 21.34L5.71 22l1-2.3A4.49 4.49 0 0 0 8 20C19 20 22 3 22 3c-1 2-8 2.52-13 4.29C8 7.6 8 8 8 8c4-1 9-1 9 0z" />
            </svg>
            <span className="font-mono tracking-tighter">MG</span>
          </div>

          <div className="flex flex-col">
            <span className="font-semibold text-sm sm:text-base text-slate-900 tracking-tight flex items-center gap-1.5">
              MR.GREEN
            </span>
          </div>
        </div>

        {/* Right: Connection Indicator & Settings */}
        <div className="flex items-center gap-2.5">
          {/* Connection Status Pill */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border transition-colors ${
              isOnline
                ? 'bg-green-50 text-green-700 border-green-200/80'
                : 'bg-slate-50 text-slate-500 border-slate-200'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isOnline ? 'bg-green-500 animate-pulse' : 'bg-slate-400'
              }`}
            />
            <span className="tracking-wide">{isOnline ? 'LIVE' : 'OFFLINE'}</span>
          </div>

          {/* New Chat Accessible Reset (Discreet) */}
          {onNewChat && (
            <button
              type="button"
              onClick={onNewChat}
              className="p-1.5 rounded-full text-slate-400 hover:text-green-600 hover:bg-green-50 transition-colors"
              aria-label="Start new chat"
              title="Reset conversation"
            >
              <Plus className="w-4 h-4" />
            </button>
          )}

          {/* Settings Icon */}
          <button
            type="button"
            onClick={onOpenSettings}
            className="p-1.5 rounded-full text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            aria-label="Open settings"
            title="Assistant settings"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
export default Header;
