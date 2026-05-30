import { Cpu, Zap, Radio } from "lucide-react";
import { AgentStatus } from "../lib/api";

export default function StatusBar({ status }: { status: AgentStatus | null }) {
  const provider = status?.provider || "none";
  const ok = provider !== "none";
  const sources = status?.sources || {};
  const liveSources = Object.entries(sources).filter(([, s]) => s?.available);

  return (
    <header className="relative z-10 border-b border-white/5">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Cpu size={22} className="text-neon-cyan" />
            <span className="absolute -right-1 -top-1 w-2 h-2 bg-neon-cyan rounded-full animate-pulse" />
          </div>
          <div>
            <div className="font-display font-bold tracking-widest text-sm">
              <span className="text-gradient">CONTENT.AGENT</span>
              <span className="text-white/40">_v2</span>
            </div>
            <div className="text-[10px] uppercase tracking-[0.3em] text-white/40 font-mono">
              live trend intelligence
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono flex-wrap">
          <span className="chip">
            <span className={`w-1.5 h-1.5 rounded-full mr-2 ${ok ? "bg-neon-lime animate-pulse" : "bg-red-400"}`} />
            {ok ? `LLM://${provider.toUpperCase()}` : "NO_PROVIDER"}
          </span>
          {liveSources.map(([name]) => (
            <span key={name} className="chip">
              <Radio size={10} className="mr-1 text-neon-cyan" />
              {name.toUpperCase()} LIVE
            </span>
          ))}
          <span className="chip">
            <Zap size={10} className="mr-1 text-neon-violet" /> ONLINE
          </span>
        </div>
      </div>
    </header>
  );
}
