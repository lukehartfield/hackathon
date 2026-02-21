# EV Network GNN Pipeline Context

## Purpose
`ev_network_gnn.py` is a graph-neural-network substitute pipeline for EV charging expansion in Austin, TX.

It preserves the same backend input/output contract as the existing classical and lightweight-learning scripts, but replaces node scoring with GNN-based learning.

## Models Supported
Select model with `--model`:
- `gcn`
- `graphsage`
- `gat`

## Input Contract
Default data directory: `data/`

Required for real run:
- `data/existing_stations.csv`

Preferred candidate source:
- `data/austin_npa.geojson`
  - uses NPA polygon centroids as candidate nodes
  - uses `population` property to derive `population_score`

Fallback candidate source:
- `data/candidate_sites.csv`

Fallback if missing data:
- deterministic synthetic placeholders

## Feature Engineering
Per candidate node, script computes:
- `traffic_score` (synthetic from population for NPA mode)
- `parking_score` (synthetic from population for NPA mode)
- `demand_proxy` (synthetic from population for NPA mode)
- `distance_to_nearest_existing`
- `charger_gap_score` (inverse local existing density)

Node feature vector used by GNN:
- `[traffic_score, parking_score, charger_gap_score, distance_to_nearest_existing, demand_proxy]`

## Learning Target
Training target is selected in this order if available:
1. `target_impact`
2. `historical_sessions`
3. `utilization`
4. proxy target (feature-based weighted blend)

The target is min-max normalized for training.

## Graph Construction
- Candidate-only adjacency is built with geospatial threshold (`--edge-radius-km`, default `3.0` km).
- Self-loops are included.
- Full graph (existing + candidate) is used for community metrics output.

## Optimization Stage
After GNN scoring:
- `learned_node_score` is assigned to each candidate.
- Greedy facility expansion selects nodes for scenario budgets `10/25/50`.
- Service radius is adaptively tuned if baseline coverage is saturated.

## Output Contract
Outputs match existing pipeline contract and can feed frontend directly:
- `ranked_recommendations.csv`
- `scenario_summary.csv`
- `node_clusters.csv`
- `underserved_communities.csv`
- `recommendations.geojson`
- `clusters.geojson`

Additional learning outputs:
- `node_scores.csv`
- `model_metadata.json`

## CLI Example
```powershell
python ev_network_gnn.py --data-dir data --output-dir outputs_gnn_gat --model gat --epochs 200
```

## Frontend Compatibility Notes
The frontend adapter should treat:
- `marginal_demand_gain` as the recommendation gain field
- `node_weight` as the final scored ranking value
- `population_score` as optional enrichment for display/tooltips

## Practical Defaults for Hackathon
- Use `gcn` or `graphsage` for fastest stable runs.
- Use `gat` for attention-based narrative, but expect slightly slower training.
- Keep `--epochs` around `120-250` for demo turnaround.
