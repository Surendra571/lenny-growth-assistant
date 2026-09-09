import React from 'react';
import { Sparkles, MessageSquare, Zap, Layers } from 'lucide-react';

interface EmptyChatStateProps {
  onSelectPrompt: (prompt: string, skillOverride?: string) => void;
}

export const EmptyChatState: React.FC<EmptyChatStateProps> = ({ onSelectPrompt }) => {
  const promptExamples = [
    {
      title: "Superhuman's PMF Engine",
      guest: "Rahul Vohra",
      prompt: "How did Rahul Vohra measure PMF for Superhuman using the 40% disappointed metric?",
      icon: Zap,
    },
    {
      title: "B2B Product-Led Growth",
      guest: "Elena Verna",
      prompt: "How does Elena Verna define self-serve freemium flywheels and product-qualified leads?",
      icon: Layers,
    },
    {
      title: "Founder Mode & Strategy",
      guest: "Brian Chesky",
      prompt: "What were Brian Chesky's key lessons on founder mode and product orchestration at Airbnb?",
      icon: MessageSquare,
    },
    {
      title: "Ship 30 for 30 Essay",
      guest: "Editorial Synthesis",
      prompt: "Write a Ship 30 for 30 atomic essay about cohort retention curves and compounding growth loops.",
      skillOverride: "ship30",
      icon: Sparkles,
    },
  ];

  return (
    <div className="max-w-2xl mx-auto w-full flex-1 flex flex-col justify-center items-center text-center px-4 py-8 space-y-6">
      <div className="w-14 h-14 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 text-2xl shadow-lg shadow-indigo-500/5">
        ✦
      </div>
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">The Lenny Growth Assistant</h2>
        <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto leading-relaxed">
          Grounded product and growth wisdom extracted directly from Lenny's Podcast transcripts. Ask tactical questions or synthesize Ship 30 for 30 essays.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl">
        {promptExamples.map((item, idx) => {
          const Icon = item.icon;
          return (
            <button
              key={idx}
              onClick={() => onSelectPrompt(item.prompt, item.skillOverride)}
              className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 text-left hover:border-indigo-500/50 hover:bg-slate-850 transition flex flex-col justify-between group shadow-sm"
            >
              <div className="flex items-center justify-between w-full">
                <span className="text-xs font-semibold text-slate-200 group-hover:text-indigo-300 transition">
                  {item.title}
                </span>
                <Icon className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400 transition" />
              </div>
              <p className="text-[11px] text-slate-400 mt-1.5 line-clamp-2 leading-relaxed">
                {item.prompt}
              </p>
              <span className="text-[10px] text-indigo-400/80 font-medium mt-2 block">
                {item.guest} →
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

