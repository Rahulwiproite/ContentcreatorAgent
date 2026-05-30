---
title: ContentcreatorAgent
emoji: "\U0001F3AC"
colorFrom: violet
colorTo: cyan
sdk: docker
app_port: 7860
pinned: false
short_description: AI agent that turns live Reddit trends into viral reel scripts
---

# ContentcreatorAgent

An always-on AI agent for short-form video creators. Scrapes live trends from Reddit (+ optional X), matches them to your niche, and outputs ready-to-shoot Reel / Shorts / TikTok scripts in English, Hindi or Hinglish. Powered by Google Gemini. FastAPI + React + Docker. No login required.

> Hosted on Hugging Face Spaces? Add `GEMINI_API_KEY` as a Space Secret (Settings -> Variables and secrets). Optionally add `X_BEARER_TOKEN` for live tweet trends.

## Features

- 17 creator categories (comedy, fitness, food, fashion, tech, gaming, education, lifestyle, business, music, travel, parenting, relationships, news, motivation, beauty, general)
- Live Reddit trend scraping via public RSS (no API key needed)
- Optional X (Twitter) v2 API integration for tweet-level trends
- Multi-language output: English / Hindi (Devanagari) / Hinglish
- Click any idea -> full 30-second shootable reel script with timestamps + on-screen text
- Automatic Gemini model fallback chain to handle free-tier rate limits

## Tech Stack

- Backend: FastAPI, SQLAlchemy, SQLite, APScheduler, httpx
- Frontend: React 18, Vite, TailwindCSS, Lucide
- AI: Google Gemini (`gemini-2.5-flash` w/ auto-fallback)
- Trends: Reddit RSS, X API v2 (optional)
- Deploy: Docker Compose

## Quick start (Docker)

```bash
cp backend/.env.example backend/.env
# edit backend/.env -> paste your GEMINI_API_KEY
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Local dev (without Docker)

Backend:
```bash
cd backend
python -m venv .venv
.venv/Scripts/activate  # or source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in GEMINI_API_KEY
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Getting a free Gemini API key

1. Visit https://aistudio.google.com/apikey
2. Sign in -> Create API key (free tier)
3. Paste into `backend/.env` as `GEMINI_API_KEY=...`

Free tier limits are low (~20-250 requests/day depending on model). The app auto-falls back across 4 Gemini Flash variants. For unlimited use, add billing in Google AI Studio.

## Optional: enable X (Twitter) trends

1. https://developer.twitter.com/en/portal/dashboard
2. Create a project + app, grab the Bearer Token
3. Paste into `backend/.env` as `X_BEARER_TOKEN=...`

## Project structure

```
backend/
  app/
    main.py
    routers/agent.py        # /agent/start /agent/ideas /agent/ideas/{id}/script
    services/
      ai.py                 # provider-agnostic ideation + scripting
      gemini.py             # Gemini client with model fallback chain
      reddit.py             # RSS-based trend fetcher
      twitter.py            # X API v2 client
frontend/
  src/
    App.tsx
    components/             # Hero, Scanner, IdeaGrid, ScriptModal, SourcesPanel, StatusBar
    lib/api.ts
```

## License

MIT
