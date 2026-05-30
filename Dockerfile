# Unified single-container image for Hugging Face Spaces.
# Stage 1: build the Vite frontend, then stage 2 copies its /dist into the
# FastAPI app's static folder. FastAPI serves both the JSON API and the SPA
# from the same origin on port 7860 (HF Spaces default).

FROM node:20-alpine AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci || npm install
COPY frontend ./
ENV VITE_API_BASE=""
RUN npm run build

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/app ./app
COPY --from=frontend /fe/dist ./app/static

# HF Spaces gives writable /data. Local Docker also works (volume mount).
RUN mkdir -p /data && chmod 777 /data
ENV DATABASE_URL=sqlite:////data/agent.db
ENV PORT=7860
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://127.0.0.1:7860/healthz || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
