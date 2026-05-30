import axios from "axios";

export const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export const api = axios.create({ baseURL: API_BASE });

export type Idea = {
  id: number;
  title: string;
  hook: string;
  script_outline: string;
  hashtags: string[];
  suggested_time: string;
  platform: string;
  virality_score: number;
  vibe: string;
  favorite: boolean;
  posted: boolean;
  created_at: string;
};

export type LanguageOption = { code: string; label: string };

export type SourceStatus = {
  available?: boolean;
  live?: boolean;
  note?: string;
  reason?: string;
  error?: string;
  posts?: { subreddit: string; title: string; score: number; comments: number; url: string }[];
  top_tweets?: { text: string; likes: number; retweets: number }[];
  subs_scanned?: string[];
  category?: string;
};

export type AgentStatus = {
  ready: boolean;
  provider: string;
  niche: string;
  categories: string[];
  languages: LanguageOption[];
  sources: Record<string, SourceStatus>;
};

export type StartResponse = {
  niche: string;
  category: string;
  language: string;
  provider: string;
  sources: Record<string, SourceStatus>;
  ideas: Idea[];
};

export type ScriptResponse = { idea_id: number; title: string; script: string; language: string };

export const agent = {
  status: () => api.get<AgentStatus>("/agent/status").then((r) => r.data),
  start: (data: {
    niche?: string; category?: string; language?: string;
    vibe?: string; count?: number; platform?: string;
  }) => api.post<StartResponse>("/agent/start", data).then((r) => r.data),
  ideas: () => api.get<Idea[]>("/agent/ideas").then((r) => r.data),
  script: (id: number, language?: string) =>
    api.post<ScriptResponse>(`/agent/ideas/${id}/script`, language ? { language } : {}).then((r) => r.data),
  remove: (id: number) => api.delete(`/agent/ideas/${id}`).then((r) => r.data),
};
