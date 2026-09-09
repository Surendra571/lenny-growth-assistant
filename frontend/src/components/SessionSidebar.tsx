import React from 'react';
import { Session } from '../types';
import { MessageSquare, Plus, Trash2, Sparkles } from 'lucide-react';

interface SessionSidebarProps {
  sessions: Session[];
  currentSession: Session | null;
  onSelectSession: (session: Session) => void;
  onNewSession: () => void;
  onDeleteSession: (sessionId: string) => void;
  isLoading?: boolean;
}

export const SessionSidebar: React.FC<SessionSidebarProps> = ({
  sessions,
  currentSession,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  isLoading = false,
}) => {
  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/40 p-4 flex flex-col justify-between h-full shrink-0">
      <div className="flex flex-col flex-1 min-h-0">
        <button
          onClick={onNewSession}
          className="w-full py-2.5 px-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition flex items-center justify-center space-x-2 shadow-lg shadow-indigo-600/20"
        >
          <Plus className="w-4 h-4" />
          <span>New Conversation</span>
        </button>

        <div className="mt-5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
          <span>Conversations</span>
          <span className="text-[10px] text-slate-500">{sessions.length}</span>
        </div>

        <div className="mt-2.5 space-y-1 overflow-y-auto flex-1 pr-1">
          {isLoading ? (
            <div className="space-y-2 py-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-8 rounded-lg bg-slate-800/50 animate-pulse" />
              ))}
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-xs text-slate-500 italic p-3 text-center">
              No conversations yet. Start a new one above!
            </div>
          ) : (
            sessions.map((s) => {
              const isActive = currentSession?.id === s.id;
              return (
                <div
                  key={s.id}
                  className={`group relative flex items-center justify-between rounded-lg px-2.5 py-2 text-xs transition cursor-pointer ${isActive
                      ? 'bg-indigo-950/70 border border-indigo-800 text-indigo-200 shadow-sm'
                      : 'text-slate-400 hover:bg-slate-850 hover:text-slate-200 border border-transparent'
                    }`}
                  onClick={() => onSelectSession(s)}
                >
                  <div className="flex items-center space-x-2 truncate min-w-0 pr-2">
                    <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-indigo-400' : 'text-slate-500'}`} />
                    <span className="truncate">{s.title || 'Untitled Conversation'}</span>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteSession(s.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-slate-800 transition"
                    title="Delete conversation"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>

      <div className="text-[11px] text-slate-500 border-t border-slate-800/80 pt-3 flex items-center justify-between mt-2">
        <span className="flex items-center space-x-1.5">
          <Sparkles className="w-3 h-3 text-indigo-400" />
          <span>Lenny Growth AI</span>
        </span>
        <span className="text-[10px] text-slate-500 font-mono">v1.0.0</span>
      </div>
    </aside>
  );
};
