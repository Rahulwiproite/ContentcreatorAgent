import { Trash2, FileText, ArrowUpRight } from "lucide-react";
import { Idea } from "../lib/api";

export default function IdeaGrid({
  ideas, onSelect, onRemove,
}: {
  ideas: Idea[];
  onSelect: (i: Idea) => void;
  onRemove: (id: number) => void;
}) {
  return (
    <section className="mt-12 animate-fade-up">
      <div className="flex items-end justify-between mb-5">
        <h2 className="font-display text-2xl tracking-widest">
          <span className="text-gradient">OUTPUT</span> <span className="text-white/40">/ {ideas.length} ideas</span>
        </h2>
        <div className="chip">click any card → full script</div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {ideas.map((i) => (
          <Card key={i.id} idea={i} onSelect={onSelect} onRemove={onRemove} />
        ))}
      </div>
    </section>
  );
}

function Card({ idea, onSelect, onRemove }: {
  idea: Idea;
  onSelect: (i: Idea) => void;
  onRemove: (id: number) => void;
}) {
  const score = Math.round(idea.virality_score * 100);
  const tier = score >= 80 ? "neon-pink" : score >= 65 ? "neon-violet" : "neon-cyan";
  return (
    <div
      onClick={() => onSelect(idea)}
      className="group relative cursor-pointer glass rounded-xl p-5 transition hover:-translate-y-0.5 hover:bg-white/[0.06] border-gradient"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="font-display text-lg leading-tight">
          {idea.title}
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); onRemove(idea.id); }}
          className="text-white/30 hover:text-red-400 transition"
          title="discard"
        >
          <Trash2 size={14} />
        </button>
      </div>

      <div className="flex items-center gap-2 mb-3">
        <span className={`chip border-${tier}/50 text-${tier}`}>
          <span className={`w-1.5 h-1.5 rounded-full mr-2 bg-${tier} animate-pulse`} />
          virality {score}
        </span>
        <span className="chip">{idea.vibe}</span>
      </div>

      <div className="text-sm text-white/80 mb-3 line-clamp-3">
        {idea.hook}
      </div>

      <div className="text-[11px] text-white/40 font-mono uppercase tracking-wider mb-2">
        post @ {idea.suggested_time || "—"}
      </div>

      <div className="flex flex-wrap gap-1.5 mb-4">
        {(idea.hashtags || []).slice(0, 5).map((h, idx) => (
          <span key={idx} className="text-[10px] font-mono text-neon-cyan/80">{h}</span>
        ))}
      </div>

      <div className="flex items-center justify-between pt-3 border-t border-white/5">
        <span className="text-[11px] font-mono text-white/40 tracking-wider uppercase">
          <FileText size={11} className="inline mr-1" /> tap for script
        </span>
        <ArrowUpRight size={14} className="text-white/30 group-hover:text-neon-violet transition" />
      </div>
    </div>
  );
}
