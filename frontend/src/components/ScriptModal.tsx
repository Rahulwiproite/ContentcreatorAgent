import { useEffect } from "react";
import { X, Copy, Check, Loader2 } from "lucide-react";
import { useState } from "react";
import { Idea, ScriptResponse } from "../lib/api";

export default function ScriptModal({
  idea, script, loading, onClose,
}: {
  idea: Idea;
  script: ScriptResponse | null;
  loading: boolean;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);

  const copy = async () => {
    if (!script?.script) return;
    await navigator.clipboard.writeText(`${script.title}\n\n${script.script}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center p-3 md:p-8 animate-fade-up">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      <div className="relative w-full max-w-3xl glass rounded-2xl border-gradient overflow-hidden max-h-[90vh] flex flex-col">
        <div className="scanline opacity-30 absolute inset-0 pointer-events-none" />
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-neon-violet to-transparent" />

        <header className="relative flex items-start justify-between gap-4 p-5 border-b border-white/5">
          <div>
            <div className="text-[10px] uppercase tracking-[0.3em] text-neon-cyan font-mono mb-1">
              script.generated
            </div>
            <div className="font-display text-xl">{idea.title}</div>
            <div className="mt-2 flex items-center gap-2">
              <span className="chip">virality {Math.round(idea.virality_score * 100)}</span>
              <span className="chip">{idea.platform}</span>
            </div>
          </div>
          <button onClick={onClose} className="text-white/40 hover:text-white transition p-1">
            <X size={20} />
          </button>
        </header>

        <div className="relative flex-1 overflow-y-auto p-5">
          {loading && (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <Loader2 className="animate-spin text-neon-violet" size={28} />
              <div className="font-mono text-xs uppercase tracking-[0.3em] text-white/60">
                generating script…
              </div>
            </div>
          )}

          {!loading && script && (
            <pre className="text-[15px] leading-relaxed whitespace-pre-wrap text-white/90 font-sans">
              {script.script}
            </pre>
          )}
        </div>

        <footer className="relative p-4 border-t border-white/5 flex items-center justify-between gap-3">
          <div className="text-[10px] font-mono uppercase tracking-[0.25em] text-white/40">
            language: HI · use as starting point, riff on it
          </div>
          <button onClick={copy} disabled={!script || loading} className="btn-ghost disabled:opacity-50">
            {copied ? <Check size={14} className="text-neon-lime" /> : <Copy size={14} />}
            {copied ? "copied" : "copy"}
          </button>
        </footer>
      </div>
    </div>
  );
}
