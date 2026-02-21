# Austin EV Data Pipeline — Setup & Execution

This document describes the data pipeline we executed to connect EV charging stations (OCM) with traffic and parking data for the Austin EV expansion optimization project.

## Overview

The pipeline pulls data from three sources and produces CSV files that feed `ev_network_optimization.py`:

- **EV Charging (Supply)** — Open Charge Map (OCM)
- **Traffic (Demand Proxy)** — City of Austin Open Data
- **Parking (Feasibility)** — City of Austin Open Data

## Prerequisites

1. **OCM Austin data** — Must exist at `data/ocm_austin.json`. Generate it with:
   ```bash
   # Requires OCM_API_KEY in .env or environment
   python scripts/fetch_ocm_austin.py
   ```

2. **Python 3** — No extra packages required (uses stdlib `json`, `urllib`, `csv`).

## Data Sources

| Source | City of Austin Dataset | Socrata ID | Fields Used |
|--------|------------------------|------------|-------------|
| Traffic | Real-Time Traffic Incident Reports | `dx9v-zd7x` | `latitude`, `longitude` |
| Parking | Parking Lot Entrances and Exits | `ij6a-fwpi` | `latitude`, `longitude`, `parking_lo` |
| EV Chargers | Open Charge Map API (pre-fetched) | — | `AddressInfo.Latitude/Longitude`, `Connections`, `OperatorInfo` |

All Austin Open Data endpoints are public; no API key is required.

## Execution Steps

### Step 1: Fetch OCM EV Charging Data (if not already done)

```bash
# Set OCM_API_KEY in .env, then:
python scripts/fetch_ocm_austin.py
```

Outputs:
- `data/ocm_austin.json`
- `data/ocm_austin.geojson`

### Step 2: Fetch Traffic & Parking + Build CSVs

```bash
python scripts/fetch_traffic_parking_austin.py
```

This script:

1. Loads OCM data from `data/ocm_austin.json`
2. Fetches traffic incidents from Austin Open Data (Socrata API)
3. Fetches parking lot entrances from Austin Open Data
4. Converts OCM records → `data/existing_stations.csv`
5. Builds candidates from parking lots with:
   - `traffic_score` — normalized count of traffic incidents within 2 km
   - `parking_score` — 100 (parking lots have high feasibility)
   - `demand_proxy` — incident density (high-traffic areas)

Outputs:
- `data/existing_stations.csv` (684 rows)
- `data/candidate_sites.csv` (173 rows)

### Step 3: Run EV Network Optimization

```bash
python ev_network_optimization.py --data-dir data --output-dir outputs
```

Outputs (in `outputs/`):
- `ranked_recommendations.csv`
- `scenario_summary.csv`
- `node_clusters.csv`
- `underserved_communities.csv`
- `recommendations.geojson`
- `clusters.geojson`

## Sample Run Results (What We Executed)

```
=== Austin EV Data ETL: OCM + Traffic + Parking ===

Fetching traffic incidents (Austin Open Data)...
  -> 9808 incidents in Austin bbox
Fetching parking lot entrances (Austin Open Data)...
  -> 173 parking locations in Austin bbox
Wrote 684 rows to data/existing_stations.csv
Wrote 173 rows to data/candidate_sites.csv

Done. Run: python ev_network_optimization.py --data-dir data --output-dir outputs
```

```
=== EV Charging Expansion Results (Austin) ===
Nodes in graph: 857
Edges in graph: 59286

Scenario summary:
  add=10 | selected=10 | coverage=1.000 | demand_gain=0.000
  add=25 | selected=25 | coverage=1.000 | demand_gain=0.000
  add=50 | selected=50 | coverage=1.000 | demand_gain=0.000

Top 10 recommendations:
   1. PK_651 | weight=0.601 | marginal_gain=0.000 | coverage=1.000
   2. PK_384 | weight=0.519 | marginal_gain=0.000 | coverage=1.000
   ...

Underserved communities found: 0
Output directory: /Users/shruthisubramanian/Downloads/hackathon/outputs
```

## File Layout After Execution

```
hackathon/
├── data/
│   ├── ocm_austin.json          # OCM EV stations (from fetch_ocm_austin.py)
│   ├── ocm_austin.geojson
│   ├── existing_stations.csv    # OCM → optimization format
│   └── candidate_sites.csv     # Parking + traffic scores
├── outputs/
│   ├── ranked_recommendations.csv
│   ├── scenario_summary.csv
│   ├── node_clusters.csv
│   ├── underserved_communities.csv
│   ├── recommendations.geojson
│   └── clusters.geojson
├── scripts/
│   ├── fetch_ocm_austin.py       # Pull OCM data
│   └── fetch_traffic_parking_austin.py  # Pull traffic + parking, build CSVs
├── ev_network_optimization.py    # Graph optimization pipeline
└── Data_Pipeline_Setup.md        # This file
```

## Logic Summary

- **Existing stations** are OCM EV charging sites within Austin’s approximate bounding box.
- **Candidates** are Austin parking lot entrances; each gets a traffic-based score from nearby incident density.
- **Traffic incidents** serve as a demand proxy: more incidents ≈ more traffic ≈ higher demand for charging.
- The optimization pipeline uses these CSVs to rank expansion locations and detect underserved communities.
