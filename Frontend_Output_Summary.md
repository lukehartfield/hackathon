# Frontend Output Summary (Recommended Dataset)

## Recommended Output Set
Use: `outputs_run_gnn_gat/`

Reason: among the latest model runs, this set produced the most spatially spread top-10 new-node recommendations (best geographic coverage feel for demo maps).

## Spread Check (Top 10)
Compared by average nearest-neighbor distance (km) for top-10 recommended nodes:
- `outputs_run_classical`: `3.164`
- `outputs_run_learning`: `3.122`
- `outputs_run_gnn_gcn`: `3.187`
- `outputs_run_gnn_graphsage`: `3.122`
- `outputs_run_gnn_gat`: `3.251`  <- best spread

## Files Frontend Should Consume
From `outputs_run_gnn_gat/`:
- `recommendations.geojson` (new node candidates)
- `clusters.geojson` (community cluster visualization)
- `ranked_recommendations.csv` (table/list panel)
- `scenario_summary.csv` (KPI cards/charts)
- `underserved_communities.csv` (underserved overlay/join)

Optional:
- `node_scores.csv` (debug/model score table)
- `model_metadata.json` (show model config in dev/admin panel)

## Field Notes for Frontend
- Recommendation gain field is `marginal_demand_gain`.
- Frontend adapter maps it to `marginal_gain` in `web/lib/geojson.ts`.
- Coordinates come from GeoJSON geometry:
  - `lat = coordinates[1]`
  - `lng = coordinates[0]`

## Copy Commands (PowerShell)
```powershell
Copy-Item outputs_run_gnn_gat\recommendations.geojson web\public\data\recommendations.geojson -Force
Copy-Item outputs_run_gnn_gat\clusters.geojson web\public\data\clusters.geojson -Force
Copy-Item outputs_run_gnn_gat\ranked_recommendations.csv web\public\data\ranked_recommendations.csv -Force
Copy-Item outputs_run_gnn_gat\scenario_summary.csv web\public\data\scenario_summary.csv -Force
Copy-Item outputs_run_gnn_gat\underserved_communities.csv web\public\data\underserved_communities.csv -Force
```

## If You Need Conservative/Stable Alternative
Use `outputs_run_classical/` as fallback baseline with similar node choices and simpler explainability.
