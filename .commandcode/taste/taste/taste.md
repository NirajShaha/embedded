# Taste
- Prefers a full-stack stack of Next.js (with shadcn/ui + Tailwind CSS) for the frontend and FastAPI + PostgreSQL for the backend. Confidence: 0.7
- Favors wizard/stepper-style multi-page flows (sequential pages, multi-select attributes, save-and-continue navigation) when building app UIs. Confidence: 0.6
- Communicates requirements at a high level and delegates architecture/implementation detail to the agent, expecting it to clarify ambiguities (e.g. page counts, seed content) before building. Confidence: 0.6
- Prefers dev infrastructure to be self-provisioning/auto-created (database, tables, and seed data created automatically on startup) rather than set up with manual steps. Confidence: 0.6
- Values fully reproducible, from-scratch setup on any machine — wants comprehensive setup documentation (prerequisites, per-app config, a root README quick-start, and troubleshooting for known issues) rather than relying on the developer's local state. Confidence: 0.6
- Works on Windows (PowerShell) and expects run/setup instructions in PowerShell/Windows form (e.g., `.venv\Scripts\Activate.ps1` for the backend virtualenv) rather than POSIX equivalents. Confidence: 0.6
- Values proper repository hygiene: wants a single comprehensive root-level `.gitignore` covering the whole application (Python/venv, Node/Next.js, env/secrets with `.env.example` kept, IDE, logs, OS junk) rather than relying only on scattered per-directory ignore files. Confidence: 0.5
