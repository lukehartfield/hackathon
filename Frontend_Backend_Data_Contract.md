# Frontend-Backend Data Contract

## Purpose
This file defines how the frontend should consume backend optimization outputs from:
- `ev_network_optimization.py` (classical)
- `ev_network_learning.py` (learning)

It includes exact field mappings and adapter rules so the UI reads the correct data points.

## Backend Output Files
Each pipeline run writes these files:
- `ranked_recommendations.csv`
- `scenario_summary.csv`
- `node_clusters.csv`
- `underserved_communities.csv`
- `recommendations.geojson`
- `clusters.geojson`

Learning pipeline also writes:
- `node_scores.csv`
- `model_metadata.json`

## Canonical Frontend Input Targets
For current web app, copy backend outputs into `web/public/data/`:
- `recommendations.geojson`
- `clusters.geojson`
- `ocm_austin.geojson` (already used by `/api/stations`)

Optional API/dashboard inputs:
- `scenario_summary.csv`
- `underserved_communities.csv`
- `node_scores.csv`
- `model_metadata.json`

## Field Mapping (Important)

### 1) Recommendations (`recommendations.geojson`)
Backend properties currently include:
- `site_id`
- `node_weight`
- `population_score`
- `marginal_demand_gain`
- `cumulative_coverage`

Frontend `Recommendation` type (`web/lib/types.ts`) expects:
- `lat`
- `lng`
- `site_id`
- `node_weight`
- `marginal_gain`

Adapter rule:
- `lat = geometry.coordinates[1]`
- `lng = geometry.coordinates[0]`
- `marginal_gain = properties.marginal_demand_gain` (fallback to `properties.marginal_gain` if present)

### 2) Clusters (`clusters.geojson`)
Backend properties include:
- `site_id`
- `community_id`
- `is_existing`
- `distance_to_nearest_existing_km`
- `node_weight`
- `population_score`

Frontend `ClusterFeature` expects:
- `lat`
- `lng`
- `community_id`
- `is_underserved`

Adapter rule:
- `lat = geometry.coordinates[1]`
- `lng = geometry.coordinates[0]`
- `community_id = properties.community_id`
- `is_underserved` is not on `clusters.geojson` directly; derive it by joining `community_id` against `underserved_communities.csv` where `underserved == true`.

### 3) Scenario Summary (`scenario_summary.csv`)
Columns:
- `stations_added`
- `selected_sites`
- `coverage_ratio`
- `aggregate_marginal_demand_gain`
- `baseline_coverage_ratio`
- `effective_service_radius_km`

Use for:
- KPI cards
- before/after coverage charts
- diagnostics display (radius tuning)

## Recommended Frontend Adapter Updates

### Update `parseRecommendations` in `web/lib/geojson.ts`
Use:
- `marginal_gain: Number(f.properties.marginal_demand_gain ?? f.properties.marginal_gain ?? 0)`

### Update `parseClusters` in `web/lib/geojson.ts`
Either:
- accept `is_underserved` when present, or
- inject it after joining with `underserved_communities.csv` by `community_id`.

## Minimal Integration Flow
1. Run backend pipeline (classical or learning).
2. Copy `recommendations.geojson` and `clusters.geojson` into `web/public/data/`.
3. If using underserved highlighting, also load `underserved_communities.csv` and join by `community_id`.
4. Keep frontend type contract stable (`marginal_gain`, `lat`, `lng`) via adapter layer only.

## Example Command Flow
```powershell
python ev_network_optimization.py --data-dir data --output-dir outputs_classical_npa
Copy-Item outputs_classical_npa\recommendations.geojson web\public\data\recommendations.geojson -Force
Copy-Item outputs_classical_npa\clusters.geojson web\public\data\clusters.geojson -Force
```

Use the same flow for learning outputs by replacing `outputs_classical_npa` with `outputs_learning_npa`.
