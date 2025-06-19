# Temperature Monitoring System

This repository is a **production‑ready, modular Python monorepo** that simulates, ingests, stores,
and serves temperature data for refrigerated facilities (e.g., cold‑chain warehouses).

## Highlights
* **FastAPI** + **SQLAlchemy** back‑end with JWT auth
* Pluggable data collectors (CSV, API, Webhook)
* Postgres + Alembic‑style SQL migrations
* Docker & Kubernetes deployment blueprints
* Hooks for future ML anomaly detection and a Grafana/Prometheus stack

## Quick Start (Local)

```bash
# 1. Clone and enter
git clone <repo‑url> && cd temperature-monitoring-system
# 2. Create a virtualenv + install deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# 3. Spin up containers (Postgres, Prometheus, etc.)
docker compose up -d
# 4. Run migrations & seed db
make db-init
# 5. Launch API
make api
```

Visit **http://localhost:8000/docs** for interactive OpenAPI docs.

See [`docs/`](docs/) for full architecture notes and user guides.
