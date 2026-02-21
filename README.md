# ChargePilot

**Graph-optimized EV charging expansion for Austin, TX.**

Built for the TVG x c0mpiled Hackathon at UT Austin.

---

## The Problem

Austin is one of the fastest-growing cities in the U.S. EV adoption is accelerating, but charging infrastructure placement still relies on incomplete data -- operators lack visibility into traffic flow, parking feasibility, and neighborhood-level coverage gaps. The result: overloaded stations in some corridors, dead zones in others, and no systematic way to decide where the next charger should go.

ChargePilot fixes this. We ingest real urban data, model the charging network as a weighted graph, learn node-level expansion scores, and output a ranked list of where to build next -- backed by numbers, not guesswork.

---

## Data Sources

All data is real and pulled from public APIs. No synthetic datasets in production.

| Source | Records | Role | API |
|--------|---------|------|-----|
| Open Charge Map (OCM) | 684 stations | Supply layer -- existing charger locations, capacity, operator, connector types | OCM REST API |
| Austin Traffic Incidents | 9,808 records | Demand proxy -- high-incident corridors signal high vehicle throughput | City of Austin Socrata (`dx9v-zd7x`) |
| Austin Parking Lot Entrances | 173 locations | Site feasibility -- parking lots are buildable candidate sites | City of Austin Socrata (`ij6a-fwpi`) |
| ACS 2023 Block-Group Population | 1,297 block groups | Neighborhood demand -- population assigned to planning areas | U.S. Census Bureau ACS |
| Austin NPA Boundaries | 54 planning areas | Spatial aggregation -- neighborhood polygons for coverage analysis | City of Austin Open Data |
| Radar Traffic Volumes | 10 intersections | Flow confirmation -- average vehicle counts at key intersections | City of Austin Socrata |
| Census Tract Data | 268 tracts | Demographics -- population, housing units, area for density modeling | U.S. Census Bureau |

---

## Data Pipeline

Three ETL scripts pull, clean, and normalize the raw data into CSVs and GeoJSON that feed the optimization engine.

```
fetch_ocm_austin.py          --> ocm_austin.json, ocm_austin.geojson
fetch_traffic_parking_austin.py --> existing_stations.csv, candidate_sites.csv
fetch_austin_demographics.py --> austin_npa_population.csv, austin_npa.geojson
```

Each candidate site is assigned a five-dimensional feature vector:

- `traffic_score` -- normalized count of traffic incidents within 2 km
- `parking_score` -- parking lot feasibility signal
- `charger_gap_score` -- inverse of existing charger density nearby
- `distance_to_nearest_existing` -- how far the nearest charger is
- `demand_proxy` -- incident density as a throughput estimate

All features are min-max scaled to [0, 1] before scoring.

---

## ML Algorithm -- Graph Neural Scoring

The model (`ev_network_learning.py`) uses a formal learned pipeline: feature weights are not fixed; they are estimated from data and then propagated through the graph. The result behaves like a neural network with dynamic weights.

1. **Linear Layer (Ridge Regression)** -- A learned weight vector maps the five input features to a scalar score. Weights are fit via ridge regression on proxy targets (traffic + demand composite or historical utilization when available). No hand-tuned coefficients; all weights are data-driven. Regularization (lambda = 0.05) prevents overfitting.

2. **Proximity Graph** -- Candidates are nodes; edges connect nodes within 3 km. Edge weights are learned from geometry: `affinity = 1 / (distance + 0.05)`. The graph adjacency defines the structure for the next stage.

3. **Graph Message-Passing Layers** -- Each node updates its score by aggregating from its neighbors:
   ```
   score[node] = alpha * score[node] + (1 - alpha) * weighted_neighbor_mean
   ```
   With alpha = 0.70 and 2 iterations, this acts like message-passing layers in a GAT (Graph Attention Network). The effective attention weights over neighbors are distance-based. High-demand clusters reinforce each other; the final score is context-aware.

4. **Output Normalization** -- Smoothed scores are min-max normalized to produce `learned_node_score` per candidate.

A classical baseline (`ev_network_optimization.py`) exists for comparison but uses fixed heuristics; the primary model is the learning pipeline with dynamic weights.

---

## Optimization -- Greedy Facility Expansion

Given a budget (10, 25, or 50 new stations), the optimizer runs a greedy facility location algorithm:

- At each step, select the candidate that maximizes:
  ```
  value = marginal_demand_covered * (0.7 + 0.3 * learned_node_score)
  ```
- `marginal_demand_covered` is the sum of `demand_weight` for all uncovered candidates brought within the service radius by placing this station.
- The service radius is auto-tuned to prevent trivial 100% coverage in dense areas.
- After selection, update coverage and repeat.

Community detection via connected components on the full graph (existing + candidates) identifies natural mobility clusters and flags underserved communities -- areas with high demand scores but no existing stations nearby.

---

## Outputs

The pipeline produces these artifacts:

| File | Description |
|------|-------------|
| `ranked_recommendations.csv` | Top candidates ranked by learned score and marginal demand gain |
| `scenario_summary.csv` | Coverage and demand metrics for 10/25/50 station scenarios |
| `node_clusters.csv` | Every node with community assignment and distance to nearest existing station |
| `underserved_communities.csv` | Communities flagged as underserved (high demand, low supply) |
| `recommendations.geojson` | Recommended expansion sites for map rendering |
| `clusters.geojson` | All nodes with cluster metadata for map rendering |
| `model_metadata.json` | Learned weights, model config, training target source |
| `node_scores.csv` | Per-site comparison of base learned score vs. graph-smoothed score |

---

## Frontend -- ChargePilot Dashboard

A Next.js 14 app renders the full network on an interactive dark-themed Leaflet map.

- **Overview tab** -- 684 stations color-coded by utilization (red/yellow/green), summary stats
- **Congestion tab** -- Demand heatmap overlay, top 15 most-loaded stations
- **Nodes tab** -- Recommended new sites as blue markers, ranked by network impact
- **AI Insights tab** -- Groq-powered executive narrative comparing before/after coverage

```bash
cd web && npm install && npm run dev
# Open http://localhost:3000
```

### Frontend-Backend Data Contract

The frontend consumes backend outputs from `web/public/data/`. Copy pipeline outputs before running the app.

| Backend file | Frontend target | Purpose |
|--------------|-----------------|---------|
| `recommendations.geojson` | `web/public/data/recommendations.geojson` | Suggested expansion sites |
| `clusters.geojson` | `web/public/data/clusters.geojson` | Node clusters, community metadata |
| `ocm_austin.geojson` | `web/public/data/ocm_austin.geojson` | Station layer (used by `/api/stations`) |
| `underserved_communities.csv` | Optional | Join by `community_id` to derive `is_underserved` for cluster highlighting |

**Field mappings:**
- `recommendations.geojson`: `lat/lng` from geometry; `marginal_gain` = `marginal_demand_gain`
- `clusters.geojson`: `is_underserved` is not stored; derive it by joining `community_id` with `underserved_communities.csv` where `underserved == true`

**Integration flow:**
1. Run the optimization pipeline (classical or learning).
2. Copy `recommendations.geojson` and `clusters.geojson` into `web/public/data/`.
3. For underserved highlighting, load `underserved_communities.csv` and join by `community_id`.

```bash
# Example: copy learning pipeline outputs into frontend
cp outputs/recommendations.geojson web/public/data/recommendations.geojson
cp outputs/clusters.geojson web/public/data/clusters.geojson
```

---

## Built with Morph (c0mpiled / Transpose Platform)

ChargePilot was built using Morph MCP integration inside Cursor IDE, provided by c0mpiled (Transpose Platform) -- the hackathon's tooling sponsor.

Two Morph-powered tools were used throughout the build:

- **WarpGrep** (`warpgrep_codebase_search`) -- An AI-powered codebase search subagent that ran parallel grep and file reads across the project. Used to navigate the data pipeline, locate optimization logic, trace feature flows, and inform edits across all scripts and frontend components.

- **edit_file** -- A high-speed file editing tool that enabled rapid iteration on Python scripts and TypeScript components without reading entire files into context.

These tools accelerated development velocity: the full data pipeline, graph optimization engine, learning model, and interactive frontend were built and iterated on within a single hackathon session using Morph's agentic coding workflow.

---

## How to Run

### 1. Fetch data

```bash
# Set OCM_API_KEY in .env
python scripts/fetch_ocm_austin.py
python scripts/fetch_traffic_parking_austin.py
python scripts/fetch_austin_demographics.py
```

### 2. Run optimization

```bash
# Learning pipeline (graph neural scoring, recommended)
python ev_network_learning.py --data-dir data --output-dir outputs

# Classical baseline (fixed heuristics)
python ev_network_optimization.py --data-dir data --output-dir outputs
```

### 3. Copy outputs to frontend

```bash
cp outputs/recommendations.geojson web/public/data/recommendations.geojson
cp outputs/clusters.geojson web/public/data/clusters.geojson
```

### 4. Launch frontend

```bash
cd web
npm install
npm run dev
```

### Environment variables

```
OCM_API_KEY=       # Open Charge Map (needed for data fetch)
GROQ_API_KEY=      # Groq (needed for AI Insights tab)
```

---

## Repository Structure

```
hackathon/
├── data/                        # Raw and processed datasets
│   ├── ocm_austin.json          # 684 EV stations from OCM
│   ├── ocm_austin.geojson       # Same, as GeoJSON
│   ├── existing_stations.csv    # Stations formatted for optimizer
│   ├── candidate_sites.csv      # Parking-based candidates with scores
│   ├── austin_npa.geojson       # Neighborhood planning area boundaries
│   ├── austin_npa_population.csv
│   ├── austin_blockgroup_population.csv
│   ├── census_tracts_austin.csv
│   ├── traffic_incidents_austin.csv
│   └── radar_volumes_austin.csv
├── scripts/
│   ├── fetch_ocm_austin.py      # OCM data pull
│   ├── fetch_traffic_parking_austin.py  # Traffic + parking + census ETL
│   └── fetch_austin_demographics.py     # NPA population estimates
├── ev_network_learning.py       # Primary: learned weights, graph message passing
├── ev_network_optimization.py   # Baseline: fixed heuristics
├── web/                         # Next.js frontend
│   ├── app/                     # Pages and API routes
│   ├── components/              # MapView, TabPanel, tab components
│   └── lib/                     # Types, scoring, GeoJSON loaders
└── outputs/                     # Pipeline artifacts (CSV, GeoJSON)
```

---

## Team

Built at the TVG x c0mpiled Hackathon, UT Austin, 2026.
