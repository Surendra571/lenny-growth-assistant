import React, { useState } from 'react';
import { Message, SourceCitation } from '../types';
import { Bot, User, BookOpen, ChevronDown, ChevronUp, Sparkles, ExternalLink, ShieldAlert } from 'lucide-react';

interface ChatMessageProps {
  message: Message;
  onOpenArtifact?: (artifactId: string) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, onOpenArtifact }) => {
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const isAssistant = message.role === 'assistant';
  const isShip30 = message.metadata?.intent === 'ship30' || message.metadata?.skill === 'ship30';
  const artifactId = message.metadata?.artifact_id;
  const sources: SourceCitation[] = message.sources || message.metadata?.sources || [];
  const isRefusal = message.content.includes("I couldn't find enough support") ||
    message.content.includes("Topic Not Covered in Lenny's Podcast") ||
    message.content.includes("NO RELEVANT TRANSCRIPT EVIDENCE FOUND");

  // Simple, safe Markdown-to-JSX parser
  const renderMarkdown = (text: string) => {
    const blocks = text.split(/\n\n+/);
    return blocks.map((block, idx) => {
      const trimmed = block.trim();
      if (!trimmed) return null;

      if (trimmed.startsWith('# ')) {
        return (
          <h1 key={idx} className="text-lg font-bold text-white mt-4 mb-2 pb-1 border-b border-slate-800">
            {trimmed.replace(/^#\s+/, '')}
          </h1>
        );
      }
      if (trimmed.startsWith('## ')) {
        return (
          <h2 key={idx} className="text-base font-semibold text-indigo-300 mt-4 mb-2">
            {trimmed.replace(/^##\s+/, '')}
          </h2>
        );
      }
      if (trimmed.startsWith('### ')) {
        return (
          <h3 key={idx} className="text-sm font-semibold text-slate-200 mt-3 mb-1">
            {trimmed.replace(/^###\s+/, '')}
          </h3>
        );
      }
      if (trimmed.startsWith('---')) {
        return <hr key={idx} className="border-slate-800 my-4" />;
      }
      if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
        const items = trimmed.split('\n').filter((l) => l.trim().startsWith('* ') || l.trim().startsWith('- '));
        return (
          <ul key={idx} className="list-disc pl-5 my-2 space-y-1 text-xs text-slate-300">
            {items.map((it, i) => (
              <li key={i} dangerouslySetInnerHTML={{ __html: formatInline(it.replace(/^[\*\-]\s+/, '')) }} />
            ))}
          </ul>
        );
      }
      if (/^\d+\.\s+/.test(trimmed)) {
        const items = trimmed.split('\n').filter((l) => /^\d+\.\s+/.test(l.trim()));
        return (
          <ol key={idx} className="list-decimal pl-5 my-2 space-y-1 text-xs text-slate-300">
            {items.map((it, i) => (
              <li key={i} dangerouslySetInnerHTML={{ __html: formatInline(it.replace(/^\d+\.\s+/, '')) }} />
            ))}
          </ol>
        );
      }

      return (
        <p
          key={idx}
          className="text-xs leading-relaxed text-slate-300 my-2"
          dangerouslySetInnerHTML={{ __html: formatInline(trimmed) }}
        />
      );
    });
  };

  const formatInline = (str: string): string => {
    // Escape standard HTML first to prevent injection
    let safe = str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Bold
    safe = safe.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>');
    // Italic
    safe = safe.replace(/\*(.*?)\*/g, '<em class="text-slate-200">$1</em>');
    // Inline code
    safe = safe.replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono text-[11px]">$1</code>');
    return safe;
  };

  return (
    <div className={`flex w-full ${isAssistant ? 'justify-start' : 'justify-end'} my-3`}>
      <div
        className={`flex max-w-2xl rounded-xl p-4 transition-all shadow-sm ${isAssistant
            ? isRefusal
              ? 'bg-amber-950/20 border border-amber-800/40 text-slate-200'
              : 'bg-slate-900/80 border border-slate-800 text-slate-200'
            : 'bg-indigo-600 text-white shadow-indigo-600/10'
          }`}
      >
        {/* Avatar */}
        <div className="mr-3 shrink-0">
          {isAssistant ? (
            <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs ${isRefusal ? 'bg-amber-900/40 text-amber-300 border border-amber-700/40' : 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
              }`}>
              {isRefusal ? <ShieldAlert className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>
          ) : (
            <div className="w-7 h-7 rounded-lg bg-indigo-500/30 flex items-center justify-center text-white text-xs">
              <User className="w-4 h-4" />
            </div>
          )}
        </div>

        {/* Message Content */}
        <div className="flex-1 min-w-0 space-y-2">
          {/* Header metadata */}
          <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
            <span className="font-semibold text-slate-200">
              {isAssistant ? (isRefusal ? 'Knowledge Boundary Refusal' : isShip30 ? 'Ship 30 for 30 Essay' : 'Lenny Growth Assistant') : 'You'}
            </span>
            {isAssistant && message.metadata?.model && (
              <span className="text-[10px] text-slate-500 font-mono">{message.metadata.model}</span>
            )}
          </div>

          {/* Ship 30 Header Badge */}
          {isShip30 && (
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-indigo-950/60 border border-indigo-800/50 my-2">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <div>
                  <div className="text-xs font-semibold text-indigo-200">
                    {message.metadata?.title || 'Ship 30 for 30 Editorial Essay'}
                  </div>
                  {message.metadata?.word_count && (
                    <div className="text-[10px] text-indigo-400">
                      ~{message.metadata.word_count} words · Skimmable 3-Pillar Framework
                    </div>
                  )}
                </div>
              </div>
              {artifactId && onOpenArtifact && (
                <button
                  onClick={() => onOpenArtifact(artifactId)}
                  className="px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white text-[11px] font-medium transition flex items-center space-x-1 shrink-0"
                >
                  <ExternalLink className="w-3 h-3" />
                  <span>Open Artifact</span>
                </button>
              )}
            </div>
          )}

          {/* Body */}
          <div className="text-xs space-y-1">
            {isAssistant ? renderMarkdown(message.content) : <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>}
          </div>

          {/* Grounded Sources Drawer */}
          {isAssistant && sources.length > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-800/80">
              <button
                onClick={() => setSourcesOpen(!sourcesOpen)}
                className="flex items-center justify-between w-full text-[11px] font-medium text-indigo-400 hover:text-indigo-300 transition py-1"
              >
                <div className="flex items-center space-x-1.5">
                  <BookOpen className="w-3.5 h-3.5" />
                  <span>Verified Podcast Sources ({sources.length})</span>
                </div>
                {sourcesOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>

              {sourcesOpen && (
                <div className="mt-2 space-y-2">
                  {sources.map((src, i) => (
                    <div key={i} className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] space-y-1">
                      <div className="flex items-center justify-between text-slate-300 font-semibold">
                        <span>{src.guest_name ? `${src.guest_name} — ` : ''}{src.episode_title}</span>
                        {src.relevance_score && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-emerald-400 font-mono">
                            {Math.round(src.relevance_score * 100)}% match
                          </span>
                        )}
                      </div>
                      {src.timestamp && (
                        <div className="text-[10px] text-slate-400">Timestamp: {src.timestamp}</div>
                      )}
                      <p className="text-slate-400 italic text-[11px] border-l-2 border-indigo-500/40 pl-2 mt-1">
                        &quot;{src.snippet}&quot;
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

