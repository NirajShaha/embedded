# Embedded Config App

A comprehensive full-stack application for managing ECU (Electronic Control Unit) configurations and security testing. Built with **Next.js + shadcn/ui + Tailwind** frontend and a **FastAPI + MySQL** backend.

## Features

- **Project Management**: Create and manage embedded systems projects with name and description
- **ECU Details**: Store and manage detailed ECU specifications including:
  - ECU name, part number, and risk rating
  - Architecture, vehicle line, and year
  - Microcontroller/CPU provider details
  - Availability dates for hardware, harness, and production software
  - Export control classification
  - Penetration testing provider information
- **Test Cases Dashboard**: View and filter security test cases by:
  - Category (threat categories)
  - Test type (automated, manual, etc.)
  - Interactive expandable rows with full test case details
- **Configuration Wizard**: Multi-step attribute selection pages for detailed project configuration
- **Full MySQL Integration**: All data persisted with proper relationships and constraints

## Quick start

```bash
# Backend (terminal 1)
cd backend
python -m venv .venv
pip install -r requirements.txt
cp .env.example .env        # then set your MySQL user/password in .env
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

## API Endpoints

### Projects

- `GET /api/projects` - List all projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Get project details

### ECU Details

- `GET /api/projects/{projectId}/ecu-detail` - Get ECU details for project
- `POST /api/projects/{projectId}/ecu-detail` - Create ECU details
- `PUT /api/projects/{projectId}/ecu-detail` - Update ECU details

### Test Cases

- `GET /api/test-cases/categories` - List test categories
- `GET /api/test-cases/types` - List test types
- `GET /api/test-cases?category_id=X&test_type_id=Y` - List filtered test cases
- `GET /api/test-cases/{id}` - Get test case details

### Configuration

- `GET /api/pages/{page}/attributes` - Get attribute groups for a page
- `GET /api/projects/{projectId}/page/{page}/selections` - Get user selections for a page
- `PUT /api/projects/{projectId}/page/{page}/selections` - Update selections

## Stack

- **Frontend:** Next.js 16, TypeScript, Tailwind CSS v4, shadcn/ui, React Query
- **Backend:** FastAPI, SQLAlchemy 2.0 (async), aiomysql, MySQL 8.0+
