# Multi-stage Dockerfile: build React client, then run Flask + Gunicorn/eventlet.

# ----- Stage 1: build the React client -----
FROM node:20-alpine AS client-build
WORKDIR /app/client
COPY client/package.json client/package-lock.json* ./
RUN npm ci --no-audit --no-fund
COPY client/ ./
RUN npm run build

# ----- Stage 2: Python runtime -----
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=5001

WORKDIR /app

# Install Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY src /app/catan/src
COPY web /app/catan/web
COPY ai /app/catan/ai
COPY tests /app/catan/tests
COPY __init__.py /app/catan/__init__.py
COPY GAME_RULES.md README.md /app/catan/

# Copy built client from stage 1
COPY --from=client-build /app/client/dist /app/catan/client/dist

# Make `catan` a package findable on sys.path
WORKDIR /app

ENV FLASK_APP=catan.web.app:app
EXPOSE 5001

# Gunicorn with the eventlet worker supports Socket.IO websockets. Shell form so
# $PORT expands — hosts like Render inject a dynamic port; falls back to 5001.
CMD gunicorn -k eventlet -w 1 -b 0.0.0.0:${PORT:-5001} catan.web.app:app
