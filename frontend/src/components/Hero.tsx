import { Sparkles, Play, RefreshCw } from "lucide-react";
import { AgentStatus } from "../lib/api";

const VIBES = [
  "relatable observational",
  "educational",
  "inspirational",
  "self-deprecating",
  "roast",
  "wholesome",
  "satire",
  "high-energy",
  "calm explainer",
];

export default function Hero({
  phase, niche, setNiche, category, setCategory, language, setLanguage,
  vibe, setVibe, count, setCount, onStart, status, ideasExist,
}: {
  phase: "idle" | "scanning" | "results";
  niche: string; setNiche: (v: string) => void;
  category: string; setCategory: (v: string) => void;
  language: string; setLanguage: (v: string) => void;
  vibe: string; setVibe: (v: string) => void;
  count: number; setCount: (v: number) => void;
  onStart: () => void;
  status: AgentStatus | null;
  ideasExist: boolean;
}) {
  const busy = phase === "scanning";
  const categories = status?.categories || ["general"];
  const languages = status?.languages || [{ code: "en", label: "English" }];

  return (
    <section className="text-center pt-6 pb-8 animate-fade-up">
      <div className="inline-flex items-center gap-2 chip mb-6 border-neon-violet/30">
        <Sparkles size={12} className="text-neon-violet" />
        <span>autonomous content intelligence</span>
      </div>

      <h1 className="font-display text-5xl md:text-6xl font-black leading-tight">
        <span className="text-gradient">VIRAL IDEAS</span>
        <span className="block text-white/90 mt-2 text-3xl md:text-4xl font-mono">
          for any creator. any niche.
        </span>
      </h1>

      <p className="mt-5 max-w-2xl mx-auto text-white/60 text-sm md:text-base font-mono">
        agent scans live trends from Reddit + X &rarr; matches them to your niche
        &rarr; outputs ideas + full reel scripts in your language.
      </p>

      <div className="mt-10 mx-auto max-w-4xl glass border border-white/10 rounded-2xl p-5 md:p-6 relative">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4 text-left">
          <Field label="YOUR NICHE / DESCRIPTION">
            <input
              className="w-full bg-transparent outline-none text-sm placeholder:text-white/30 placeholder:font-mono"
              value={niche}
              onChange={(e) => setNiche(e.target.value)}
              placeholder="e.g. home workouts for desk workers, age 25-35"
            />
          </Field>
          <Field label="CATEGORY">
            <select
              className="w-full bg-transparent outline-none font-mono text-sm cursor-pointer"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {categories.map((c) => <option key={c} value={c} className="bg-bg">{c}</option>)}
            </select>
          </Field>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5 text-left">
          <Field label="LANGUAGE">
            <select
              className="w-full bg-transparent outline-none font-mono text-sm cursor-pointer"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              {languages.map((l) => <option key={l.code} value={l.code} className="bg-bg">{l.label}</option>)}
            </select>
          </Field>
          <Field label="VIBE">
            <select
              className="w-full bg-transparent outline-none font-mono text-sm cursor-pointer"
              value={vibe}
              onChange={(e) => setVibe(e.target.value)}
            >
              {VIBES.map((v) => <option key={v} value={v} className="bg-bg">{v}</option>)}
            </select>
          </Field>
          <Field label="IDEAS COUNT">
            <input
              type="number" min={1} max={10}
              className="w-full bg-transparent outline-none font-mono text-sm"
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
            />
          </Field>
        </div>

        <button onClick={onStart} disabled={busy} className="btn-primary w-full md:w-auto mx-auto animate-glow">
          {busy ? <RefreshCw size={16} className="animate-spin" /> : <Play size={16} />}
          {busy ? "AGENT.RUNNING" : ideasExist ? "REGENERATE" : "START THE AGENT"}
        </button>
      </div>
    </section>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <div className="text-[10px] uppercase tracking-[0.25em] text-white/40 font-mono mb-1.5">
        {label}
      </div>
      <div className="px-3 py-2 rounded-lg bg-white/[0.03] border border-white/10 focus-within:border-neon-violet/60 transition">
        {children}
      </div>
    </label>
  );
}
