import React, { useState } from 'react';
import { ChatMessage as ChatMessageType } from '../../types/chat';
import { Bot, User, Volume2, ChevronDown, ChevronUp, Cpu, CheckCircle2, Clock } from 'lucide-react';

interface ChatMessageProps {
  message: ChatMessageType;
  onSpeak?: (text: string) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, onSpeak }) => {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  const [showTools, setShowTools] = useState<boolean>(false);

  // Format simple markdown: code blocks, inline code, bold, line breaks
  const renderFormattedContent = (content: string) => {
    // Check for code blocks
    const parts = content.split(/(```[\s\S]*?```)/g);

    return parts.map((part, index) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        const lines = part.slice(3, -3).trim().split('\n');
        const language = lines[0].match(/^[a-zA-Z0-9_-]+$/) ? lines[0] : '';
        const code = language ? lines.slice(1).join('\n') : lines.join('\n');

        return (
          <div key={index} className="my-2 rounded-lg bg-zinc-950/80 border border-zinc-800 p-2.5 font-mono text-xs overflow-x-auto text-emerald-300">
            {language && <div className="text-[10px] text-zinc-500 mb-1 uppercase font-semibold">{language}</div>}
            <pre><code>{code}</code></pre>
          </div>
        );
      }

      // Format bold and inline code in regular text paragraphs
      return (
        <span key={index} className="whitespace-pre-wrap leading-relaxed">
          {part.split(/(`[^`]+`|\*\*[^*]+\*\*)/g).map((subPart, subIdx) => {
            if (subPart.startsWith('`') && subPart.endsWith('`')) {
              return (
                <code key={subIdx} className="bg-zinc-800/80 text-emerald-300 px-1 py-0.5 rounded text-xs font-mono">
                  {subPart.slice(1, -1)}
                </code>
              );
            }
            if (subPart.startsWith('**') && subPart.endsWith('**')) {
              return (
                <strong key={subIdx} className="font-semibold text-white">
                  {subPart.slice(2, -2)}
                </strong>
              );
            }
            return subPart;
          })}
        </span>
      );
    });
  };

  if (isSystem) {
    return (
      <div className="flex justify-center my-2 px-4">
        <div className="bg-rose-950/40 border border-rose-800/40 text-rose-300 text-xs px-3 py-1.5 rounded-full max-w-md text-center">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex w-full my-2.5 px-3 sm:px-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`flex gap-2.5 max-w-[88%] sm:max-w-[80%] ${
          isUser ? 'flex-row-reverse' : 'flex-row'
        }`}
      >
        {/* Avatar */}
        <div
          className={`w-7 h-7 sm:w-8 sm:h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold ${
            isUser
              ? 'bg-emerald-600/30 text-emerald-300 border border-emerald-500/40'
              : 'bg-zinc-800 text-emerald-400 border border-zinc-700'
          }`}
        >
          {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
        </div>

        {/* Message Bubble Container */}
        <div className="flex flex-col">
          {/* Header with Name & Timestamp */}
          <div
            className={`flex items-center gap-2 mb-1 text-[11px] text-zinc-400 ${
              isUser ? 'justify-end' : 'justify-start'
            }`}
          >
            <span className="font-medium text-zinc-300">
              {isUser ? 'YOU' : 'MR.GREEN'}
            </span>
            <span>•</span>
            <span className="text-[10px]">{message.timestamp}</span>
            {!isUser && onSpeak && (
              <button
                type="button"
                onClick={() => onSpeak(message.content)}
                title="Speak message aloud"
                className="text-zinc-500 hover:text-emerald-400 p-0.5 rounded transition-colors"
                aria-label="Speak message"
              >
                <Volume2 className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Bubble Body */}
          <div
            className={`rounded-2xl px-4 py-3 text-sm text-zinc-100 shadow-md ${
              isUser
                ? 'bg-gradient-to-br from-emerald-950/70 to-zinc-900 border border-emerald-500/30 rounded-tr-none'
                : 'bg-zinc-900/90 border border-zinc-800 rounded-tl-none'
            }`}
          >
            {renderFormattedContent(message.content)}

            {/* Subtle Tool Activity Accordion (if tools were used) */}
            {message.toolActivities && message.toolActivities.length > 0 && (
              <div className="mt-2.5 pt-2 border-t border-zinc-800">
                <button
                  type="button"
                  onClick={() => setShowTools(!showTools)}
                  className="flex items-center gap-1.5 text-[11px] font-mono text-emerald-400/90 hover:text-emerald-300 transition-colors"
                >
                  <Cpu className="w-3.5 h-3.5 text-emerald-400" />
                  <span>
                    Used {message.toolActivities.length}{' '}
                    {message.toolActivities.length === 1 ? 'tool' : 'tools'}
                  </span>
                  {showTools ? (
                    <ChevronUp className="w-3 h-3 ml-0.5" />
                  ) : (
                    <ChevronDown className="w-3 h-3 ml-0.5" />
                  )}
                </button>

                {showTools && (
                  <div className="mt-2 space-y-1.5 pl-2 border-l border-emerald-500/20 text-xs">
                    {message.toolActivities.map((tool) => (
                      <div
                        key={tool.id}
                        className="flex items-center justify-between text-zinc-400 bg-zinc-950/50 px-2 py-1 rounded"
                      >
                        <span className="flex items-center gap-1 font-mono text-[11px] text-zinc-300">
                          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                          {tool.toolName}
                        </span>
                        {tool.durationMs !== undefined && (
                          <span className="text-[10px] text-zinc-500 font-mono flex items-center gap-0.5">
                            <Clock className="w-2.5 h-2.5" />
                            {tool.durationMs}ms
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
