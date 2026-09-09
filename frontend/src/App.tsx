import { useState, useEffect, useRef } from 'react';
import {
  checkHealth,
  listSessions,
  createSession,
  deleteSession,
  listMessages,
  sendMessage,
  listSessionArtifacts,
  deleteArtifact,
} from './services/api';
import { Artifact, Message, Session, SystemHealth } from './types';
import { SessionSidebar } from './components/SessionSidebar';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { EmptyChatState } from './components/EmptyChatState';
import { ArtifactViewer } from './components/ArtifactViewer';
import {
  PanelRightClose,
  PanelRightOpen,
  RefreshCw,
  ShieldAlert,
  Menu,
  X,
} from 'lucide-react';

export function App() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [activeArtifact, setActiveArtifact] = useState<Artifact | null>(null);

  const [isSessionsLoading, setIsSessionsLoading] = useState<boolean>(false);
  const [isMessagesLoading, setIsMessagesLoading] = useState<boolean>(false);
  const [isSending, setIsSending] = useState<boolean>(false);
  const [isArtifactLoading, setIsArtifactLoading] = useState<boolean>(false);

  const [error, setError] = useState<string | null>(null);
  const [isArtifactPanelOpen, setIsArtifactPanelOpen] = useState<boolean>(true);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending]);

  // Initial load: fetch health and sessions
  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch((err) => {
        console.warn('Health check warning:', err);
      });

    loadSessions();
  }, []);

  const loadSessions = async () => {
    setIsSessionsLoading(true);
    try {
      const sessList = await listSessions();
      setSessions(sessList);
      if (sessList.length > 0 && !currentSession) {
        setCurrentSession(sessList[0]);
      }
    } catch (err: any) {
      console.error('Failed to load sessions:', err);
      setError(err.message || 'Failed to load conversations.');
    } finally {
      setIsSessionsLoading(false);
    }
  };

  // Load conversation messages and artifacts whenever currentSession changes
  useEffect(() => {
    if (!currentSession) {
      setMessages([]);
      setArtifacts([]);
      setActiveArtifact(null);
      return;
    }

    setIsMessagesLoading(true);
    setError(null);

    Promise.all([
      listMessages(currentSession.id),
      listSessionArtifacts(currentSession.id),
    ])
      .then(([msgs, arts]) => {
        setMessages(msgs);
        setArtifacts(arts);
        setActiveArtifact(arts.length > 0 ? arts[0] : null);
      })
      .catch((err) => {
        console.error('Failed to load session content:', err);
        setError(err.message || 'Failed to load session messages and artifacts.');
      })
      .finally(() => {
        setIsMessagesLoading(false);
      });
  }, [currentSession?.id]);

  const handleNewSession = async () => {
    try {
      setError(null);
      const newSess = await createSession('New Growth Conversation');
      setSessions((prev) => [newSess, ...prev]);
      setCurrentSession(newSess);
      setMessages([]);
      setArtifacts([]);
      setActiveArtifact(null);
      setIsMobileSidebarOpen(false);
    } catch (err: any) {
      console.error('Failed to create new session:', err);
      setError(err.message || 'Failed to create new conversation.');
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await deleteSession(sessionId);
      const remaining = sessions.filter((s) => s.id !== sessionId);
      setSessions(remaining);
      if (currentSession?.id === sessionId) {
        setCurrentSession(remaining.length > 0 ? remaining[0] : null);
      }
    } catch (err: any) {
      console.error('Failed to delete session:', err);
      setError(err.message || 'Failed to delete conversation.');
    }
  };

  const handleSendMessage = async (text: string, skillOverride?: string) => {
    if (!text.trim() || isSending) return;

    let targetSession = currentSession;
    if (!targetSession) {
      try {
        targetSession = await createSession(text.slice(0, 30));
        setSessions([targetSession]);
        setCurrentSession(targetSession);
      } catch (err: any) {
        setError(err.message || 'Failed to initialize conversation session.');
        return;
      }
    }

    // Optimistic user message append
    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      session_id: targetSession.id,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMessage]);
    setIsSending(true);
    setError(null);

    try {
      const response = await sendMessage(targetSession.id, text, skillOverride);

      // Replace optimistic message and append assistant response
      setMessages((prev) => {
        const withoutTemp = prev.filter((m) => m.id !== tempUserMessage.id);
        return [...withoutTemp, response.user_message, response.assistant_message];
      });

      // Refresh session artifacts in case an artifact was created
      setIsArtifactLoading(true);
      try {
        const updatedArts = await listSessionArtifacts(targetSession.id);
        setArtifacts(updatedArts);

        if (updatedArts.length > 0) {
          setActiveArtifact(updatedArts[0]);
          setIsArtifactPanelOpen(true);
        }
      } finally {
        setIsArtifactLoading(false);
      }

      // Update session title if untitled
      if (targetSession.title === 'New Growth Conversation' || targetSession.title === 'New Conversation') {
        const newTitle = text.slice(0, 32);
        setSessions((prev) =>
          prev.map((s) => (s.id === targetSession!.id ? { ...s, title: newTitle } : s))
        );
      }
    } catch (err: any) {
      console.error('Chat error:', err);
      setError(err.message || 'Failed to complete assistant generation. Check model provider status.');
    } finally {
      setIsSending(false);
    }
  };

  const handleDeleteArtifact = async (artifactId: string) => {
    try {
      await deleteArtifact(artifactId);
      const remaining = artifacts.filter((a) => a.id !== artifactId);
      setArtifacts(remaining);
      setActiveArtifact(remaining.length > 0 ? remaining[0] : null);
    } catch (err: any) {
      console.error('Failed to delete artifact:', err);
      setError(err.message || 'Failed to delete artifact.');
    }
  };

  const handleOpenArtifact = (artifactId: string) => {
    const found = artifacts.find((a) => a.id === artifactId);
    if (found) {
      setActiveArtifact(found);
      setIsArtifactPanelOpen(true);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      {/* Top Header */}
      <header className="flex items-center justify-between px-4 sm:px-6 py-2.5 border-b border-slate-800 bg-slate-900/70 backdrop-blur shrink-0 z-10">
        <div className="flex items-center space-x-3">
          {/* Mobile hamburger menu */}
          <button
            onClick={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
            className="sm:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            title="Toggle Sessions Menu"
          >
            {isMobileSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white text-sm shadow-md shadow-indigo-500/20">
            L
          </div>
          <div>
            <h1 className="font-semibold text-sm tracking-tight text-white flex items-center space-x-2">
              <span>The Lenny Growth Assistant</span>
              <span className="hidden md:inline text-[10px] px-2 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800 font-normal">
                Grounded Intelligence
              </span>
            </h1>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              Tactical product & growth advice from Lenny's Podcast transcripts
            </p>
          </div>
        </div>

        {/* Header Right: Provider status badge & Artifact Studio toggle */}
        <div className="flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 shadow-inner">
            <span
              className={`w-2 h-2 rounded-full ${health?.status === 'ok' || health?.status === 'healthy'
                  ? 'bg-emerald-400 animate-pulse'
                  : 'bg-amber-400'
                }`}
            />
            <span className="text-slate-300 text-[11px]">
              <strong className="text-white uppercase">{health?.llm_provider || 'Ollama'}</strong>
              {health?.active_model && (
                <span className="text-slate-400 ml-1">({health.active_model})</span>
              )}
            </span>
          </div>

          <button
            onClick={() => setIsArtifactPanelOpen(!isArtifactPanelOpen)}
            className={`p-1.5 rounded-lg border text-slate-300 transition flex items-center space-x-1.5 text-xs ${isArtifactPanelOpen
                ? 'bg-indigo-600/20 border-indigo-500/50 text-indigo-200'
                : 'bg-slate-900 border-slate-800 hover:bg-slate-800'
              }`}
            title={isArtifactPanelOpen ? 'Collapse Artifact Studio' : 'Expand Artifact Studio'}
          >
            {isArtifactPanelOpen ? (
              <PanelRightClose className="w-4 h-4" />
            ) : (
              <PanelRightOpen className="w-4 h-4" />
            )}
            <span className="hidden lg:inline text-[11px] font-medium">Studio</span>
          </button>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Sidebar: Sessions (Desktop) */}
        <div className="hidden sm:flex h-full">
          <SessionSidebar
            sessions={sessions}
            currentSession={currentSession}
            onSelectSession={(s) => setCurrentSession(s)}
            onNewSession={handleNewSession}
            onDeleteSession={handleDeleteSession}
            isLoading={isSessionsLoading}
          />
        </div>

        {/* Mobile Sidebar Overlay Drawer */}
        {isMobileSidebarOpen && (
          <div className="sm:hidden absolute inset-0 z-30 bg-black/60 backdrop-blur-sm flex">
            <div className="w-64 h-full bg-slate-950 shadow-2xl">
              <SessionSidebar
                sessions={sessions}
                currentSession={currentSession}
                onSelectSession={(s) => {
                  setCurrentSession(s);
                  setIsMobileSidebarOpen(false);
                }}
                onNewSession={handleNewSession}
                onDeleteSession={handleDeleteSession}
                isLoading={isSessionsLoading}
              />
            </div>
            <div className="flex-1" onClick={() => setIsMobileSidebarOpen(false)} />
          </div>
        )}

        {/* Central Chat Workspace */}
        <main className="flex-1 flex flex-col justify-between overflow-hidden bg-slate-950">
          {/* Error Banner */}
          {error && (
            <div className="mx-4 mt-3 p-3 rounded-xl bg-rose-950/40 border border-rose-800/50 text-rose-200 text-xs flex items-center justify-between shrink-0 shadow-lg">
              <div className="flex items-center space-x-2">
                <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{error}</span>
              </div>
              <button
                onClick={() => setError(null)}
                className="p-1 rounded text-rose-400 hover:text-white hover:bg-rose-900/50 transition"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Conversation Stream */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-2">
            {isMessagesLoading ? (
              <div className="flex flex-col items-center justify-center h-full space-y-3">
                <RefreshCw className="w-6 h-6 text-indigo-400 animate-spin" />
                <p className="text-xs text-slate-400">Loading conversation history...</p>
              </div>
            ) : messages.length === 0 ? (
              <EmptyChatState
                onSelectPrompt={(prompt, skillOverride) => handleSendMessage(prompt, skillOverride)}
              />
            ) : (
              <div className="max-w-3xl mx-auto w-full">
                {messages.map((msg) => (
                  <ChatMessage
                    key={msg.id}
                    message={msg}
                    onOpenArtifact={handleOpenArtifact}
                  />
                ))}

                {isSending && (
                  <div className="flex items-center space-x-2 my-4 p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-indigo-300 w-fit">
                    <RefreshCw className="w-4 h-4 animate-spin text-indigo-400" />
                    <span>Analyzing transcripts & synthesizing response...</span>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Composer Input Bar */}
          <div className="shrink-0 bg-slate-950 border-t border-slate-850/80">
            <ChatInput
              onSendMessage={handleSendMessage}
              isLoading={isSending}
              disabled={isMessagesLoading}
            />
          </div>
        </main>

        {/* Right Artifact Studio Pane */}
        {isArtifactPanelOpen && (
          <aside className="w-full sm:w-[420px] md:w-[480px] shrink-0 border-l border-slate-800 flex flex-col h-full bg-slate-950 z-20">
            <ArtifactViewer
              artifacts={artifacts}
              activeArtifact={activeArtifact}
              onSelectArtifact={(art) => setActiveArtifact(art)}
              onDeleteArtifact={handleDeleteArtifact}
              isLoading={isArtifactLoading}
              onClose={() => setIsArtifactPanelOpen(false)}
            />
          </aside>
        )}
      </div>
    </div>
  );
}

export default App;
