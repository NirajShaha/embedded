# Embedded Config App

A two-part full-stack app: **Next.js + shadcn/ui + Tailwind** frontend and a **FastAPI +
PostgreSQL** backend. Create a project and walk through 4 multi-select attribute pages.

## Quick start

```bash
# Backend (terminal 1)
cd backend
python -m venv .venv
pip install -r requirements.txt
cp .env.example .env        # then set your Postgres user/password in .env
python run.py               # http://localhost:8000

# Frontend (terminal 2)
cd frontend
npm install
# create .env.local with NEXT_PUBLIC_API_URL=http://localhost:8000/api
npm run dev                 # http://localhost:3000
```

The backend **auto-creates** the database, tables, and seed data on first run.

## Docs

Full from-scratch setup, configuration, and troubleshooting:
**[SETUP.md](./SETUP.md)**

## Stack

- **Frontend:** Next.js 16, TypeScript, Tailwind CSS v4, shadcn/ui, next-themes, React Query
- **Backend:** FastAPI, SQLAlchemy 2.0 (async), asyncpg, PostgreSQL