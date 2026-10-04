import React, { useEffect, useRef } from 'react';
import { ChatMessage as ChatMessageType } from '../../types/chat';
import { ChatMessage } from './ChatMessage';
import { Sparkles, Terminal, Calculator, Clock } from 'lucide-react';

interface ChatListProps {
  messages: ChatMessageType[];
  isProcessing: boolean;
  onSelectPrompt?: (text: string) => void;
  onSpeak?: (text: string) => void;
}

export const ChatList: React.FC<ChatListProps> = ({
  messages,
  isProcessing,
  onSelectPrompt,
  onSpeak,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom when new messages arrive or when processing state changes
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  const samplePrompts = [
    { text: 'What is 250 × 40?', icon: Calculator, label: 'Calculator' },
    { text: 'What time is it now in UTC?', icon: Clock, label: 'Time Tool' },
    { text: 'What can you do MR.GREEN?', icon: Sparkles, label: 'Capabilities' },
    { text: 'List files in your directory', icon: Terminal, label: 'Sandbox' },
  ];

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-4 text-center select-none">
        <p className="text-sm text-zinc-400 mb-4 max-w-xs font-light">
          Ask MR.GREEN questions, give voice instructions, or try these actions:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full max-w-md">
          {samplePrompts.map((item, index) => {
            const Icon = item.icon;
            return (
              <button
                key={index}
                type="button"
                onClick={() => onSelectPrompt?.(item.text)}
                className="flex items-center gap-2.5 p-3 rounded-xl bg-zinc-900/60 border border-zinc-800/80 hover:border-emerald-500/40 hover:bg-zinc-850 transition-all text-left group"
              >
                <div className="p-2 rounded-lg bg-emerald-950/60 text-emerald-400 group-hover:scale-110 transition-transform">
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[10px] text-zinc-500 uppercase font-mono tracking-wider">
                    {item.label}
                  </div>
                  <div className="text-xs text-zinc-200 truncate group-hover:text-emerald-300">
                    "{item.text}"
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-1 sm:px-2 py-2 space-y-1 scroll-smooth">
      {messages.map((message) => (
        <ChatMessage key={message.id} message={message} onSpeak={onSpeak} />
      ))}

      {/* Thinking Indicator */}
      {isProcessing && (
        <div className="flex justify-start px-3 sm:px-4 my-2">
          <div className="flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-zinc-900 border border-zinc-800 text-xs text-emerald-400 font-mono animate-pulse">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span>MR.GREEN is thinking...</span>
          </div>
        </div>
      )}

      <div ref={bottomRef} className="h-2" />
    </div>
  );
};
