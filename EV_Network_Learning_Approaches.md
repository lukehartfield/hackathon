# EV Network Learning Approaches (Austin, TX)

## Purpose
This document defines learning-based extensions to the current classical baseline in `ev_network_optimization.py`.

It is designed to preserve the same project framing and output contract from:
- `EV_Charging_Austin_Context.md`
- `EV_Network_Optimization_Context.md`

## Current Baseline (Reference)
The existing script is a classical pipeline:
- Hand-crafted feature weighting
- Greedy expansion optimization
- Proximity-based graph + connected-components clustering

This remains the benchmark model for hackathon reliability and speed.

## Learning-Based Upgrade Strategy
Use a staged path so the team can keep shipping while adding ML/graph learning.

### Stage 1: Learned Node Scoring (Low Risk)
Goal: Replace fixed feature weights with a learned scoring model.

- Inputs:
  - `traffic_score`
  - `parking_score`
  - `charger_gap_score`
  - `distance_to_nearest_existing`
  - `demand_proxy`
  - Optional extra features (time-of-day, socioeconomic, POI density)
- Model options:
  - Linear/ElasticNet regression
  - Gradient boosted trees (XGBoost/LightGBM)
- Target options:
  - Historical utilization proxy
  - Simulated demand gain under held-out scenarios
- Integration:
  - Model outputs `learned_node_score`
  - Replace `node_weight` in greedy optimizer with `learned_node_score`

### Stage 2: Graph Embedding + Supervised Ranker (Medium Risk)
Goal: Learn graph-aware representations before ranking candidates.

- Build graph from travel-distance/proximity edges.
- Compute node embeddings (Node2Vec/DeepWalk).
- Concatenate embedding vectors with engineered tabular features.
- Train ranker/regressor to predict station impact.
- Use predicted impact as node priority in expansion optimization.

### Stage 3: Full Graph Neural Network (Higher Risk)
Goal: End-to-end node scoring with neighborhood message passing.

- Candidate architectures:
  - GraphSAGE
  - GAT
  - GCN
- Node features:
  - Existing engineered signals
  - Optional temporal slices and equity signals
- Edge features:
  - Travel time, corridor flow, accessibility strength
- Outputs:
  - Node-level expansion score
  - Optional uncertainty score for decision confidence

## Training Labels (Practical Options)
Because true labels may be sparse, use one or more:
- Historical charger utilization/occupancy (best if available)
- Session counts, energy dispensed, queue wait time
- Proxy labels from traffic + demand outcomes
- Counterfactual labels from simulation (offline what-if runs)

## Evaluation Framework
All learning methods should be compared against the current baseline using the same objectives.

### Core metrics
- Coverage ratio (at N=10/25/50)
- Demand gain proxy
- Avg distance to nearest charger
- Underserved-community improvement

### Ranking metrics
- NDCG@K for site ranking quality
- Precision@K for high-impact sites

### Spatial robustness checks
- Train/test split by geography (avoid leakage)
- Train on one period, test on later period

## Output Compatibility Contract
To support downstream integration, learning pipelines should still produce:
- `ranked_recommendations.csv`
- `scenario_summary.csv`
- `node_clusters.csv`
- `underserved_communities.csv`
- `recommendations.geojson`
- `clusters.geojson`

Recommended additions:
- `model_metadata.json` (model type, feature set, training date, metrics)
- `node_scores.csv` (site_id, classical_score, learned_score, uncertainty)

## Minimal Implementation Plan (Hackathon-Friendly)
1. Keep current classical script as baseline and fallback.
2. Add a new script (example: `ev_network_learning.py`) that:
   - reads same input CSVs
   - trains a learned scorer
   - outputs same artifacts
3. Add command flag to choose strategy:
   - `--mode classical` or `--mode learned`
4. Publish side-by-side benchmark table for N=10/25/50 scenarios.

## Risks and Mitigations
- Risk: Weak labels produce unstable models.
  - Mitigation: Use classical baseline + calibration checks.
- Risk: Spatial leakage inflates metrics.
  - Mitigation: geography-aware splits.
- Risk: Overfitting to placeholder synthetic data.
  - Mitigation: do not report synthetic-only model performance as production-ready.

## Decision Guidance
For the hackathon demo:
- Ship classical baseline for reliability.
- Add Stage 1 learned scorer if time permits.
- Present Stage 2/3 as roadmap with architecture diagram and evaluation plan.
