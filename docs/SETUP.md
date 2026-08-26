# Embedded Config App — Full Setup Guide

A two-part application: a **Next.js frontend** (TypeScript, shadcn/ui, Tailwind, dark/light
mode) and a **FastAPI backend** (MySQL via SQLAlchemy async). This guide takes you
from a clean machine to a running app.

**What you get:** a dashboard that greets the user, lists past projects in cards, lets you
create a project (name + description), add ECU details for each project, view test cases
filtered by category and test type, and walk through **4 multi-select attribute pages**
one by one. Every selection is persisted to MySQL.

---

## 1. Prerequisites

| Tool    | Version tested    | Check with                                               |
| ------- | ----------------- | -------------------------------------------------------- |
| Node.js | v26 (any LTS 18+) | `node --version`                                         |
| Python  | 3.14 (3.11+)      | `python --version`                                       |
| MySQL   | 8.0 (5.7+)        | `mysql --version` or service running on `localhost:3306` |

**MySQL must be running** before you start the backend. Nothing else has to be
pre-created — the backend creates its **database, tables, and seed data automatically**
on first start. All you need is a working `user` / `password`.

---

## 2. Project layout

```
embedded/
  backend/
    app/
      main.py                    # FastAPI app, CORS, startup (create db+seed)
      config.py                  # reads .env (DATABASE_URL, CORS_ORIGINS)
      database.py                # async engine + auto-create database
      models.py                  # Project, EcuDetail, TestCase, Categories, etc.
      schemas.py                 # Pydantic request/response models
      seed.py                    # 4 pages x 5 groups x sub-attributes (idempotent)
      routers/
        projects.py              # GET/POST projects
        ecu_details.py          # GET/POST/PUT ECU details
        test_cases.py           # GET test cases with filtering
        pages.py                # page attributes + per-project page selections
    schema/
      schema.sql                # MySQL table definitions
    requirements.txt
    .env.example                # template for .env
    run.py                      # uvicorn launcher
  frontend/
    src/
      app/                      # dashboard + projects/[id]/dashboard + page/[n]
      components/               # sidebar, ECU form, test cases dashboard, etc.
      lib/                      # types, api client, navigation
    .env.local                  # NEXT_PUBLIC_API_URL (not committed)
```

---

## 3. Backend setup (FastAPI + MySQL)

### 3.1 Create a virtual env and install dependencies

From the repo root:

```bash
cd backend
python -m venv .venv
```

Activate it, then install:

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

> If `pip` reports `No module named pip`, bootstrap it first:
> `python -m ensurepip --upgrade`

### 3.2 Configure the database connection

Copy the template and edit it:

```bash
cp .env.example .env
```

```ini
# backend/.env
DATABASE_URL=mysql+aiomysql://root:manager@localhost:3306/embedded_db
CORS_ORIGINS=["http://localhost:3000"]
```

- Replace `root:manager` with **your** MySQL user and password.
- `CORS_ORIGINS` **must be JSON syntax** (it's a list) because pydantic-settings parses
  lists as JSON.

> `DATABASE_URL` is also configurable via an environment variable of the same name, which
> takes precedence over the `.env` file.

### 3.3 Run the backend

```bash
python run.py
# or directly:
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

On startup the backend **automatically**:

1. Creates the `embedded_db` database if it doesn't exist.
2. Creates all tables (projects, ECU details, test cases, categories, etc.).
3. Seeds the 4 pages with 5 main attributes each (idempotent — safe to restart).

Verify:

```bash
curl http://localhost:8000/api/health        # {"status":"ok"}
curl http://localhost:8000/api/projects      # []
curl http://localhost:8000/api/pages/1/attributes  # 5 seeded groups
curl http://localhost:8000/api/test-cases/categories  # test categories
```

Interactive docs: **http://localhost:8000/docs**

---

## 4. Frontend setup (Next.js + shadcn)

The shadcn/ui components are pre-installed in `frontend/src/components/ui`,
so `npm install` is all you need.

```bash
cd frontend
npm install
```

Create the environment file (not committed to git):

```bash
# Windows (PowerShell)
New-Item -ItemType File .env.local
# macOS / Linux
touch .env.local
```

```ini
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

Run the dev server:

```bash
npm run dev
```

Open **http://localhost:3000** — the dashboard greets you, shows project cards, and the
**New project** button starts the 4-page wizard.

---

## 5. Running both at once

Terminal 1 — backend:

```bash
cd backend
python run.py          # -> http://localhost:8000
```

Terminal 2 — frontend:

```bash
cd frontend
npm run dev            # -> http://localhost:3000
```

**Flow:** Dashboard → **New project** (name + description) → auto-redirects to
`/projects/{id}/page/1` → select sub-attributes, **Save & continue** through pages 1–4 →
back to the dashboard with the new project card. Toggle dark/light via the button in the
sidebar footer. Reloading a page restores your saved selections from the backend.

---

## 6. Config summary

| Setting              | Backend (`.env`)                                                      | Frontend (`.env.local`)                         |
| -------------------- | --------------------------------------------------------------------- | ----------------------------------------------- |
| API URL              | —                                                                     | `NEXT_PUBLIC_API_URL=http://localhost:8000/api` |
| Database             | `DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/embedded` | —                                               |
| Allowed CORS origins | `CORS_ORIGINS=["http://localhost:3000"]`                              | —                                               |
| Greeting name        | —                                                                     | `src/config.ts` → `APP_USER_NAME = "Alex"`      |

CORS already allows `http://localhost:3000`, so the frontend can call the API.

---

## 7. Common issues

**Backend won't start: `error parsing value for field "cors_origins"`**
`syntax: CORS_ORIGINS` must be JSON: `CORS_ORIGINS=["http://localhost:3000"]`.

**`password authentication failed for user "postgres"`**
Your real Postgres password differs from the default. Update `DATABASE_URL` in `backend/.env`.

**Port 8000 already in use**
Stop the previous server: on PowerShell
`Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force`.

**`python -m venv .venv` fails with "Unable to copy ... python.exe"**
The existing venv's interpreter is still running (e.g. the backend is up). Stop the server
first, then delete `.venv` and recreate. You usually don't need to recreate at all — just
reuse the existing `.venv`.

**Frontend "fetch failed" / empty dashboard**
Backend isn't running, or `NEXT_PUBLIC_API_URL` points at the wrong host/port. Start the
backend and confirm `http://localhost:8000/api/health` responds.

**Missing sub-attributes on a page (500 from `/api/pages/{n}/attributes`)**
This was a lazy-loading bug in async SQLAlchemy; it's already fixed with `selectinload` in
`app/routers/pages.py`. If you see it again, ensure the query uses
`.options(selectinload(AttributeGroup.attributes))`.

---

## 8. Restarting clean (fresh data)

To wipe all data and start over:

```bash
# from the repo root, with backend stopped
psql -U postgres -c "DROP DATABASE IF EXISTS embedded WITH (FORCE);"
```

Then just run the backend again — it recreates the database, tables, and seed data.
