# dazuoagent frontend

React + TypeScript + Vite + Tailwind. Talks to the FastAPI backend through the Vite dev proxy (`/api` → `http://127.0.0.1:8000`).

## Run locally

```bash
cd frontend
npm install
npm run dev      # http://127.0.0.1:5173
```

Make sure the backend is running (`dazuoagent-api` in `backend/`) — otherwise the API client will hit 404s in the dev proxy.

## Layout

- `src/main.tsx` — ReactDOM root
- `src/router.tsx` — React Router (BrowserRouter); layout wraps every page
- `src/components/layout/` — Sidebar, TopBar, Layout shell
- `src/pages/` — Dashboard / ProjectList / ProjectDetail / DesignStudio / MaterialLibrary / QuotationView
- `src/components/floorplan/` — *to be added* Canvas/SVG floor-plan editor
- `src/components/design/` — *to be added* react-three-fiber 3D viewer
- `src/lib/api.ts` — typed Axios clients
- `src/types/` — wire-format types (mirror of backend Pydantic schemas)
- `src/stores/` — Zustand stores (currently `useAppStore`)

See [`../CLAUDE.md`](../CLAUDE.md) for the full architecture overview.