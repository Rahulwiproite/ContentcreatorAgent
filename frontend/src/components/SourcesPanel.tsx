import { useState } from "react";
import { ChevronDown, Database } from "lucide-react";
import { SourceStatus } from "../lib/api";

export default function SourcesPanel({ sources }: { sources: Record<string, SourceStatus> | null }) {
  const [open, setOpen] = useState(false);
  if (!sources) return null;

  const reddit = sources.reddit;
  const x = sources.x;
  const redditPosts = reddit?.posts || [];
  const xTweets = x?.top_tweets || [];
  const xActive = !!x?.live;

  return (
    <div className="mt-10 glass rounded-xl border border-white/10 overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-3 text-left hover:bg-white/[0.03] transition"
      >
        <div className="flex items-center gap-3">
          <Database size={14} className="text-neon-cyan" />
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-white/70">
            live data analyzed
          </span>
          <span className="chip">
            <span className={`w-1.5 h-1.5 rounded-full mr-2 ${reddit?.live ? "bg-neon-lime animate-pulse" : "bg-red-400"}`} />
            reddit {reddit?.live ? `· ${redditPosts.length} posts` : "FAILED"}
          </span>
          {xActive && (
            <span className="chip">
              <span className="w-1.5 h-1.5 rounded-full mr-2 bg-neon-lime animate-pulse" />
              x · {xTweets.length} tweets
            </span>
          )}
        </div>
        <ChevronDown size={16} className={`text-white/40 transition ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="px-5 pb-5 grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-white/5 pt-4">
          <div>
            <div className="text-[10px] uppercase tracking-[0.25em] text-neon-cyan font-mono mb-2">
              Reddit · {reddit?.subs_scanned?.join(", ") || "—"}
            </div>
            {redditPosts.length === 0 && <div className="muted text-xs">no data</div>}
            <ul className="space-y-1.5 text-xs">
              {redditPosts.slice(0, 10).map((p: any, i: number) => (
                <li key={i} className="border-b border-white/5 pb-1.5">
                  <a href={p.url} target="_blank" rel="noreferrer" className="hover:text-neon-violet">
                    {p.title}
                  </a>
                  <div className="text-white/40 font-mono text-[10px] mt-0.5">
                    r/{p.subreddit} · {p.score}↑ · {p.comments}💬
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <div className="text-[10px] uppercase tracking-[0.25em] text-neon-pink font-mono mb-2">
              {xActive ? "X · viral tweets" : "more sources (optional)"}
            </div>
            {xActive ? (
              <ul className="space-y-1.5 text-xs">
                {xTweets.slice(0, 8).map((t: any, i: number) => (
                  <li key={i} className="border-b border-white/5 pb-1.5">
                    <div className="text-white/80">{t.text}</div>
                    <div className="text-white/40 font-mono text-[10px] mt-0.5">
                      {t.likes}♥ · {t.retweets}↻
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-xs text-white/50 font-mono leading-relaxed">
                Add X (Twitter) for live tweet trends by setting{" "}
                <code className="text-neon-violet">X_BEARER_TOKEN</code> in <code>backend/.env</code>.
                Instagram analytics require a Meta Developer App (currently skipped).
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
