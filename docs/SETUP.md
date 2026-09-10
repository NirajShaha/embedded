# Embedded Config App — Complete Setup Guide

A full-stack application for managing **ECU (Electronic Control Unit) configurations and security testing**.

- **Frontend:** Next.js 16 + TypeScript + shadcn/ui + Tailwind CSS (dark/light mode)
- **Backend:** FastAPI + SQLAlchemy async + MySQL 8.0
- **Database:** MySQL with Prisma schema management

The application auto-creates the database, tables, and seed data on first backend run. You manage projects, ECU details, test cases, and walk through **4 multi-select attribute configuration pages**. All data persists to MySQL.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Project Structure](#2-project-structure)
3. [Backend Setup](#3-backend-setup)
4. [Frontend Setup](#4-frontend-setup)
5. [Running Both Servers](#5-running-both-at-once)
6. [Configuration Reference](#6-configuration-reference)
7. [API Endpoints](#7-api-endpoints)
8. [Troubleshooting](#8-troubleshooting)
9. [Fresh Start / Reset Database](#9-restarting-clean-fresh-data)

---

## 1. Prerequisites

Install these tools first:

| Tool    | Version      | Check with                      | Download                              |
| ------- | ------------ | ------------------------------- | ------------------------------------ |
| Node.js | 18+ (LTS)    | `node --version`                | https://nodejs.org                   |
| Python  | 3.11+        | `python --version`              | https://python.org                   |
| MySQL   | 5.7+ (8.0+)  | `mysql --version` or app verify | https://mysql.com or Docker image    |

**Critical:** MySQL must be running and accessible at `localhost:3306` before starting the backend.
- Default MySQL credentials: `root` / `password` (or your custom user/password)
- Database is auto-created; no manual schema setup needed

**Optional:** Git (for cloning the repository)

---

## 2. Project Structure

```
embedded/
├── backend/                        # FastAPI + SQLAlchemy + MySQL
│   ├── app/
│   │   ├── main.py                # FastAPI app entry, CORS setup, auto-seed on startup
│   │   ├── config.py              # Environment config (DATABASE_URL, CORS_ORIGINS)
│   │   ├── database.py            # Async SQLAlchemy engine + auto-create database
│   │   ├── models.py              # ORM models (Project, EcuDetail, TestCase, etc.)
│   │   ├── schemas.py             # Pydantic request/response schemas
│   │   ├── auth.py                # Authentication (JWT, password hashing with pwdlib)
│   │   ├── pdf_generator.py       # PDF generation for test cases
│   │   ├── prisma_client.py       # Prisma ORM client
│   │   ├── routers/
│   │   │   ├── projects.py        # GET/POST projects (list, create, get by ID)
│   │   │   ├── ecu_details.py    # GET/POST/PUT ECU configurations
│   │   │   ├── test_cases.py     # GET test cases with filtering (category, type)
│   │   │   ├── pages.py          # Page attributes + per-project page selections
│   │   │   ├── admin_test_cases.py
│   │   │   └── auth.py           # Auth endpoints
│   │   └── seed.py                # Auto-seed: 4 pages × 5 groups with attributes
│   ├── prisma/
│   │   ├── schema.prisma          # Prisma schema definitions
│   │   └── migrations/            # Database migrations
│   ├── requirements.txt           # Python dependencies
│   ├── .env.example               # Template for .env (copy this → .env)
│   └── run.py                     # Uvicorn launcher script
│
├── frontend/                       # Next.js + TypeScript + shadcn/ui
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx           # Dashboard (project cards, new project button)
│   │   │   ├── login/page.tsx     # Login page
│   │   │   ├── admin/             # Admin test cases management
│   │   │   └── projects/[projectId]/
│   │   │       ├── dashboard/     # Project-specific dashboard
│   │   │       └── page/[pageNumber]/  # Multi-page configuration wizard
│   │   ├── components/
│   │   │   ├── create-project-dialog.tsx
│   │   │   ├── ecu-detail-form.tsx
│   │   │   ├── test-cases-dashboard.tsx
│   │   │   ├── page-selection-form.tsx
│   │   │   └── ui/               # shadcn/ui components (buttons, cards, dialogs, etc.)
│   │   ├── lib/
│   │   │   ├── api.ts            # Fetch wrapper + base API URLs
│   │   │   ├── types.ts          # TypeScript type definitions
│   │   │   └── utils.ts          # Utility functions
│   │   └── config.ts             # Frontend app config (greetings, names, etc.)
│   ├── package.json              # Dependencies + scripts
│   ├── tsconfig.json             # TypeScript config
│   ├── next.config.ts            # Next.js config
│   └── .env.local                # Environment variables (not committed, auto-ignored)
│
└── docs/                          # Documentation
    ├── SETUP.md                   # This file
    ├── IMPLEMENTATION.md          # Implementation details and flow
    └── PDF_GENERATION.md          # PDF feature documentation
```

---

## 3. Backend Setup (FastAPI + MySQL)

### 3.1 Open Terminal & Navigate

```bash
cd backend
```

### 3.2 Create & Activate Python Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (Command Prompt)
.venv\Scripts\activate.bat

# macOS / Linux
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt.

### 3.3 Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies include:**
- `fastapi` — web framework
- `uvicorn[standard]` — ASGI server
- `sqlalchemy` + `aiomysql` — async MySQL driver
- `pydantic` + `pydantic-settings` — validation & config
- `PyJWT` + `pwdlib[argon2]` — authentication
- `pandas` + `openpyxl` — Excel reading
- `reportlab` + `pillow` — PDF generation
- `cryptography` — encryption
- `prisma` — ORM (optional, for migrations)

### 3.4 Configure MySQL Connection

Copy the example environment file:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `backend/.env`:

```ini
# backend/.env
DATABASE_URL=mysql+aiomysql://root:password@localhost:3306/embedded_db
CORS_ORIGINS=["http://localhost:3000"]
```

**Important:**
- Replace `root:password` with your actual MySQL username and password
- `embedded_db` is created automatically; don't create it manually
- `CORS_ORIGINS` must be **valid JSON** (a list in double quotes)

### 3.5 Start the Backend

```bash
python run.py
```

Or directly:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**On startup, the backend automatically:**
1. Connects to MySQL
2. Creates the `embedded_db` database (if missing)
3. Creates all tables using SQLAlchemy models
4. Seeds 4 pages with 5 attribute groups each (idempotent — safe to restart)

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 3.6 Verify Backend is Running

In a new terminal (while backend is running):

```bash
# Check health
curl http://localhost:8000/api/health

# List projects (should be empty initially)
curl http://localhost:8000/api/projects

# View seeded page attributes
curl http://localhost:8000/api/pages/1/attributes

# View test case categories
curl http://localhost:8000/api/test-cases/categories
```

**Interactive API docs:** Open http://localhost:8000/docs in your browser to explore all endpoints.

---

## 4. Frontend Setup (Next.js + shadcn/ui)

### 4.1 Open a New Terminal & Navigate

```bash
cd frontend
```

### 4.2 Install Dependencies

```bash
npm install
```

This installs:
- **Next.js 16** — React framework
- **TypeScript** — type safety
- **shadcn/ui** — pre-built UI components
- **Tailwind CSS** — utility-first styling
- **Radix UI** — accessible component primitives
- **TanStack Query** — data fetching
- **TanStack Table** — data tables

### 4.3 Create Environment File

```bash
# Windows (PowerShell)
New-Item -ItemType File .env.local

# macOS / Linux
touch .env.local
```

Edit `frontend/.env.local`:

```ini
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

**Note:** `NEXT_PUBLIC_` prefix makes this variable available in the browser. Keep this file in `.gitignore` (already excluded).

### 4.4 Start the Frontend Dev Server

```bash
npm run dev
```

**Expected output:**
```
  ▲ Next.js 16.0.0
  - Local:        http://localhost:3000
  - Environments: .env.local
```

Open **http://localhost:3000** in your browser.

---

## 5. Running Both at Once

**Terminal 1 (Backend):**

```bash
cd backend
# (activate venv first if not already)
python run.py
```

**Terminal 2 (Frontend):**

```bash
cd frontend
npm run dev
```

### User Journey

1. **Dashboard** → See project cards + greeting
2. **New Project** → Enter project name & description
3. **Auto-redirect** → `/projects/{id}/page/1`
4. **Configuration Wizard** → Pages 1–4, select attributes on each page
5. **Save & Continue** → Progress through wizard
6. **Back to Dashboard** → New project card appears with all selections persisted

### UI Features

- **Dark/Light Mode** → Toggle in sidebar footer
- **Responsive** → Works on desktop, tablet, mobile
- **Live Reload** → Changes appear instantly (with `.venv` running backend)

---

## 6. Configuration Reference

### Backend Environment Variables

**`backend/.env`**

| Variable          | Example                                                  | Required | Notes                                                       |
| ----------------- | -------------------------------------------------------- | -------- | ----------------------------------------------------------- |
| `DATABASE_URL`    | `mysql+aiomysql://root:password@localhost:3306/embedded` | ✓        | Must be MySQL async URL; database auto-created on startup   |
| `CORS_ORIGINS`    | `["http://localhost:3000"]`                              | ✓        | **Must be valid JSON** (double-quoted list)                 |
| `SECRET_KEY`      | (optional)                                               |          | JWT secret; auto-generated if omitted                       |

### Frontend Environment Variables

**`frontend/.env.local`**

| Variable               | Example                        | Required | Notes                                                          |
| ---------------------- | ------------------------------ | -------- | -------------------------------------------------------------- |
| `NEXT_PUBLIC_API_URL`  | `http://localhost:8000/api`    | ✓        | Backend API base URL; must match running backend              |

### Frontend Source Config

**`frontend/src/config.ts`**

```typescript
export const APP_USER_NAME = "Alex";        // Greeting name
export const DEFAULT_DARK_MODE = false;     // Dark mode by default?
```

---

## 7. API Endpoints

All endpoints are prefixed with `/api`.

### Projects

- `GET /api/projects` — List all projects (cards, project info)
- `POST /api/projects` — Create a new project (name, description)
- `GET /api/projects/{projectId}` — Get project details
- `PUT /api/projects/{projectId}` — Update project

### ECU Details

- `GET /api/projects/{projectId}/ecu-details` — List ECU details for a project
- `POST /api/projects/{projectId}/ecu-details` — Add ECU detail
- `PUT /api/ecu-details/{ecuId}` — Update ECU detail

### Test Cases

- `GET /api/test-cases` — List all test cases
- `GET /api/test-cases/categories` — List test categories
- `GET /api/projects/{projectId}/test-cases` — Test cases for a project
- (Filtering by category and test type supported via query params)

### Page Attributes

- `GET /api/pages/{pageNumber}/attributes` — Seeded attributes for page N (1–4)
- `GET /api/projects/{projectId}/pages/{pageNumber}/selections` — User's saved selections
- `POST /api/projects/{projectId}/pages/{pageNumber}/selections` — Save attribute selections

### Health & Docs

- `GET /api/health` — Backend status (`{"status":"ok"}`)
- `GET /docs` — Interactive Swagger UI (FastAPI docs)
- `GET /redoc` — ReDoc API documentation

---

## 8. Troubleshooting

### Backend Issues

#### "Failed to connect to MySQL server"
- **Cause:** MySQL not running or wrong credentials
- **Fix:**
  ```bash
  # Verify MySQL is running (Windows)
  Get-Process mysqld
  # or check Services app
  
  # Test connection
  mysql -u root -p -h localhost
  ```
- Update `DATABASE_URL` in `backend/.env` with correct credentials

#### "CORS_ORIGINS error parsing value"
- **Cause:** `CORS_ORIGINS` is not valid JSON
- **Fix:** Ensure it's a valid JSON list with double quotes:
  ```ini
  # Wrong
  CORS_ORIGINS=['http://localhost:3000']
  
  # Correct
  CORS_ORIGINS=["http://localhost:3000"]
  ```

#### "Port 8000 already in use"
- **Fix (Windows PowerShell):**
  ```powershell
  $id = (Get-NetTCPConnection -LocalPort 8000).OwningProcess
  Stop-Process -Id $id -Force
  ```
- **Fix (macOS/Linux):**
  ```bash
  lsof -i :8000
  kill -9 <PID>
  ```

#### "No module named 'aiomysql'" after installing requirements
- **Cause:** `pip install` might have failed silently
- **Fix:**
  ```bash
  pip install --upgrade pip
  pip install -r requirements.txt --no-cache-dir
  ```

#### ".venv\Scripts\Activate.ps1 cannot be loaded" (PowerShell)
- **Cause:** Execution policy blocked
- **Fix:**
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  .venv\Scripts\Activate.ps1
  ```

### Frontend Issues

#### "fetch failed" / Dashboard is empty
- **Cause:** Backend not running or wrong `NEXT_PUBLIC_API_URL`
- **Fix:**
  1. Verify backend is running: `curl http://localhost:8000/api/health`
  2. Check `frontend/.env.local`:
     ```ini
     NEXT_PUBLIC_API_URL=http://localhost:8000/api
     ```
  3. Hard refresh browser (Ctrl+Shift+R)

#### "Port 3000 already in use"
- **Fix (Windows PowerShell):**
  ```powershell
  $id = (Get-NetTCPConnection -LocalPort 3000).OwningProcess
  Stop-Process -Id $id -Force
  ```

#### "Cannot find module '@/components/ui/...'"
- **Cause:** Missing shadcn components
- **Fix:**
  ```bash
  npm install
  ```

#### Components not loading / Errors in console
- **Fix:** Clear Next.js cache and reinstall
  ```bash
  rm -r .next node_modules
  npm install
  npm run dev
  ```

### Network / CORS Issues

If you get CORS errors when the frontend calls the backend:

1. **Verify backend is running:** `curl http://localhost:8000/api/health`
2. **Check `CORS_ORIGINS` in `backend/.env`:**
   ```ini
   # Must include frontend URL
   CORS_ORIGINS=["http://localhost:3000"]
   ```
3. **Restart backend** after changing `.env`

---

## 9. Restarting Clean (Fresh Data)

To wipe all data and start fresh:

### Option A: Delete Database via MySQL CLI

```bash
# Connect to MySQL and drop the database
mysql -u root -p

# At the mysql> prompt:
mysql> DROP DATABASE IF EXISTS embedded_db;
mysql> EXIT;
```

Then restart the backend — it will recreate the database and seed data.

### Option B: Delete Database via PowerShell (Windows)

```powershell
mysql -u root -p -e "DROP DATABASE IF EXISTS embedded_db;"
```

### Option C: Manual Database Directory (Advanced)

```bash
# Find MySQL data directory (usually)
# Windows: C:\ProgramData\MySQL\MySQL Server 8.0\data\
# macOS: /usr/local/mysql/data/
# Linux: /var/lib/mysql/

# Delete the folder: rm -r <data_dir>/embedded_db
```

**After any of the above:**

```bash
# Restart backend (Terminal 1)
cd backend
python run.py
```

The backend will:
1. Detect missing `embedded_db`
2. Create it from scratch
3. Re-seed all attributes, test cases, and categories
4. Be ready for use immediately

---

## Quick Reference: First Run Checklist

- [ ] MySQL running and accessible (verify with `mysql -u root -p`)
- [ ] Python 3.11+ installed (`python --version`)
- [ ] Node.js 18+ installed (`node --version`)
- [ ] Backend virtual env created: `python -m venv .venv`
- [ ] Backend activated: `.venv\Scripts\Activate.ps1` (Windows) or `source .venv/bin/activate` (macOS/Linux)
- [ ] Backend dependencies installed: `pip install -r requirements.txt`
- [ ] Backend `.env` created and configured with MySQL credentials
- [ ] Backend running: `python run.py` (Terminal 1)
- [ ] Backend health check: `curl http://localhost:8000/api/health`
- [ ] Frontend dependencies installed: `npm install`
- [ ] Frontend `.env.local` created with `NEXT_PUBLIC_API_URL`
- [ ] Frontend running: `npm run dev` (Terminal 2)
- [ ] Dashboard loads at `http://localhost:3000`

---

## Need Help?

- **API Docs:** http://localhost:8000/docs (interactive Swagger UI)
- **Backend logs:** Check terminal where `python run.py` is running
- **Frontend logs:** Check browser console (F12 → Console tab)
- **Project docs:** See `docs/IMPLEMENTATION.md` for architecture details
