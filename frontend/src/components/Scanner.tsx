import { useEffect, useState } from "react";
import { SourceStatus } from "../lib/api";

export default function Scanner({
  sources, category,
}: { sources: Record<string, SourceStatus>; category: string }) {
  const redditOn = sources.reddit?.available;
  const xOn = sources.x?.available;
  const igOn = sources.instagram?.available;

  const steps = [
    redditOn ? `fetching top posts from Reddit r/${category}…` : "Reddit OFFLINE",
    xOn ? "scraping viral tweets from X…" : "X OFFLINE (skip)",
    igOn ? "pulling Instagram top hashtags…" : "Instagram OFFLINE (skip)",
    "analyzing meme grammar & format velocity…",
    "matching trends to your niche…",
    "drafting hooks (3-second discipline)…",
    "scoring virality & finalizing ideas…",
  ];

  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((x) => Math.min(x + 1, steps.length - 1)), 1400);
    return () => clearInterval(t);
  }, [steps.length]);

  return (
    <div className="mt-10 max-w-3xl mx-auto glass rounded-2xl p-6 relative overflow-hidden">
      <div className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-neon-cyan to-transparent animate-scan" />
      <div className="scanline opacity-50" />

      <div className="flex items-center gap-3 mb-5">
        <div className="relative w-8 h-8">
          <div className="absolute inset-0 rounded-full border-2 border-neon-cyan/30" />
          <div className="absolute inset-0 rounded-full border-t-2 border-neon-cyan animate-spin-slow" />
          <div className="absolute inset-1 rounded-full bg-neon-cyan/20 animate-pulse" />
        </div>
        <div>
          <div className="font-display tracking-widest text-sm text-neon-cyan">AGENT.SCANNING</div>
          <div className="text-[10px] font-mono uppercase text-white/40 tracking-[0.25em]">do not close window</div>
        </div>
      </div>

      <ul className="space-y-2 font-mono text-sm">
        {steps.map((s, idx) => (
          <li key={idx} className={`flex items-start gap-3 transition ${idx > i ? "opacity-30" : ""}`}>
            <span className={`mt-1.5 inline-block w-2 h-2 rounded-full ${
              idx < i ? "bg-neon-lime" : idx === i ? "bg-neon-cyan animate-pulse" : "bg-white/20"
            }`} />
            <span className={idx === i ? "text-white" : "text-white/60"}>{s}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
