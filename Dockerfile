# ── Zoiko orbit Chatbot — Dockerfile ─────────────────────────────────────────
# Matches this exact folder structure:
#   backend/app.py
#   backend/retrain.py
#   backend/requirements.txt   (or root requirements.txt)
#   data/knowledge.json
#   frontend/index.html
# ──────────────────────────────────────────────────────────────────────────────

FROM python:3.10-slim

WORKDIR /app

# ── Install dependencies ───────────────────────────────────────────────────────
# Supports requirements.txt in root OR in backend/ — whichever exists
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ── Copy backend source ────────────────────────────────────────────────────────
COPY backend/ backend/

# ── Ensure backend is a Python package ────────────────────────────────────────
RUN touch backend/__init__.py

# ── Copy frontend (FastAPI serves it as static files) ─────────────────────────
COPY frontend/ frontend/

# ── Copy knowledge base (already lives in data/) ──────────────────────────────
COPY data/ data/

# ── Run retrain on every build to bake in latest knowledge ───────────────────
RUN python backend/retrain.py

# ── Cloud Run uses $PORT (default 8080) ───────────────────────────────────────
ENV PORT=8080
EXPOSE 8080

# ── Start server ──────────────────────────────────────────────────────────────
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "--log-level", "info"]
