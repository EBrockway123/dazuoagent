# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

dazuoagent is a **whole-house custom furniture (全屋定制) agent platform**. Customers upload a floor plan, chat with an LLM-powered design assistant to lay out built-in furniture (wardrobes, kitchen cabinets, TV stands, …), browse a material library (board types + veneer finishes + hardware), and receive an itemised quotation.

The product is split into two top-level packages that talk over HTTP/JSON:

```
backend/   FastAPI + SQLAlchemy + LangChain agent (Python 3.11+)
frontend/  React + TypeScript + Vite + Tailwind + Zustand
```

## Repo layout

```
.
├── backend/                # Python service
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── src/dazuoagent/
│   │   ├── main.py         # FastAPI app factory; mounted at /api/v1 + /health
│   │   ├── core/           # settings, SQLAlchemy engine/session
│   │   ├── models/         # ORM (Material, Project, Room, Design, Furniture, Quotation, …)
│   │   ├── schemas/        # Pydantic request/response shapes
│   │   ├── api/v1/         # routers; aggregated by api/v1/router.py
│   │   ├── services/       # CRUD + pricing engine (quotation_service)
│   │   ├── agent/          # LLM agent (mock by default) + tools + prompts
│   │   └── db/seed.py      # sample materials
│   ├── tests/              # pytest smoke suite
│   └── README.md
├── frontend/               # React app
│   ├── package.json
│   ├── vite.config.ts      # /api → http://127.0.0.1:8000 dev proxy
│   ├── src/
│   │   ├── main.tsx        # ReactDOM root
│   │   ├── router.tsx      # React Router; every page wrapped by Layout
│   │   ├── components/layout/   # Sidebar, TopBar, Layout shell
│   │   ├── pages/          # Dashboard, ProjectList, ProjectDetail, DesignStudio, MaterialLibrary, QuotationView
│   │   ├── lib/api.ts      # typed Axios clients (materials/projects/designs/quotations/agents)
│   │   ├── stores/         # Zustand
│   │   └── types/          # wire-format types — mirror of backend Pydantic schemas
│   └── README.md
├── data/                   # runtime SQLite + uploaded floor plans (gitignored)
├── scripts/dev.{sh,ps1}    # launch backend + frontend together
├── docker-compose.yml
├── .env.example            # template; copy to backend/.env
└── README.md
```

## Layer rules

These are the conventions that keep the architecture readable — read them before adding code.

- **Backend routers stay thin.** Each router in [`backend/src/dazuoagent/api/v1/`](backend/src/dazuoagent/api/v1/) should only: (1) take request payload, (2) call into a `services/*` function, (3) return a Pydantic schema. No ORM access in routers; no business logic in services' call sites.
- **Services own transactions.** DB session lifecycle (`get_db`) is created in [`backend/src/dazuoagent/core/database.py`](backend/src/dazuoagent/core/database.py) and passed in. Services call `db.commit()` / `db.refresh()`. Routers never touch the session directly.
- **One declarative base, one registry.** Every ORM model imports `Base` from `dazuoagent.core.database`. `dazuoagent.models.__init__` re-exports each model so `Base.metadata.create_all` and Alembic autogenerate see them all.
- **ORM ↔ schema separation.** ORM models live in `models/`, Pydantic wire shapes in `schemas/`. The boundary is enforced via `model_config = ConfigDict(from_attributes=True)` on read schemas; service functions do the conversion.
- **Frontend API layer is the only network boundary.** Pages import from [`frontend/src/lib/api.ts`](frontend/src/lib/api.ts), never `axios` directly. Each domain (`materialsApi`, `projectsApi`, …) exposes typed methods.
- **Layout wraps every route.** [`frontend/src/router.tsx`](frontend/src/router.tsx) renders `<Layout>…</Layout>` around each page. New pages must NOT bring their own outer chrome.
- **Tailwind brand tokens.** Custom palette lives in [`frontend/tailwind.config.js`](frontend/tailwind.config.js) under `colors.brand`. Use `bg-brand-500`, `text-brand-700`, etc. — never hardcode hex outside `lib/utils.ts`.

## Domain model (high level)

| Model      | File                          | Purpose                                                     |
| ---------- | ----------------------------- | ----------------------------------------------------------- |
| Material   | `models/material.py`          | Board SKU + 五金; carries `price` + `unit`. Single table covers both boards and hardware via nullable `board_type` / `hardware_category`. |
| Project    | `models/project.py`           | Customer job + floor plan + rooms.                           |
| Room       | `models/project.py`           | Child of Project; width/length/area in mm + ㎡.             |
| Design     | `models/design.py`            | Furniture layout for a project. `is_final` marks the one used for quotation. |
| Furniture  | `models/design.py`            | Single built-in piece; references `material_id`.            |
| Quotation  | `models/quotation.py`         | Header (subtotal/labor/tax/total) + snapshot line items.    |

Quotation line items are **snapshots** — the pricing engine in [`backend/src/dazuoagent/services/quotation_service.py`](backend/src/dazuoagent/services/quotation_service.py) recomputes everything from the design on `POST /quotations/{id}/generate-from-design/{design_id}`. Don't mutate `QuotationLineItem` rows after issuance.

## The agent

The LLM agent is in [`backend/src/dazuoagent/agent/`](backend/src/dazuoagent/agent/):

- `agent.py` exposes `chat()` and `parse_floorplan()`. Both have a mock implementation; the real LangChain call is stubbed (raise `NotImplementedError`) until `settings.llm_provider` is flipped off `"mock"`.
- `tools.py` is the registry of Python functions the agent can call (currently `list_materials`, `get_project_rooms`).
- `prompts.py` holds the system prompts — change tone / behaviour there, not in code.

When wiring a real LLM: set `LLM_PROVIDER=openai` (or `anthropic`) in `.env`, fill in the API key, and replace `_langchain_chat()` in `agent/agent.py`. The HTTP contract in `api/v1/agents.py` does not change.

## Commands

```bash
# --- Backend ---
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -e ".[dev]"
python -m dazuoagent.db.seed                     # init SQLite + sample materials
dazuoagent-api                                   # → http://127.0.0.1:8000  (Swagger at /docs)
pytest                                           # run tests
ruff check .                                     # lint
ruff format .                                    # format

# --- Frontend ---
cd frontend
npm install
npm run dev                                      # → http://127.0.0.1:5173
npm run build                                    # production bundle into dist/
npm run lint

# --- Both at once ---
./scripts/dev.sh          # bash (Linux/macOS)
.\scripts\dev.ps1         # PowerShell (Windows)

# --- Docker ---
docker compose up --build  # backend on :8000, frontend on :5173
```

## Environment

All knobs are in [`backend/src/dazuoagent/core/config.py`](backend/src/dazuoagent/core/config.py) (Pydantic Settings). The template is [`.env.example`](.env.example) — copy to `backend/.env`. Most relevant:

- `LLM_PROVIDER` — `mock` | `openai` | `anthropic` (defaults to `mock`)
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` — provider keys
- `DATABASE_URL` — defaults to a SQLite file under `data/db/`; flip to `postgresql+psycopg://…` for prod
- `CORS_ORIGINS` — list; defaults include the Vite dev server

## Conventions worth knowing

- **Pydantic v2 only.** Don't import from `pydantic.BaseModel` v1 syntax; schemas use `model_config = ConfigDict(from_attributes=True)`.
- **Type hints on every public function.** `from __future__ import annotations` at the top of every backend file.
- **Single source of truth for tool config.** No `setup.cfg`, `tox.ini`, `ruff.toml`, `tsconfig.tsbuildinfo` — everything lives in `backend/pyproject.toml` and `frontend/tsconfig.json`/`vite.config.ts`.
- **Frontend path alias.** `@/` maps to `frontend/src/` (see `vite.config.ts` and `tsconfig.json`).
- **Generated SQLite is gitignored** — see top-level `.gitignore`. Re-run `python -m dazuoagent.db.seed` after pulling schema changes until Alembic lands.