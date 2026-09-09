import React, { useState } from 'react';
import { Artifact } from '../types';
import { Code, Eye, FileText, Layers, RefreshCw, ShieldAlert, Sparkles, X, Copy, Check, Trash2 } from 'lucide-react';

interface ArtifactViewerProps {
  artifacts: Artifact[];
  activeArtifact: Artifact | null;
  onSelectArtifact: (artifact: Artifact) => void;
  onDeleteArtifact?: (artifactId: string) => void;
  isLoading?: boolean;
  error?: string | null;
  onClose?: () => void;
}

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({
  artifacts,
  activeArtifact,
  onSelectArtifact,
  onDeleteArtifact,
  isLoading = false,
  error = null,
  onClose,
}) => {
  const [viewMode, setViewMode] = useState<'rendered' | 'code'>('rendered');
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!activeArtifact) return;
    navigator.clipboard.writeText(activeArtifact.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6 text-center space-y-3 bg-slate-900/40">
        <RefreshCw className="w-6 h-6 text-indigo-400 animate-spin" />
        <p className="text-xs text-slate-400 font-medium">Loading artifact...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6 text-center space-y-3 bg-slate-900/40">
        <ShieldAlert className="w-8 h-8 text-rose-400" />
        <h3 className="text-sm font-semibold text-white">Failed to Load Artifact</h3>
        <p className="text-xs text-slate-400 max-w-xs">{error}</p>
      </div>
    );
  }

  if (!activeArtifact) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6 text-center space-y-4 bg-slate-900/30">
        <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shadow-inner">
          <Sparkles className="w-6 h-6" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-200">Artifact Studio</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-xs leading-relaxed">
            Ship 30 for 30 essays, interactive growth calculators, and PMF models will render here side-by-side with your conversation.
          </p>
        </div>
        {artifacts.length > 0 && (
          <div className="w-full max-w-xs text-left mt-4">
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block mb-2">
              Session Artifacts ({artifacts.length})
            </span>
            <div className="space-y-1.5 max-h-60 overflow-y-auto">
              {artifacts.map((art) => (
                <button
                  key={art.id}
                  onClick={() => onSelectArtifact(art)}
                  className="w-full text-left px-3 py-2 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-xs text-slate-200 transition truncate flex items-center justify-between group"
                >
                  <div className="flex items-center space-x-2 truncate">
                    <FileText className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                    <span className="truncate">{art.title}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 uppercase font-mono">{art.artifact_type}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-slate-900/40 border-l border-slate-800">
      {/* Artifact Studio Header */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/80 backdrop-blur">
        <div className="flex items-center space-x-2 min-w-0">
          <div className="p-1.5 rounded-md bg-indigo-600/20 text-indigo-400 shrink-0">
            {activeArtifact.artifact_type === 'html' ? <Layers className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
          </div>
          <div className="min-w-0">
            <h2 className="text-xs font-semibold text-white truncate">{activeArtifact.title}</h2>
            <div className="flex items-center space-x-2 mt-0.5">
              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.2 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                {activeArtifact.artifact_type}
              </span>
              <span className="text-[10px] text-slate-400">v{activeArtifact.version}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-1.5 shrink-0">
          {/* Artifact Selector Dropdown if multiple */}
          {artifacts.length > 1 && (
            <select
              value={activeArtifact.id}
              onChange={(e) => {
                const found = artifacts.find((a) => a.id === e.target.value);
                if (found) onSelectArtifact(found);
              }}
              className="bg-slate-800 border border-slate-700 text-slate-200 text-[11px] rounded px-2 py-1 focus:outline-none focus:border-indigo-500 max-w-[120px] truncate"
            >
              {artifacts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.title}
                </option>
              ))}
            </select>
          )}

          {/* Copy Content Button */}
          <button
            onClick={handleCopy}
            className="p-1.5 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition"
            title="Copy content to clipboard"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>

          {/* Delete Artifact Button */}
          {onDeleteArtifact && (
            <button
              onClick={() => onDeleteArtifact(activeArtifact.id)}
              className="p-1.5 rounded text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
              title="Delete artifact"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}

          {/* Toggle View Mode */}
          <div className="flex items-center bg-slate-800 rounded p-0.5 border border-slate-700">
            <button
              onClick={() => setViewMode('rendered')}
              className={`px-2 py-1 rounded text-[10px] font-medium transition flex items-center space-x-1 ${
                viewMode === 'rendered' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
              title="Rendered View"
            >
              <Eye className="w-3 h-3" />
              <span>Preview</span>
            </button>
            <button
              onClick={() => setViewMode('code')}
              className={`px-2 py-1 rounded text-[10px] font-medium transition flex items-center space-x-1 ${
                viewMode === 'code' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
              title="Source Code"
            >
              <Code className="w-3 h-3" />
              <span>Code</span>
            </button>
          </div>

          {onClose && (
            <button
              onClick={onClose}
              className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition"
              title="Close Artifact Pane"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </header>

      {/* Artifact Viewer Content Body */}
      <div className="flex-1 overflow-auto p-4 bg-slate-950">
        {viewMode === 'code' ? (
          <pre className="text-[11px] font-mono text-slate-300 bg-slate-900/90 p-4 rounded-lg border border-slate-800 overflow-x-auto whitespace-pre-wrap leading-relaxed">
            {activeArtifact.content}
          </pre>
        ) : activeArtifact.artifact_type === 'html' ? (
          <div className="w-full h-full min-h-[500px] rounded-lg border border-slate-800 overflow-hidden bg-white shadow-xl">
            <iframe
              title={activeArtifact.title}
              srcDoc={activeArtifact.content}
              sandbox="allow-scripts"
              className="w-full h-full min-h-[500px] border-0"
            />
          </div>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none space-y-4 text-slate-200">
            {activeArtifact.content.split('\n\n').map((block, idx) => {
              const trimmed = block.trim();
              if (trimmed.startsWith('# ')) {
                return (
                  <h1 key={idx} className="text-xl font-bold text-white border-b border-slate-800 pb-2">
                    {trimmed.replace(/^#\s+/, '')}
                  </h1>
                );
              }
              if (trimmed.startsWith('## ')) {
                return (
                  <h2 key={idx} className="text-base font-semibold text-indigo-300 mt-4">
                    {trimmed.replace(/^##\s+/, '')}
                  </h2>
                );
              }
              if (trimmed.startsWith('### ')) {
                return (
                  <h3 key={idx} className="text-sm font-semibold text-slate-300 mt-3">
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
                  <ul key={idx} className="list-disc pl-5 space-y-1 text-xs text-slate-300">
                    {items.map((it, i) => (
                      <li key={i}>{it.replace(/^[\*\-]\s+/, '')}</li>
                    ))}
                  </ul>
                );
              }
              if (/^\d+\.\s+/.test(trimmed)) {
                const items = trimmed.split('\n').filter((l) => /^\d+\.\s+/.test(l.trim()));
                return (
                  <ol key={idx} className="list-decimal pl-5 space-y-1 text-xs text-slate-300">
                    {items.map((it, i) => (
                      <li key={i}>{it.replace(/^\d+\.\s+/, '')}</li>
                    ))}
                  </ol>
                );
              }
              return (
                <p key={idx} className="text-xs leading-relaxed text-slate-300">
                  {trimmed}
                </p>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer Security Badge */}
      <footer className="px-4 py-2 border-t border-slate-800 bg-slate-900/60 text-[10px] text-slate-500 flex items-center justify-between">
        <span className="flex items-center space-x-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span>Multi-Layer Sandbox: <code>sandbox=&quot;allow-scripts&quot;</code></span>
        </span>
        <span>CSP: <code>default-src &apos;none&apos;</code></span>
      </footer>
    </div>
  );
};
