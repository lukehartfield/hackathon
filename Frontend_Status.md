# Frontend Status

## Current State

A Next.js 14 app (`web/`) that renders all 684 Austin EV charging stations on an interactive dark-themed map.

**What works right now:**
- Full-screen Leaflet map centered on Austin (30.2672, -97.7431)
- CartoDB Dark Matter tile layer (free, no API key)
- 684 green circle markers, one per station from Open Charge Map data
- Hover tooltip on each marker showing station name and charger count
- Charger count derived from `Connections[].Quantity` when `NumberOfPoints` is null (which is 93% of records)

**Run it:**
```bash
cd web
npm run dev
# Open http://localhost:3000
```

## Stack

- Next.js 14 (App Router, TypeScript)
- Leaflet (via `leaflet` + `react-leaflet@4`)
- Tailwind CSS
- Groq SDK (installed, not yet active)

## Files in Use

| File | Purpose |
|---|---|
| `app/page.tsx` | Loads OCM GeoJSON, passes stations to MapView |
| `app/layout.tsx` | Dark full-height shell |
| `components/MapView.tsx` | Leaflet map, renders station dots with tooltips |

## Files Built but Not Yet Active

These were built for the full tabbed UI and will be wired in when we add features:

| File | Purpose |
|---|---|
| `components/TabPanel.tsx` | Tab switcher (Overview, Congestion, Nodes, AI) |
| `components/tabs/OverviewTab.tsx` | Summary stats: total, avg utilization, status bars |
| `components/tabs/CongestionTab.tsx` | Top 15 most congested stations ranked list |
| `components/tabs/NodesTab.tsx` | Suggested new sites ranked by network impact |
| `components/tabs/AITab.tsx` | Groq narrative + before/after coverage score |
| `lib/types.ts` | TypeScript interfaces for stations, recommendations, clusters |
| `lib/scoring.ts` | Charger count derivation, utilization simulation, traffic scoring |
| `lib/geojson.ts` | GeoJSON parsers for OCM, recommendations, and clusters |
| `app/api/stations/route.ts` | Enriches OCM data with simulated utilization scores |
| `app/api/insights/route.ts` | Calls Groq for AI optimization narrative |
| `types/leaflet-heat.d.ts` | Type declarations for leaflet.heat plugin |

## Static Data Files (in `public/data/`)

| File | Records | Source |
|---|---|---|
| `ocm_austin.geojson` | 684 stations | Open Charge Map API |
| `recommendations.geojson` | 50 sites | Python optimizer output |
| `clusters.geojson` | 148 nodes | Python community detection |
| `ranked_recommendations.json` | 50 ranked | Converted from CSV |

## What's Next

Planned features to layer on:
1. Color-code stations by utilization (green/yellow/red)
2. Congestion heatmap overlay
3. Suggested new station locations (blue dots)
4. Tabbed side panel with stats and rankings
5. AI Insights tab with Groq-generated narrative
6. "Run Optimization" button with animated reveal
7. Community cluster shading
8. Time-of-day demand slider (stretch)

## Environment

```
GROQ_API_KEY=  # Set in web/.env.local — required for AI Insights tab
```
