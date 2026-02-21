# EV Network Optimization Script Context

## Purpose
`ev_network_optimization.py` is a hackathon-ready optimization pipeline for EV charging expansion in Austin, TX.

It converts scraped EV/traffic/parking signals into a weighted candidate graph, recommends expansion nodes, detects communities, and exports files for mapping and downstream app integration.

## Core Assumptions
- Phase-1 geography is Austin, Texas.
- Existing and candidate location records are available from scraped API data.
- If real CSVs are missing, the script uses deterministic placeholder Austin data for demo continuity.
- Candidate quality can be represented by a weighted feature vector:
  - `traffic_score`
  - `parking_score`
  - `charger_gap_score`
  - `distance_to_nearest_existing`
  - `demand_proxy`
- A greedy expansion strategy is acceptable for MVP budget scenarios (10/25/50 stations).
- Community detection is approximated using connected components on a proximity graph for a dependency-light MVP.

## Input Contract
Optional input directory: `data/`

If present, script reads:
- `data/existing_stations.csv`
- `data/candidate_sites.csv`

### `existing_stations.csv` required columns
- `site_id`
- `lat`
- `lon`

Optional columns:
- `charger_count`
- `charger_type`
- `network`

### `candidate_sites.csv` required columns
- `site_id`
- `lat`
- `lon`
- `traffic_score`
- `parking_score`
- `demand_proxy`

## Runtime Parameters
Supported CLI args:
- `--data-dir` (default `data`)
- `--output-dir` (default `outputs`)
- `--edge-radius-km` (default `3.0`)
- `--service-radius-km` (default `2.5`)
- `--density-radius-km` (default `2.0`)
- `--underserved-distance-km` (default `2.2`)

Example:
```bash
python ev_network_optimization.py --data-dir data --output-dir outputs
```

## Output Contract
The script writes these artifacts to `outputs/`:
- `ranked_recommendations.csv`
  - Ranked candidate nodes with `node_weight`, marginal demand gain, and cumulative coverage.
- `scenario_summary.csv`
  - Scenario metrics for adding 10, 25, and 50 stations.
- `node_clusters.csv`
  - Node-level community assignments and nearest-existing-station distance.
- `underserved_communities.csv`
  - Community-level summary and underserved flag.
- `recommendations.geojson`
  - Point features for recommended expansion sites.
- `clusters.geojson`
  - Point features for all nodes with community metadata.

## Integration Notes
- Map UI can ingest `recommendations.geojson` and `clusters.geojson` directly.
- Backend services can consume CSVs for dashboards or APIs.
- Recommended site IDs in `ranked_recommendations.csv` are stable join keys for linking back to source records.

## Known MVP Limitations
- Uses simplified graph/community logic to minimize dependencies.
- Optimization is greedy and heuristic, not globally optimal.
- Placeholder data is synthetic and should be replaced with production API pulls.

## Suggested Next Build Steps
1. Replace placeholder fallback with validated ETL from EV + traffic + parking APIs.
2. Add time-of-day feature slices and scenario comparisons.
3. Add equity/fairness constraints in the objective function.
4. Swap connected-components clustering for modularity/Louvain when dependency stack is stabilized.
5. Expose outputs through a lightweight API for frontend consumption.
