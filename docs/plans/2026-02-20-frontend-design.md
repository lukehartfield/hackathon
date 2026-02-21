# Frontend Design — ChargePilot EV Network Optimizer

**Date:** 2026-02-20
**Stack:** Next.js 14 (App Router, TypeScript) · react-leaflet · leaflet.heat · Tailwind CSS · Groq SDK

---

## Overview

A single-page map application that visualizes Austin's EV charging network, surfaces congestion gaps via a demand heatmap, and presents AI-generated expansion recommendations. The Python optimization script (`ev_network_optimization.py`) runs offline and its GeoJSON outputs are served as static files. The frontend consumes real OCM data (684 Austin stations, already fetched) plus pre-computed optimization outputs.

---

## Layout

Full-viewport two-column layout:

- **Left (~70%):** Leaflet map, full height, dark CartoDB tiles
- **Right (~30%):** Fixed panel — tab switcher at top, tab content below, legend bar at bottom

```
┌────────────────────────────────┬──────────────────────────┐
│                                │ [Overview][Congestion]   │
│         LEAFLET MAP            │ [Nodes][AI Insights]     │
│                                │ ─────────────────────── │
│  (layers shift per active tab) │  <tab content>           │
│                                │                          │
│                                │ ─────────────────────── │
│                                │  [▶ RUN OPTIMIZATION]    │
└────────────────────────────────┴──────────────────────────┘
│  ● Overloaded  ● Balanced  ● Underutilized  ◉ Suggested   │
└───────────────────────────────────────────────────────────┘
```

---

## Tabs

Each tab controls both the panel content and which map layers are visible.

### Overview
- **Map:** 684 station dots colored by utilization status
- **Panel:** Summary stats — total stations, coverage %, avg utilization, overloaded count

### Congestion
- **Map:** Station dots + demand/gap heatmap overlay
- **Panel:** Ranked list of stations by congestion score (highest first)

### Nodes
- **Map:** Existing stations + suggested new sites as pulsing blue dots
- **Panel:** Ranked suggested nodes with expected coverage gain per node

### AI Insights
- **Map:** Community cluster shading + recommended sites
- **Panel:** Groq-generated narrative, before/after coverage score (e.g. 67% → 89%), scenario selector (add 10 / 25 / 50 stations)

---

## Color System

| Status | Color | Hex | Trigger |
|---|---|---|---|
| Overloaded | Red | `#ef4444` | utilization > 150% |
| Balanced | Yellow | `#f59e0b` | utilization 60–150% |
| Underutilized | Green | `#22c55e` | utilization < 60% |
| Suggested | Blue (pulsing) | `#3b82f6` | from recommendations.geojson |

Map theme: CartoDB Dark Matter (free, no API key).

---

## Map Layers per Tab

| Layer | Overview | Congestion | Nodes | AI |
|---|---|---|---|---|
| Colored station dots | ✓ | ✓ | ✓ | ✓ |
| Gap/demand heatmap | — | ✓ | — | — |
| Suggested nodes (blue) | — | — | ✓ | ✓ |
| Community cluster shading | — | — | — | ✓ |

---

## Component Structure

```
app/
├── page.tsx                    # Root layout shell
├── api/
│   ├── stations/route.ts       # Enriches OCM GeoJSON, returns scored stations
│   └── insights/route.ts       # Calls Groq, streams narrative response
├── components/
│   ├── MapView.tsx             # Leaflet map; accepts activeTab, swaps layers
│   ├── TabPanel.tsx            # Tab bar + panel content router
│   ├── tabs/
│   │   ├── OverviewTab.tsx
│   │   ├── CongestionTab.tsx
│   │   ├── NodesTab.tsx
│   │   └── AITab.tsx
│   └── RunButton.tsx           # Triggers animation + Groq call
└── lib/
    ├── scoring.ts              # Derives charger count, simulates utilization
    └── geojson.ts              # Loads static GeoJSON from public/data/
```

---

## Data Flow

### Static files (pre-computed, copied to `public/data/`)
- `public/data/ocm_austin.geojson` — 684 real Austin stations
- `public/data/recommendations.geojson` — Python optimizer output
- `public/data/clusters.geojson` — community detection output

### On page load
1. Fetch `ocm_austin.geojson` → enrich each station via `scoring.ts` → set state
2. Load `recommendations.geojson` + `clusters.geojson` for Nodes/AI tabs

### Charger count derivation (NumberOfPoints is null on 643/684 stations)
```ts
const chargerCount = station.NumberOfPoints
  ?? station.Connections?.reduce((sum, c) => sum + (c.Quantity ?? 1), 0)
  ?? 1;
```

### Utilization simulation
```ts
const utilization = (trafficScore * 100) / chargerCount;
const status = utilization > 150 ? "overloaded"
             : utilization > 60  ? "balanced"
             : "underutilized";
```

### "Run Optimization" button
1. Show "Computing..." spinner (2–3s)
2. Animate map — new blue dots appear, overloaded dots pulse
3. POST to `/api/insights` → stream Groq narrative into AI tab
4. Switch to AI Insights tab automatically

### Groq API route
- Called server-side from `/api/insights/route.ts` (keeps key out of browser)
- Input: top 10 recommendations from `ranked_recommendations.csv`
- Output: streamed narrative referencing real Austin neighborhoods

---

## Key Dependencies

```json
{
  "next": "14",
  "react-leaflet": "^4",
  "leaflet": "^1.9",
  "leaflet.heat": "^0.2",
  "@types/leaflet": "^1.9",
  "groq-sdk": "latest",
  "tailwindcss": "^3",
  "papaparse": "^5"
}
```

---

## Out of Scope (MVP)

- Live Python script execution (pre-computed outputs used instead)
- TomTom Traffic API (traffic score simulated from population density proxy)
- Time-of-day slider (stretch goal)
- Equity-aware prioritization (stretch goal)
