import { useEffect, useState } from "react";
import { agent, Idea, ScriptResponse, AgentStatus, SourceStatus } from "./lib/api";
import Hero from "./components/Hero";
import Scanner from "./components/Scanner";
import IdeaGrid from "./components/IdeaGrid";
import ScriptModal from "./components/ScriptModal";
import StatusBar from "./components/StatusBar";
import SourcesPanel from "./components/SourcesPanel";

type Phase = "idle" | "scanning" | "results";

export default function App() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [activeSources, setActiveSources] = useState<Record<string, SourceStatus> | null>(null);

  const [niche, setNiche] = useState("");
  const [category, setCategory] = useState("general");
  const [language, setLanguage] = useState("en");
  const [vibe, setVibe] = useState("relatable observational");
  const [count, setCount] = useState(6);

  const [err, setErr] = useState("");
  const [selected, setSelected] = useState<Idea | null>(null);
  const [script, setScript] = useState<ScriptResponse | null>(null);
  const [scriptLoading, setScriptLoading] = useState(false);

  useEffect(() => {
    agent.status().then((s) => {
      setStatus(s);
      setNiche(s.niche);
    }).catch(() => {});
    agent.ideas().then((rows) => {
      if (rows.length) { setIdeas(rows); setPhase("results"); }
    }).catch(() => {});
  }, []);

  const start = async () => {
    setErr("");
    setPhase("scanning");
    try {
      const r = await agent.start({ niche, category, language, vibe, count });
      setIdeas(r.ideas);
      setActiveSources(r.sources);
      setPhase("results");
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Agent failed. Check backend logs.");
      setPhase("idle");
    }
  };

  const openScript = async (idea: Idea) => {
    setSelected(idea);
    setScript(null);
    setScriptLoading(true);
    try { setScript(await agent.script(idea.id, language)); }
    catch (e: any) {
      setScript({
        idea_id: idea.id, title: idea.title,
        script: "ERROR: " + (e?.response?.data?.detail || "Could not generate script"),
        language,
      });
    } finally { setScriptLoading(false); }
  };

  const removeIdea = async (id: number) => {
    await agent.remove(id);
    setIdeas(ideas.filter((i) => i.id !== id));
  };

  return (
    <div className="min-h-screen relative overflow-x-hidden">
      <div className="absolute inset-0 grid-bg opacity-30 pointer-events-none" />
      <StatusBar status={status} />

      <main className="relative max-w-6xl mx-auto px-6 pt-10 pb-24">
        <Hero
          phase={phase}
          niche={niche}
          setNiche={setNiche}
          category={category}
          setCategory={setCategory}
          language={language}
          setLanguage={setLanguage}
          vibe={vibe}
          setVibe={setVibe}
          count={count}
          setCount={setCount}
          onStart={start}
          status={status}
          ideasExist={ideas.length > 0}
        />
        {err && <div className="mt-6 chip border-red-500/50 text-red-300">{err}</div>}
        {phase === "scanning" && <Scanner sources={status?.sources || {}} category={category} />}
        {phase === "results" && (
          <>
            <SourcesPanel sources={activeSources} />
            <IdeaGrid ideas={ideas} onSelect={openScript} onRemove={removeIdea} />
          </>
        )}
      </main>

      {selected && (
        <ScriptModal
          idea={selected}
          script={script}
          loading={scriptLoading}
          onClose={() => { setSelected(null); setScript(null); }}
        />
      )}
    </div>
  );
}
