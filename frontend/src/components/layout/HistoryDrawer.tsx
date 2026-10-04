import React, { useEffect, useState } from 'react';
import { X, MessageSquare, Plus, Clock, ChevronRight } from 'lucide-react';
import { ConversationSummary } from '../../types/agent';
import { api } from '../../services/api';

interface HistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
}

export const HistoryDrawer: React.FC<HistoryDrawerProps> = ({
  isOpen,
  onClose,
  activeConversationId,
  onSelectConversation,
  onNewChat,
}) => {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    if (isOpen) {
      loadConversations();
    }
  }, [isOpen]);

  const loadConversations = async () => {
    setIsLoading(true);
    try {
      const data = await api.getConversations(50);
      setConversations(data);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  // Group conversations into Today, Yesterday, and Older
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const yesterday = today - 86400000;

  const grouped = {
    today: [] as ConversationSummary[],
    yesterday: [] as ConversationSummary[],
    older: [] as ConversationSummary[],
  };

  conversations.forEach((conv) => {
    const time = new Date(conv.updated_at || conv.created_at).getTime();
    if (time >= today) {
      grouped.today.push(conv);
    } else if (time >= yesterday) {
      grouped.yesterday.push(conv);
    } else {
      grouped.older.push(conv);
    }
  });

  const renderGroup = (title: string, list: ConversationSummary[]) => {
    if (list.length === 0) return null;

    return (
      <div className="mb-4">
        <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 px-3 py-1 font-semibold">
          {title}
        </div>
        <div className="space-y-1">
          {list.map((conv) => {
            const isSelected = activeConversationId === conv.id;
            return (
              <button
                key={conv.id}
                type="button"
                onClick={() => {
                  onSelectConversation(conv.id);
                  onClose();
                }}
                className={`w-full text-left px-3 py-2.5 rounded-xl transition-all flex items-center justify-between group ${
                  isSelected
                    ? 'bg-emerald-950/70 border border-emerald-500/40 text-emerald-200'
                    : 'hover:bg-zinc-800/60 text-zinc-350 hover:text-white border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0 pr-2">
                  <MessageSquare
                    className={`w-4 h-4 flex-shrink-0 ${
                      isSelected ? 'text-emerald-400' : 'text-zinc-500 group-hover:text-zinc-300'
                    }`}
                  />
                  <div className="min-w-0">
                    <div className="text-xs font-medium truncate">
                      {conv.title || 'Conversation with MR.GREEN'}
                    </div>
                    <div className="text-[10px] text-zinc-500 flex items-center gap-1 mt-0.5">
                      <span>{conv.message_count} messages</span>
                    </div>
                  </div>
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-zinc-600 group-hover:text-zinc-400 flex-shrink-0" />
              </button>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex animate-fade-in">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Drawer content */}
      <div className="relative w-80 max-w-[85vw] h-full bg-zinc-950 border-r border-zinc-800 flex flex-col z-10 shadow-2xl pt-safe-top pb-safe-bottom">
        {/* Drawer Header */}
        <div className="flex items-center justify-between p-4 border-b border-zinc-800">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-semibold text-white">Conversations</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-900"
            aria-label="Close conversation history"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Action Button: New Chat */}
        <div className="p-3 border-b border-zinc-850">
          <button
            type="button"
            onClick={() => {
              onNewChat();
              onClose();
            }}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>+ New Chat</span>
          </button>
        </div>

        {/* List of Conversations */}
        <div className="flex-1 overflow-y-auto p-3">
          {isLoading ? (
            <div className="flex items-center justify-center py-8 text-xs text-zinc-500 font-mono">
              Loading conversations...
            </div>
          ) : conversations.length === 0 ? (
            <div className="text-center py-8 px-4 text-xs text-zinc-500">
              No conversations yet. Start a new chat with MR.GREEN!
            </div>
          ) : (
            <>
              {renderGroup('Today', grouped.today)}
              {renderGroup('Yesterday', grouped.yesterday)}
              {renderGroup('Older', grouped.older)}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
