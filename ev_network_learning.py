#!/usr/bin/env python3
"""
Learning-based EV charging expansion prototype for Austin, TX.

This script is a substitute for the classical baseline in ev_network_optimization.py.
It keeps the same output contract while replacing hand-tuned node weights with a
learned score and graph neighborhood propagation.

Outputs (default: ./outputs):
- ranked_recommendations.csv
- scenario_summary.csv
- node_clusters.csv
- underserved_communities.csv
- recommendations.geojson
- clusters.geojson
- model_metadata.json
- node_scores.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple


@dataclass(frozen=True)
class Config:
    edge_radius_km: float = 3.0
    service_radius_km: float = 2.5
    density_radius_km: float = 2.0
    underserved_distance_km: float = 2.2
    smoothing_alpha: float = 0.70
    smoothing_iters: int = 2
    ridge_lambda: float = 0.05
    rng_seed: int = 42


FEATURE_NAMES = [
    "traffic_score",
    "parking_score",
    "charger_gap_score",
    "distance_to_nearest_existing",
    "demand_proxy",
]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = p2 - p1
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def min_max_scale(values: List[float]) -> List[float]:
    if not values:
        return []
    lo = min(values)
    hi = max(values)
    if math.isclose(lo, hi):
        return [0.5 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def generate_placeholder_data(config: Config) -> Tuple[List[Dict], List[Dict]]:
    rng = random.Random(config.rng_seed)
    center_lat, center_lon = 30.2672, -97.7431

    existing = []
    for i in range(28):
        existing.append(
            {
                "site_id": f"EX_{i:03d}",
                "lat": center_lat + rng.gauss(0, 0.05),
                "lon": center_lon + rng.gauss(0, 0.05),
                "charger_count": rng.randint(2, 12),
                "charger_type": "L2" if rng.random() < 0.75 else "DCFC",
                "network": rng.choice(["ChargePoint", "EVgo", "Tesla", "Blink"]),
                "is_existing": True,
            }
        )

    candidates = []
    for i in range(120):
        candidates.append(
            {
                "site_id": f"CA_{i:03d}",
                "lat": center_lat + rng.gauss(0, 0.07),
                "lon": center_lon + rng.gauss(0, 0.07),
                "traffic_score": rng.uniform(20, 100),
                "parking_score": rng.uniform(15, 100),
                "demand_proxy": rng.uniform(10, 100),
                "is_existing": False,
            }
        )

    return existing, candidates


def load_data(data_dir: Path, config: Config) -> Tuple[List[Dict], List[Dict], str]:
    existing_path = data_dir / "existing_stations.csv"
    candidates_path = data_dir / "candidate_sites.csv"

    if not existing_path.exists() or not candidates_path.exists():
        existing, candidates = generate_placeholder_data(config)
        return existing, candidates, "placeholder"

    existing_rows = read_csv_rows(existing_path)
    candidates_rows = read_csv_rows(candidates_path)

    existing: List[Dict] = []
    for row in existing_rows:
        existing.append(
            {
                "site_id": row["site_id"],
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "charger_count": int(float(row.get("charger_count", 1))),
                "charger_type": row.get("charger_type", "unknown"),
                "network": row.get("network", "unknown"),
                "is_existing": True,
            }
        )

    candidates: List[Dict] = []
    for row in candidates_rows:
        rec = {
            "site_id": row["site_id"],
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
            "traffic_score": float(row["traffic_score"]),
            "parking_score": float(row["parking_score"]),
            "demand_proxy": float(row["demand_proxy"]),
            "is_existing": False,
        }
        if "target_impact" in row and row["target_impact"] != "":
            rec["target_impact"] = float(row["target_impact"])
        if "historical_sessions" in row and row["historical_sessions"] != "":
            rec["historical_sessions"] = float(row["historical_sessions"])
        if "utilization" in row and row["utilization"] != "":
            rec["utilization"] = float(row["utilization"])
        candidates.append(rec)

    return existing, candidates, "csv"


def engineer_features(existing: List[Dict], candidates: List[Dict], config: Config) -> None:
    if not existing:
        raise ValueError("Need at least one existing charging station")

    for c in candidates:
        dists = [haversine_km(c["lat"], c["lon"], e["lat"], e["lon"]) for e in existing]
        c["distance_to_nearest_existing_raw"] = min(dists)
        c["existing_density_raw"] = sum(1 for d in dists if d <= config.density_radius_km)

    traffic_scaled = min_max_scale([float(c["traffic_score"]) for c in candidates])
    parking_scaled = min_max_scale([float(c["parking_score"]) for c in candidates])
    demand_scaled = min_max_scale([float(c["demand_proxy"]) for c in candidates])
    distance_scaled = min_max_scale([float(c["distance_to_nearest_existing_raw"]) for c in candidates])
    density_scaled = min_max_scale([float(c["existing_density_raw"]) for c in candidates])

    for i, c in enumerate(candidates):
        c["traffic_score"] = traffic_scaled[i]
        c["parking_score"] = parking_scaled[i]
        c["demand_proxy"] = demand_scaled[i]
        c["distance_to_nearest_existing"] = distance_scaled[i]
        c["charger_gap_score"] = 1.0 - density_scaled[i]


def identity_matrix(n: int) -> List[List[float]]:
    out = []
    for i in range(n):
        row = [0.0] * n
        row[i] = 1.0
        out.append(row)
    return out


def transpose(a: List[List[float]]) -> List[List[float]]:
    return [list(col) for col in zip(*a)]


def matmul(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    n = len(a)
    m = len(b[0])
    k = len(b)
    out = [[0.0] * m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            s = 0.0
            for t in range(k):
                s += a[i][t] * b[t][j]
            out[i][j] = s
    return out


def matvec(a: List[List[float]], v: List[float]) -> List[float]:
    out = [0.0] * len(a)
    for i in range(len(a)):
        s = 0.0
        for j in range(len(v)):
            s += a[i][j] * v[j]
        out[i] = s
    return out


def solve_linear_system(a: List[List[float]], b: List[float]) -> List[float]:
    n = len(a)
    aug = [row[:] + [b[i]] for i, row in enumerate(a)]

    for col in range(n):
        pivot = col
        max_abs = abs(aug[col][col])
        for r in range(col + 1, n):
            if abs(aug[r][col]) > max_abs:
                max_abs = abs(aug[r][col])
                pivot = r

        if math.isclose(max_abs, 0.0):
            continue

        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]

        piv = aug[col][col]
        for j in range(col, n + 1):
            aug[col][j] /= piv

        for r in range(n):
            if r == col:
                continue
            factor = aug[r][col]
            if math.isclose(factor, 0.0):
                continue
            for j in range(col, n + 1):
                aug[r][j] -= factor * aug[col][j]

    return [aug[i][n] for i in range(n)]


def fit_ridge_regression(x: List[List[float]], y: List[float], ridge_lambda: float) -> List[float]:
    xt = transpose(x)
    xtx = matmul(xt, x)
    n_features = len(xtx)

    eye = identity_matrix(n_features)
    for i in range(n_features):
        xtx[i][i] += ridge_lambda * eye[i][i]

    xty = matvec(xt, y)
    return solve_linear_system(xtx, xty)


def predict_linear(x: List[List[float]], weights: List[float]) -> List[float]:
    out = []
    for row in x:
        s = 0.0
        for i, v in enumerate(row):
            s += v * weights[i]
        out.append(s)
    return out


def determine_training_target(candidates: List[Dict]) -> Tuple[List[float], str]:
    if all("target_impact" in c for c in candidates):
        return [float(c["target_impact"]) for c in candidates], "target_impact"
    if all("historical_sessions" in c for c in candidates):
        return [float(c["historical_sessions"]) for c in candidates], "historical_sessions"
    if all("utilization" in c for c in candidates):
        return [float(c["utilization"]) for c in candidates], "utilization"

    proxy = []
    for c in candidates:
        val = (
            0.40 * float(c["traffic_score"])
            + 0.35 * float(c["demand_proxy"])
            + 0.15 * float(c["parking_score"])
            + 0.10 * float(c["distance_to_nearest_existing"])
        )
        proxy.append(val)
    return proxy, "proxy_target"


def build_candidate_graph(candidates: List[Dict], edge_radius_km: float) -> Dict[str, List[Tuple[str, float]]]:
    adjacency: Dict[str, List[Tuple[str, float]]] = {c["site_id"]: [] for c in candidates}

    for i in range(len(candidates)):
        a = candidates[i]
        for j in range(i + 1, len(candidates)):
            b = candidates[j]
            d = haversine_km(a["lat"], a["lon"], b["lat"], b["lon"])
            if d <= edge_radius_km:
                affinity = 1.0 / (d + 0.05)
                adjacency[a["site_id"]].append((b["site_id"], affinity))
                adjacency[b["site_id"]].append((a["site_id"], affinity))

    return adjacency


def graph_smooth_scores(
    candidates: List[Dict],
    adjacency: Dict[str, List[Tuple[str, float]]],
    alpha: float,
    iters: int,
) -> Dict[str, float]:
    scores = {c["site_id"]: float(c["base_learned_score"]) for c in candidates}

    for _ in range(max(0, iters)):
        updated = {}
        for c in candidates:
            sid = c["site_id"]
            nbrs = adjacency[sid]
            if not nbrs:
                updated[sid] = scores[sid]
                continue

            wsum = 0.0
            ssum = 0.0
            for nid, w in nbrs:
                wsum += w
                ssum += w * scores[nid]
            nbr_mean = ssum / wsum if wsum > 0 else scores[sid]
            updated[sid] = alpha * scores[sid] + (1.0 - alpha) * nbr_mean
        scores = updated

    return scores


def connected_components(adjacency_unweighted: Dict[str, Set[str]]) -> Dict[str, int]:
    visited: Set[str] = set()
    mapping: Dict[str, int] = {}
    comp_id = 0

    for node in adjacency_unweighted:
        if node in visited:
            continue
        stack = [node]
        visited.add(node)
        while stack:
            cur = stack.pop()
            mapping[cur] = comp_id
            for nbr in adjacency_unweighted[cur]:
                if nbr not in visited:
                    visited.add(nbr)
                    stack.append(nbr)
        comp_id += 1

    return mapping


def build_full_graph(existing: List[Dict], candidates: List[Dict], edge_radius_km: float) -> Tuple[Dict[str, Set[str]], int]:
    nodes = existing + candidates
    adjacency: Dict[str, Set[str]] = {n["site_id"]: set() for n in nodes}
    edges = 0

    for i in range(len(nodes)):
        a = nodes[i]
        for j in range(i + 1, len(nodes)):
            b = nodes[j]
            d = haversine_km(a["lat"], a["lon"], b["lat"], b["lon"])
            if d <= edge_radius_km:
                adjacency[a["site_id"]].add(b["site_id"])
                adjacency[b["site_id"]].add(a["site_id"])
                edges += 1

    return adjacency, edges


def greedy_facility_expansion(
    existing: List[Dict],
    candidates: List[Dict],
    budget: int,
    service_radius_km: float,
) -> List[Dict]:
    n = len(candidates)
    if n == 0:
        return []

    d_c2e: List[List[float]] = []
    for c in candidates:
        d_c2e.append([haversine_km(c["lat"], c["lon"], e["lat"], e["lon"]) for e in existing])

    d_c2c: List[List[float]] = []
    for ci in candidates:
        row = []
        for cj in candidates:
            row.append(haversine_km(ci["lat"], ci["lon"], cj["lat"], cj["lon"]))
        d_c2c.append(row)

    covered = [min(row) <= service_radius_km for row in d_c2e]
    selected: List[int] = []

    for _ in range(min(budget, n)):
        best_idx = -1
        best_value = -1.0

        for i in range(n):
            if i in selected:
                continue
            marginal = 0.0
            for j in range(n):
                if not covered[j] and d_c2c[j][i] <= service_radius_km:
                    marginal += float(candidates[j]["demand_weight"])
            value = marginal * (0.7 + 0.3 * float(candidates[i]["learned_node_score"]))
            if value > best_value:
                best_value = value
                best_idx = i

        if best_idx < 0:
            break

        selected.append(best_idx)
        for j in range(n):
            if d_c2c[j][best_idx] <= service_radius_km:
                covered[j] = True

    recommendations: List[Dict] = []
    covered = [min(row) <= service_radius_km for row in d_c2e]

    for rank, idx in enumerate(selected, start=1):
        marginal = 0.0
        for j in range(n):
            if not covered[j] and d_c2c[j][idx] <= service_radius_km:
                marginal += float(candidates[j]["demand_weight"])
        for j in range(n):
            if d_c2c[j][idx] <= service_radius_km:
                covered[j] = True

        rec = {
            "rank": rank,
            "site_id": candidates[idx]["site_id"],
            "lat": candidates[idx]["lat"],
            "lon": candidates[idx]["lon"],
            "node_weight": candidates[idx]["learned_node_score"],
            "marginal_demand_gain": marginal,
            "cumulative_coverage": sum(1 for x in covered if x) / n,
        }
        recommendations.append(rec)

    return recommendations


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    vals = sorted(values)
    idx = int((len(vals) - 1) * p)
    return vals[idx]


def community_metrics(
    existing: List[Dict],
    candidates: List[Dict],
    community_map: Dict[str, int],
    config: Config,
) -> Tuple[List[Dict], List[Dict]]:
    nodes = existing + candidates
    node_rows: List[Dict] = []

    for n in nodes:
        d = min(haversine_km(n["lat"], n["lon"], e["lat"], e["lon"]) for e in existing)
        row = {
            "site_id": n["site_id"],
            "lat": n["lat"],
            "lon": n["lon"],
            "is_existing": n["is_existing"],
            "community_id": community_map.get(n["site_id"], -1),
            "distance_to_nearest_existing_km": d,
            "node_weight": n.get("learned_node_score", ""),
        }
        node_rows.append(row)

    by_comm: Dict[int, Dict] = {}
    for row in node_rows:
        cid = int(row["community_id"])
        if cid not in by_comm:
            by_comm[cid] = {
                "community_id": cid,
                "node_count": 0,
                "existing_count": 0,
                "distances": [],
                "weights": [],
            }

        by_comm[cid]["node_count"] += 1
        if row["is_existing"]:
            by_comm[cid]["existing_count"] += 1
        by_comm[cid]["distances"].append(float(row["distance_to_nearest_existing_km"]))
        if row["node_weight"] != "":
            by_comm[cid]["weights"].append(float(row["node_weight"]))

    weight_cutoff = percentile([float(c["learned_node_score"]) for c in candidates], 0.65)
    summary_rows: List[Dict] = []
    for cid, agg in by_comm.items():
        avg_dist = sum(agg["distances"]) / len(agg["distances"]) if agg["distances"] else 0.0
        avg_weight = sum(agg["weights"]) / len(agg["weights"]) if agg["weights"] else 0.0
        underserved = (
            (avg_dist >= config.underserved_distance_km or agg["existing_count"] == 0)
            and avg_weight >= weight_cutoff
        )
        summary_rows.append(
            {
                "community_id": cid,
                "node_count": agg["node_count"],
                "existing_count": agg["existing_count"],
                "avg_dist_to_existing_km": avg_dist,
                "avg_node_weight": avg_weight,
                "underserved": underserved,
            }
        )

    summary_rows.sort(key=lambda x: x["community_id"])
    return node_rows, summary_rows


def write_csv(path: Path, rows: List[Dict], fields: List[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def to_geojson(rows: List[Dict], prop_fields: List[str]) -> Dict:
    feats = []
    for row in rows:
        props = {k: row.get(k, None) for k in prop_fields}
        feats.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(row["lon"]), float(row["lat"])]},
                "properties": props,
            }
        )
    return {"type": "FeatureCollection", "features": feats}


def run_pipeline(data_dir: Path, output_dir: Path, config: Config) -> None:
    existing, candidates, data_mode = load_data(data_dir, config)
    engineer_features(existing, candidates, config)

    x: List[List[float]] = []
    for c in candidates:
        x.append([1.0] + [float(c[f]) for f in FEATURE_NAMES])

    target, target_source = determine_training_target(candidates)
    target_scaled = min_max_scale(target)

    weights = fit_ridge_regression(x, target_scaled, config.ridge_lambda)
    base_scores_raw = predict_linear(x, weights)
    base_scores = min_max_scale(base_scores_raw)

    for i, c in enumerate(candidates):
        c["base_learned_score"] = base_scores[i]
        c["demand_weight"] = 0.6 * float(c["traffic_score"]) + 0.4 * float(c["demand_proxy"])

    cand_graph = build_candidate_graph(candidates, config.edge_radius_km)
    smoothed = graph_smooth_scores(candidates, cand_graph, config.smoothing_alpha, config.smoothing_iters)

    final_scores = min_max_scale([smoothed[c["site_id"]] for c in candidates])
    for i, c in enumerate(candidates):
        c["learned_node_score"] = final_scores[i]

    full_graph, edge_count = build_full_graph(existing, candidates, config.edge_radius_km)
    communities = connected_components(full_graph)
    node_clusters, community_summary = community_metrics(existing, candidates, communities, config)

    scenarios = [10, 25, 50]
    scenario_rows: List[Dict] = []
    scenario_recs: Dict[int, List[Dict]] = {}

    for budget in scenarios:
        recs = greedy_facility_expansion(existing, candidates, budget, config.service_radius_km)
        scenario_recs[budget] = recs
        scenario_rows.append(
            {
                "stations_added": budget,
                "selected_sites": len(recs),
                "coverage_ratio": recs[-1]["cumulative_coverage"] if recs else 0.0,
                "aggregate_marginal_demand_gain": sum(r["marginal_demand_gain"] for r in recs),
            }
        )

    ranked_recs = scenario_recs[50]

    node_scores_rows = []
    for c in candidates:
        node_scores_rows.append(
            {
                "site_id": c["site_id"],
                "base_learned_score": c["base_learned_score"],
                "learned_node_score": c["learned_node_score"],
                "demand_weight": c["demand_weight"],
            }
        )

    model_metadata = {
        "model_type": "ridge_regression_plus_graph_smoothing",
        "target_source": target_source,
        "data_mode": data_mode,
        "feature_names": FEATURE_NAMES,
        "weights": {"intercept": weights[0], **{FEATURE_NAMES[i]: weights[i + 1] for i in range(len(FEATURE_NAMES))}},
        "smoothing_alpha": config.smoothing_alpha,
        "smoothing_iters": config.smoothing_iters,
        "ridge_lambda": config.ridge_lambda,
    }

    output_dir.mkdir(parents=True, exist_ok=True)

    write_csv(
        output_dir / "ranked_recommendations.csv",
        ranked_recs,
        ["rank", "site_id", "lat", "lon", "node_weight", "marginal_demand_gain", "cumulative_coverage"],
    )
    write_csv(
        output_dir / "scenario_summary.csv",
        scenario_rows,
        ["stations_added", "selected_sites", "coverage_ratio", "aggregate_marginal_demand_gain"],
    )
    write_csv(
        output_dir / "node_clusters.csv",
        node_clusters,
        [
            "site_id",
            "lat",
            "lon",
            "is_existing",
            "community_id",
            "distance_to_nearest_existing_km",
            "node_weight",
        ],
    )
    write_csv(
        output_dir / "underserved_communities.csv",
        community_summary,
        [
            "community_id",
            "node_count",
            "existing_count",
            "avg_dist_to_existing_km",
            "avg_node_weight",
            "underserved",
        ],
    )
    write_csv(
        output_dir / "node_scores.csv",
        node_scores_rows,
        ["site_id", "base_learned_score", "learned_node_score", "demand_weight"],
    )

    rec_geo = to_geojson(
        ranked_recs,
        ["rank", "site_id", "node_weight", "marginal_demand_gain", "cumulative_coverage"],
    )
    clu_geo = to_geojson(
        node_clusters,
        ["site_id", "community_id", "is_existing", "distance_to_nearest_existing_km", "node_weight"],
    )

    with (output_dir / "recommendations.geojson").open("w", encoding="utf-8") as f:
        json.dump(rec_geo, f, indent=2)
    with (output_dir / "clusters.geojson").open("w", encoding="utf-8") as f:
        json.dump(clu_geo, f, indent=2)
    with (output_dir / "model_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(model_metadata, f, indent=2)

    print("=== EV Charging Expansion Results (Learning Approach) ===")
    print(f"Nodes in graph: {len(existing) + len(candidates)}")
    print(f"Edges in graph: {edge_count}")
    print(f"Training target source: {target_source}")

    print("\nScenario summary:")
    for row in scenario_rows:
        print(
            f"  add={row['stations_added']:>2} | selected={row['selected_sites']:>2} "
            f"| coverage={row['coverage_ratio']:.3f} | demand_gain={row['aggregate_marginal_demand_gain']:.3f}"
        )

    if ranked_recs:
        print("\nTop 10 recommendations:")
        for row in ranked_recs[:10]:
            print(
                f"  {row['rank']:>2}. {row['site_id']} | score={row['node_weight']:.3f} "
                f"| marginal_gain={row['marginal_demand_gain']:.3f} | coverage={row['cumulative_coverage']:.3f}"
            )

    underserved_count = sum(1 for row in community_summary if row["underserved"])
    print(f"\nUnderserved communities found: {underserved_count}")
    print(f"Output directory: {output_dir.resolve()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Learning-based EV charging expansion in Austin, TX")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--edge-radius-km", type=float, default=3.0)
    parser.add_argument("--service-radius-km", type=float, default=2.5)
    parser.add_argument("--density-radius-km", type=float, default=2.0)
    parser.add_argument("--underserved-distance-km", type=float, default=2.2)
    parser.add_argument("--smoothing-alpha", type=float, default=0.70)
    parser.add_argument("--smoothing-iters", type=int, default=2)
    parser.add_argument("--ridge-lambda", type=float, default=0.05)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = Config(
        edge_radius_km=args.edge_radius_km,
        service_radius_km=args.service_radius_km,
        density_radius_km=args.density_radius_km,
        underserved_distance_km=args.underserved_distance_km,
        smoothing_alpha=args.smoothing_alpha,
        smoothing_iters=args.smoothing_iters,
        ridge_lambda=args.ridge_lambda,
    )
    run_pipeline(args.data_dir, args.output_dir, cfg)


if __name__ == "__main__":
    main()
