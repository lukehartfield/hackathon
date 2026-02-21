#!/usr/bin/env python3
"""
EV charging network optimization prototype for Austin, TX.

Assumes API data has been scraped and can be loaded from CSV files.
If CSVs are missing, the script falls back to placeholder Austin records.

Outputs (in ./outputs by default):
- ranked_recommendations.csv
- scenario_summary.csv
- node_clusters.csv
- underserved_communities.csv
- recommendations.geojson
- clusters.geojson
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
    rng_seed: int = 42


FEATURE_WEIGHTS: Dict[str, float] = {
    "traffic_score": 0.30,
    "parking_score": 0.20,
    "charger_gap_score": 0.20,
    "distance_to_nearest_existing": 0.15,
    "demand_proxy": 0.15,
}


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


def load_data(data_dir: Path, config: Config) -> Tuple[List[Dict], List[Dict]]:
    existing_path = data_dir / "existing_stations.csv"
    candidates_path = data_dir / "candidate_sites.csv"

    if not existing_path.exists() or not candidates_path.exists():
        return generate_placeholder_data(config)

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
        candidates.append(
            {
                "site_id": row["site_id"],
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "traffic_score": float(row["traffic_score"]),
                "parking_score": float(row["parking_score"]),
                "demand_proxy": float(row["demand_proxy"]),
                "is_existing": False,
            }
        )

    return existing, candidates


def engineer_features(existing: List[Dict], candidates: List[Dict], config: Config) -> None:
    if not existing:
        raise ValueError("Need at least one existing charging station.")

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

        node_weight = 0.0
        for fname, weight in FEATURE_WEIGHTS.items():
            node_weight += weight * float(c[fname])

        c["node_weight"] = node_weight
        c["demand_weight"] = 0.6 * c["traffic_score"] + 0.4 * c["demand_proxy"]


def build_graph(existing: List[Dict], candidates: List[Dict], config: Config) -> Tuple[Dict[str, Set[str]], int]:
    nodes = existing + candidates
    adjacency: Dict[str, Set[str]] = {n["site_id"]: set() for n in nodes}
    edge_count = 0

    for i in range(len(nodes)):
        a = nodes[i]
        for j in range(i + 1, len(nodes)):
            b = nodes[j]
            d = haversine_km(a["lat"], a["lon"], b["lat"], b["lon"])
            if d <= config.edge_radius_km:
                adjacency[a["site_id"]].add(b["site_id"])
                adjacency[b["site_id"]].add(a["site_id"])
                edge_count += 1

    return adjacency, edge_count


def connected_components(adjacency: Dict[str, Set[str]]) -> Dict[str, int]:
    visited: Set[str] = set()
    comp_id = 0
    mapping: Dict[str, int] = {}

    for node in adjacency:
        if node in visited:
            continue
        stack = [node]
        visited.add(node)
        while stack:
            cur = stack.pop()
            mapping[cur] = comp_id
            for nbr in adjacency[cur]:
                if nbr not in visited:
                    visited.add(nbr)
                    stack.append(nbr)
        comp_id += 1

    return mapping


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
            value = marginal * (0.7 + 0.3 * float(candidates[i]["node_weight"]))
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
            "node_weight": candidates[idx]["node_weight"],
            "marginal_demand_gain": marginal,
            "cumulative_coverage": sum(1 for x in covered if x) / n,
        }
        recommendations.append(rec)

    return recommendations


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = int((len(sorted_vals) - 1) * p)
    return sorted_vals[idx]


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
            "node_weight": n.get("node_weight", ""),
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

    weight_cutoff = percentile([float(c["node_weight"]) for c in candidates], 0.65)
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
    features = []
    for row in rows:
        props = {k: row.get(k, None) for k in prop_fields}
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(row["lon"]), float(row["lat"])]},
                "properties": props,
            }
        )
    return {"type": "FeatureCollection", "features": features}


def run_pipeline(data_dir: Path, output_dir: Path, config: Config) -> None:
    existing, candidates = load_data(data_dir, config)
    engineer_features(existing, candidates, config)

    adjacency, edge_count = build_graph(existing, candidates, config)
    community_map = connected_components(adjacency)
    node_clusters, community_summary = community_metrics(existing, candidates, community_map, config)

    scenarios = [10, 25, 50]
    scenario_summary: List[Dict] = []
    scenario_recs: Dict[int, List[Dict]] = {}

    for budget in scenarios:
        recs = greedy_facility_expansion(existing, candidates, budget, config.service_radius_km)
        scenario_recs[budget] = recs

        scenario_summary.append(
            {
                "stations_added": budget,
                "selected_sites": len(recs),
                "coverage_ratio": recs[-1]["cumulative_coverage"] if recs else 0.0,
                "aggregate_marginal_demand_gain": sum(r["marginal_demand_gain"] for r in recs),
            }
        )

    ranked_recs = scenario_recs[50]

    output_dir.mkdir(parents=True, exist_ok=True)

    write_csv(
        output_dir / "ranked_recommendations.csv",
        ranked_recs,
        ["rank", "site_id", "lat", "lon", "node_weight", "marginal_demand_gain", "cumulative_coverage"],
    )
    write_csv(
        output_dir / "scenario_summary.csv",
        scenario_summary,
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

    rec_geojson = to_geojson(
        ranked_recs,
        ["rank", "site_id", "node_weight", "marginal_demand_gain", "cumulative_coverage"],
    )
    cluster_geojson = to_geojson(
        node_clusters,
        ["site_id", "community_id", "is_existing", "distance_to_nearest_existing_km", "node_weight"],
    )

    with (output_dir / "recommendations.geojson").open("w", encoding="utf-8") as f:
        json.dump(rec_geojson, f, indent=2)
    with (output_dir / "clusters.geojson").open("w", encoding="utf-8") as f:
        json.dump(cluster_geojson, f, indent=2)

    print("=== EV Charging Expansion Results (Austin) ===")
    print(f"Nodes in graph: {len(existing) + len(candidates)}")
    print(f"Edges in graph: {edge_count}")

    print("\nScenario summary:")
    for row in scenario_summary:
        print(
            f"  add={row['stations_added']:>2} | selected={row['selected_sites']:>2} "
            f"| coverage={row['coverage_ratio']:.3f} | demand_gain={row['aggregate_marginal_demand_gain']:.3f}"
        )

    if ranked_recs:
        print("\nTop 10 recommendations:")
        for row in ranked_recs[:10]:
            print(
                f"  {row['rank']:>2}. {row['site_id']} | weight={row['node_weight']:.3f} "
                f"| marginal_gain={row['marginal_demand_gain']:.3f} "
                f"| coverage={row['cumulative_coverage']:.3f}"
            )

    underserved_count = sum(1 for row in community_summary if row["underserved"])
    print(f"\nUnderserved communities found: {underserved_count}")
    print(f"Output directory: {output_dir.resolve()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Optimize EV charging expansion in Austin, TX")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--edge-radius-km", type=float, default=3.0)
    parser.add_argument("--service-radius-km", type=float, default=2.5)
    parser.add_argument("--density-radius-km", type=float, default=2.0)
    parser.add_argument("--underserved-distance-km", type=float, default=2.2)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = Config(
        edge_radius_km=args.edge_radius_km,
        service_radius_km=args.service_radius_km,
        density_radius_km=args.density_radius_km,
        underserved_distance_km=args.underserved_distance_km,
    )
    run_pipeline(args.data_dir, args.output_dir, cfg)


if __name__ == "__main__":
    main()
