import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, RefreshCw } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string, skillOverride?: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading,
  disabled = false,
}) => {
  const [text, setText] = useState('');
  const [ship30Mode, setShip30Mode] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [text]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || isLoading || disabled) return;

    onSendMessage(trimmed, ship30Mode ? 'ship30' : undefined);
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto pt-2 pb-4 px-4">
      {/* Skill mode selector */}
      <div className="flex items-center space-x-2 mb-2">
        <button
          type="button"
          onClick={() => setShip30Mode(!ship30Mode)}
          className={`px-2.5 py-1 rounded-full text-[11px] font-medium transition flex items-center space-x-1.5 border ${ship30Mode
              ? 'bg-indigo-600/30 border-indigo-500 text-indigo-200'
              : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
        >
          <Sparkles className={`w-3 h-3 ${ship30Mode ? 'text-indigo-400' : 'text-slate-500'}`} />
          <span>{ship30Mode ? '✦ Ship 30 Mode: Active' : 'Enable Ship 30 Mode'}</span>
        </button>
      </div>

      {/* Input container */}
      <form onSubmit={handleSubmit} className="flex items-end rounded-xl border border-slate-800 bg-slate-900/90 p-2 focus-within:border-indigo-500 transition shadow-lg shadow-black/20">
        <textarea
          ref={textareaRef}
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || isLoading}
          placeholder={
            ship30Mode
              ? 'Enter a product topic for a 1,250-word Ship 30 for 30 essay...'
              : "Ask Lenny about PMF, PLG, founder mode, or type 'Turn that into a Ship 30'..."
          }
          className="flex-1 max-h-28 bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none resize-none px-2 py-1.5 leading-relaxed"
        />

        <button
          type="submit"
          disabled={!text.trim() || isLoading || disabled}
          className="px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:hover:bg-indigo-600 text-white text-xs font-medium transition flex items-center justify-center shrink-0 ml-2 shadow-md shadow-indigo-600/20"
          title="Send message (Enter)"
        >
          {isLoading ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Send className="w-3.5 h-3.5" />
          )}
        </button>
      </form>
      <div className="flex items-center justify-between text-[10px] text-slate-500 mt-1.5 px-1">
        <span>Enter to send · Shift+Enter for newline</span>
        <span>Grounded on 10 podcast transcript episodes</span>
      </div>
    </div>
  );
};

