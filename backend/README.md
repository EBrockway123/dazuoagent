# dazuoagent backend

FastAPI service for the whole-house custom furniture platform.

## Run locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"

# initialise DB + seed materials
python -m dazuoagent.db.seed

# start API (http://127.0.0.1:8000, docs at /docs)
dazuoagent-api
# or: uvicorn dazuoagent.main:app --reload
```

## Tests

```bash
pytest
```

## Layout

- `src/dazuoagent/main.py` — FastAPI app + CORS
- `src/dazuoagent/core/` — settings, SQLAlchemy session
- `src/dazuoagent/models/` — ORM (Material, Project, Design, Quotation, …)
- `src/dazuoagent/schemas/` — Pydantic request/response shapes
- `src/dazuoagent/api/v1/` — versioned HTTP routers
- `src/dazuoagent/services/` — business logic (CRUD + pricing engine)
- `src/dazuoagent/agent/` — LLM agent + tools + prompts
- `src/dazuoagent/db/seed.py` — sample data
- `tests/` — pytest suite

See [`../CLAUDE.md`](../CLAUDE.md) for the full architecture overview.