import { Plus, Menu, Sliders } from 'lucide-react';

interface HeaderProps {
  isOnline: boolean;
  onNewChat: () => void;
  onOpenHistory: () => void;
  onOpenSettings: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  isOnline,
  onNewChat,
  onOpenHistory,
  onOpenSettings,
}) => {
  return (
    <header className="sticky top-0 z-30 w-full bg-zinc-950/80 backdrop-blur-md border-b border-zinc-800/80 px-4 py-3 pt-safe-top">
      <div className="flex items-center justify-between max-w-5xl mx-auto">
        {/* Left: History drawer toggle & Brand */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onOpenHistory}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-900 border border-transparent hover:border-zinc-800 transition-colors"
            aria-label="Open conversation history"
            title="Conversation history"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2">
            {/* Glowing Logo Icon */}
            <div className="w-7 h-7 rounded-lg bg-emerald-950 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-black text-xs font-mono shadow-sm shadow-emerald-500/30">
              MG
            </div>
            <div>
              <span className="font-bold text-sm sm:text-base tracking-wider text-white font-mono flex items-center gap-1.5">
                MR.GREEN
              </span>
            </div>
          </div>
        </div>

        {/* Right: Status Pill, Settings & + New Chat */}
        <div className="flex items-center gap-2">
          {/* Connection Status Pill */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono font-medium border ${
              isOnline
                ? 'bg-emerald-950/70 text-emerald-300 border-emerald-500/30'
                : 'bg-zinc-900 text-zinc-400 border-zinc-700'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isOnline ? 'bg-emerald-400 animate-pulse' : 'bg-zinc-500'
              }`}
            />
            <span>{isOnline ? 'LIVE' : 'OFFLINE'}</span>
          </div>

          {/* Voice Settings */}
          <button
            type="button"
            onClick={onOpenSettings}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-900 border border-transparent hover:border-zinc-800 transition-colors"
            aria-label="Open voice settings"
            title="Voice settings"
          >
            <Sliders className="w-4 h-4" />
          </button>

          {/* New Chat Button */}
          <button
            type="button"
            onClick={onNewChat}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-zinc-900 hover:bg-emerald-950 text-zinc-200 hover:text-emerald-300 border border-zinc-800 hover:border-emerald-500/40 text-xs font-medium transition-all"
            aria-label="Start new chat"
          >
            <Plus className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">New Chat</span>
          </button>
        </div>
      </div>
    </header>
  );
};
