# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

ChargePilot — an EV charging network optimizer for Austin, TX. Combines real Open Charge Map station data (684 stations, already fetched) with simulated demand scoring and a Python graph optimization pipeline to recommend where to expand charging infrastructure. Delivered as a Next.js map application.

## Stack

- **Frontend:** Next.js 14 (App Router, TypeScript), react-leaflet, leaflet.heat, Tailwind CSS
- **AI:** Groq SDK (key in `.env` as `GROQ_API_KEY`)
- **Data pipeline:** Python (`scripts/`, `ev_network_optimization.py`)
- **OCM data:** `data/ocm_austin.json` + `data/ocm_austin.geojson` (pre-fetched, 684 stations)

## Commands

```bash
# Install dependencies
npm install

# Dev server
npm run dev

# Build
npm run build

# Re-fetch OCM data (requires OCM_API_KEY in .env)
py scripts/fetch_ocm_austin.py

# Run optimization pipeline
py ev_network_optimization.py --data-dir data --output-dir outputs
```

## Architecture

### Data flow

```
Python pipeline → outputs/*.geojson/csv → public/data/ → Next.js frontend
OCM API        → data/ocm_austin.geojson → public/data/
```

The Python script runs **offline before the demo**. Its outputs are static files served from `public/data/`. The frontend never executes Python at runtime.

### Key output files (Python → frontend)

| File | Used by |
|---|---|
| `outputs/recommendations.geojson` | Nodes tab + AI tab (suggested new sites) |
| `outputs/clusters.geojson` | AI tab (community cluster shading) |
| `outputs/ranked_recommendations.csv` | Groq prompt context |
| `outputs/scenario_summary.csv` | AI tab scenario selector |

### Frontend structure

- `app/page.tsx` — root layout, two-column (map 70% / panel 30%)
- `app/api/stations/route.ts` — enriches OCM GeoJSON with utilization scores
- `app/api/insights/route.ts` — calls Groq server-side, streams narrative
- `components/MapView.tsx` — Leaflet map, swaps layers based on `activeTab`
- `components/tabs/` — one component per tab (Overview, Congestion, Nodes, AIInsights)
- `lib/scoring.ts` — derives charger count + simulates utilization
- `lib/geojson.ts` — loads static GeoJSON from `public/data/`

### Tabs → map layer mapping

| Tab | Map layers active |
|---|---|
| Overview | Colored station dots |
| Congestion | Dots + demand/gap heatmap |
| Nodes | Dots + blue suggested sites |
| AI Insights | Dots + cluster shading + suggested sites |

### Charger count quirk

`NumberOfPoints` is null on ~94% of OCM records. Always derive charger count as:
```ts
station.NumberOfPoints ?? station.Connections?.reduce((sum, c) => sum + (c.Quantity ?? 1), 0) ?? 1
```

### Utilization simulation

```ts
const utilization = (trafficScore * 100) / chargerCount;
// > 150% → overloaded (#ef4444), 60–150% → balanced (#f59e0b), < 60% → underutilized (#22c55e)
```

### "Run Optimization" button flow

1. 2–3s "Computing..." spinner
2. Animate map (blue dots appear, overloaded nodes pulse)
3. POST `/api/insights` → stream Groq narrative into AI tab
4. Auto-switch to AI Insights tab

## Environment variables

```
OCM_API_KEY=       # Open Charge Map (only needed to re-fetch data)
GROQ_API_KEY=      # Required at runtime for AI Insights tab
```

## Design docs

See `docs/plans/2026-02-20-frontend-design.md` for full frontend design with layout diagrams, color system, and component architecture.
