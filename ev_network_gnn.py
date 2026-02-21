#!/usr/bin/env python3
"""
GNN-based EV charging expansion pipeline for Austin, TX.

Same input/output contract as existing optimization scripts, but node scoring is
produced by a graph neural network (GCN, GraphSAGE, or GAT).
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

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass(frozen=True)
class Config:
    edge_radius_km: float = 3.0
    service_radius_km: float = 2.5
    density_radius_km: float = 2.0
    underserved_distance_km: float = 2.2
    min_uncovered_ratio: float = 0.15
    hidden_dim: int = 32
    epochs: int = 250
    lr: float = 0.01
    weight_decay: float = 1e-4
    dropout: float = 0.15
    model_type: str = "gcn"
    seed: int = 42


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


def _feature_centroid_lat_lon(feature: Dict) -> Tuple[float, float] | None:
    geometry = feature.get("geometry") or {}
    gtype = geometry.get("type")
    coords = geometry.get("coordinates")
    if not coords:
        return None

    points: List[Tuple[float, float]] = []
    if gtype == "Polygon":
        ring = coords[0] if coords else []
        points = [(float(x), float(y)) for x, y in ring]
    elif gtype == "MultiPolygon":
        for poly in coords:
            if not poly:
                continue
            ring = poly[0] if poly else []
            points.extend((float(x), float(y)) for x, y in ring)
    elif gtype == "Point":
        points = [(float(coords[0]), float(coords[1]))]

    if not points:
        return None

    lon = sum(p[0] for p in points) / len(points)
    lat = sum(p[1] for p in points) / len(points)
    return lat, lon


def load_npa_candidates(data_dir: Path, seed: int) -> List[Dict]:
    npa_path = data_dir / "austin_npa.geojson"
    if not npa_path.exists():
        return []

    with npa_path.open("r", encoding="utf-8") as f:
        geo = json.load(f)

    features = geo.get("features", [])
    rows: List[Tuple[Dict, float, Tuple[float, float]]] = []
    raw_pop: List[float] = []
    for feat in features:
        props = feat.get("properties") or {}
        centroid = _feature_centroid_lat_lon(feat)
        if centroid is None:
            continue
        pop = float(props.get("population", 0) or 0)
        rows.append((props, pop, centroid))
        raw_pop.append(pop)

    if not rows:
        return []

    pop_scaled = min_max_scale(raw_pop)
    rng = random.Random(seed)
    out: List[Dict] = []
    for i, (props, _pop, (lat, lon)) in enumerate(rows):
        p = pop_scaled[i]
        traffic = max(5.0, min(100.0, 40.0 + 60.0 * p + rng.uniform(-8.0, 8.0)))
        parking = max(5.0, min(100.0, 80.0 - 25.0 * p + rng.uniform(-10.0, 10.0)))
        demand = max(5.0, min(100.0, 35.0 + 65.0 * p + rng.uniform(-6.0, 6.0)))
        out.append(
            {
                "site_id": f"NPA_{props.get('OBJECTID', i)}",
                "lat": lat,
                "lon": lon,
                "population_score": p,
                "traffic_score": traffic,
                "parking_score": parking,
                "demand_proxy": demand,
                "is_existing": False,
            }
        )
    return out


def generate_placeholder_data(seed: int) -> Tuple[List[Dict], List[Dict], str]:
    rng = random.Random(seed)
    center_lat, center_lon = 30.2672, -97.7431

    existing = []
    for i in range(28):
        existing.append(
            {
                "site_id": f"EX_{i:03d}",
                "lat": center_lat + rng.gauss(0, 0.05),
                "lon": center_lon + rng.gauss(0, 0.05),
                "charger_count": rng.randint(2, 12),
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

    return existing, candidates, "placeholder"


def load_data(data_dir: Path, cfg: Config) -> Tuple[List[Dict], List[Dict], str]:
    existing_path = data_dir / "existing_stations.csv"
    candidates_path = data_dir / "candidate_sites.csv"

    if not existing_path.exists():
        return generate_placeholder_data(cfg.seed)

    existing_rows = read_csv_rows(existing_path)
    existing: List[Dict] = []
    for row in existing_rows:
        existing.append(
            {
                "site_id": row["site_id"],
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "charger_count": int(float(row.get("charger_count", 1))),
                "is_existing": True,
            }
        )

    npa_candidates = load_npa_candidates(data_dir, cfg.seed)
    if npa_candidates:
        return existing, npa_candidates, "npa_geojson"

    if not candidates_path.exists():
        return generate_placeholder_data(cfg.seed)

    candidates_rows = read_csv_rows(candidates_path)
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

    return existing, candidates, "csv"


def engineer_features(existing: List[Dict], candidates: List[Dict], cfg: Config) -> None:
    for c in candidates:
        dists = [haversine_km(c["lat"], c["lon"], e["lat"], e["lon"]) for e in existing]
        c["distance_to_nearest_existing_raw"] = min(dists)
        c["existing_density_raw"] = sum(1 for d in dists if d <= cfg.density_radius_km)

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
        c["demand_weight"] = 0.6 * c["traffic_score"] + 0.4 * c["demand_proxy"]


def determine_target(candidates: List[Dict]) -> Tuple[List[float], str]:
    if all("target_impact" in c for c in candidates):
        return [float(c["target_impact"]) for c in candidates], "target_impact"
    if all("historical_sessions" in c for c in candidates):
        return [float(c["historical_sessions"]) for c in candidates], "historical_sessions"
    if all("utilization" in c for c in candidates):
        return [float(c["utilization"]) for c in candidates], "utilization"

    proxy = []
    for c in candidates:
        proxy.append(
            0.40 * float(c["traffic_score"])
            + 0.35 * float(c["demand_proxy"])
            + 0.15 * float(c["parking_score"])
            + 0.10 * float(c["distance_to_nearest_existing"])
        )
    return proxy, "proxy_target"


def build_candidate_adj(candidates: List[Dict], edge_radius_km: float) -> torch.Tensor:
    n = len(candidates)
    a = torch.zeros((n, n), dtype=torch.float32)
    for i in range(n):
        a[i, i] = 1.0
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_km(candidates[i]["lat"], candidates[i]["lon"], candidates[j]["lat"], candidates[j]["lon"])
            if d <= edge_radius_km:
                a[i, j] = 1.0
                a[j, i] = 1.0
    return a


def normalize_adj(a: torch.Tensor) -> torch.Tensor:
    deg = a.sum(dim=1)
    inv_sqrt = torch.pow(deg.clamp(min=1.0), -0.5)
    d_inv = torch.diag(inv_sqrt)
    return d_inv @ a @ d_inv


class GCNRegressor(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int, dropout: float):
        super().__init__()
        self.lin1 = nn.Linear(in_dim, hidden_dim)
        self.lin2 = nn.Linear(hidden_dim, 1)
        self.dropout = dropout

    def forward(self, x: torch.Tensor, a: torch.Tensor) -> torch.Tensor:
        h = a @ x
        h = F.relu(self.lin1(h))
        h = F.dropout(h, p=self.dropout, training=self.training)
        out = self.lin2(a @ h)
        return out.squeeze(-1)


class GraphSAGERegressor(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int, dropout: float):
        super().__init__()
        self.lin1 = nn.Linear(in_dim * 2, hidden_dim)
        self.lin2 = nn.Linear(hidden_dim * 2, 1)
        self.dropout = dropout

    def forward(self, x: torch.Tensor, a: torch.Tensor) -> torch.Tensor:
        row_sum = a.sum(dim=1, keepdim=True).clamp(min=1.0)
        neigh = (a @ x) / row_sum
        h = F.relu(self.lin1(torch.cat([x, neigh], dim=1)))
        h = F.dropout(h, p=self.dropout, training=self.training)
        neigh_h = (a @ h) / row_sum
        out = self.lin2(torch.cat([h, neigh_h], dim=1))
        return out.squeeze(-1)


class GATLayer(nn.Module):
    def __init__(self, in_dim: int, out_dim: int, dropout: float):
        super().__init__()
        self.w = nn.Linear(in_dim, out_dim, bias=False)
        self.a_src = nn.Parameter(torch.empty(out_dim))
        self.a_dst = nn.Parameter(torch.empty(out_dim))
        self.dropout = dropout
        nn.init.xavier_uniform_(self.w.weight)
        nn.init.normal_(self.a_src, std=0.1)
        nn.init.normal_(self.a_dst, std=0.1)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        h = self.w(x)
        src = (h * self.a_src).sum(dim=1)
        dst = (h * self.a_dst).sum(dim=1)
        e = F.leaky_relu(src[:, None] + dst[None, :], negative_slope=0.2)

        mask = adj > 0
        e = e.masked_fill(~mask, -1e9)
        alpha = torch.softmax(e, dim=1)
        alpha = F.dropout(alpha, p=self.dropout, training=self.training)
        return alpha @ h


class GATRegressor(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int, dropout: float):
        super().__init__()
        self.gat1 = GATLayer(in_dim, hidden_dim, dropout)
        self.gat2 = GATLayer(hidden_dim, 1, dropout)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        h = F.elu(self.gat1(x, adj))
        h = F.dropout(h, p=0.15, training=self.training)
        out = self.gat2(h, adj)
        return out.squeeze(-1)


def build_model(model_type: str, in_dim: int, hidden_dim: int, dropout: float) -> nn.Module:
    mt = model_type.lower()
    if mt == "gcn":
        return GCNRegressor(in_dim, hidden_dim, dropout)
    if mt == "graphsage":
        return GraphSAGERegressor(in_dim, hidden_dim, dropout)
    if mt == "gat":
        return GATRegressor(in_dim, hidden_dim, dropout)
    raise ValueError(f"Unsupported model type: {model_type}")


def train_gnn(candidates: List[Dict], cfg: Config) -> Tuple[List[float], Dict]:
    random.seed(cfg.seed)
    torch.manual_seed(cfg.seed)

    x_rows = [[float(c[f]) for f in FEATURE_NAMES] for c in candidates]
    x = torch.tensor(x_rows, dtype=torch.float32)
    y_raw, target_source = determine_target(candidates)
    y = torch.tensor(min_max_scale(y_raw), dtype=torch.float32)

    adj = build_candidate_adj(candidates, cfg.edge_radius_km)
    a_norm = normalize_adj(adj)

    model = build_model(cfg.model_type, in_dim=x.shape[1], hidden_dim=cfg.hidden_dim, dropout=cfg.dropout)
    optim = torch.optim.Adam(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)

    idx = list(range(len(candidates)))
    random.shuffle(idx)
    split = max(1, int(len(idx) * 0.8))
    tr_idx = torch.tensor(idx[:split], dtype=torch.long)
    va_idx = torch.tensor(idx[split:] if split < len(idx) else idx[:1], dtype=torch.long)

    best_val = float("inf")
    best_state = None

    for _ in range(cfg.epochs):
        model.train()
        pred = model(x, a_norm if cfg.model_type != "gat" else adj)
        loss = F.mse_loss(pred[tr_idx], y[tr_idx])
        optim.zero_grad()
        loss.backward()
        optim.step()

        model.eval()
        with torch.no_grad():
            val_pred = model(x, a_norm if cfg.model_type != "gat" else adj)
            val_loss = F.mse_loss(val_pred[va_idx], y[va_idx]).item()
            if val_loss < best_val:
                best_val = val_loss
                best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)

    model.eval()
    with torch.no_grad():
        preds = model(x, a_norm if cfg.model_type != "gat" else adj).tolist()

    preds_scaled = min_max_scale([float(p) for p in preds])
    metadata = {
        "model_type": cfg.model_type,
        "feature_names": FEATURE_NAMES,
        "target_source": target_source,
        "epochs": cfg.epochs,
        "hidden_dim": cfg.hidden_dim,
        "dropout": cfg.dropout,
        "learning_rate": cfg.lr,
        "weight_decay": cfg.weight_decay,
        "validation_mse": best_val,
    }
    return preds_scaled, metadata


def build_full_graph(existing: List[Dict], candidates: List[Dict], edge_radius_km: float) -> Tuple[Dict[str, Set[str]], int]:
    nodes = existing + candidates
    adjacency: Dict[str, Set[str]] = {n["site_id"]: set() for n in nodes}
    edges = 0
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            d = haversine_km(nodes[i]["lat"], nodes[i]["lon"], nodes[j]["lat"], nodes[j]["lon"])
            if d <= edge_radius_km:
                adjacency[nodes[i]["site_id"]].add(nodes[j]["site_id"])
                adjacency[nodes[j]["site_id"]].add(nodes[i]["site_id"])
                edges += 1
    return adjacency, edges


def connected_components(adjacency: Dict[str, Set[str]]) -> Dict[str, int]:
    visited: Set[str] = set()
    mapping: Dict[str, int] = {}
    cid = 0
    for node in adjacency:
        if node in visited:
            continue
        stack = [node]
        visited.add(node)
        while stack:
            cur = stack.pop()
            mapping[cur] = cid
            for nbr in adjacency[cur]:
                if nbr not in visited:
                    visited.add(nbr)
                    stack.append(nbr)
        cid += 1
    return mapping


def candidate_distance_stats(existing: List[Dict], candidates: List[Dict]) -> List[float]:
    out = []
    for c in candidates:
        out.append(min(haversine_km(c["lat"], c["lon"], e["lat"], e["lon"]) for e in existing))
    return out


def compute_effective_service_radius(cfg: Config, nearest: List[float]) -> Tuple[float, float, bool]:
    if not nearest:
        return cfg.service_radius_km, 0.0, False
    n = len(nearest)
    baseline = sum(1 for d in nearest if d <= cfg.service_radius_km) / n
    max_cov = max(0.0, min(1.0, 1.0 - cfg.min_uncovered_ratio))
    if baseline <= max_cov:
        return cfg.service_radius_km, baseline, False
    sorted_d = sorted(nearest)
    idx = int((n - 1) * max_cov)
    return max(0.01, sorted_d[idx]), baseline, True


def greedy_facility_expansion(existing: List[Dict], candidates: List[Dict], budget: int, service_radius_km: float) -> List[Dict]:
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
        best_val = -1.0
        for i in range(n):
            if i in selected:
                continue
            marginal = 0.0
            for j in range(n):
                if not covered[j] and d_c2c[j][i] <= service_radius_km:
                    marginal += float(candidates[j]["demand_weight"])
            val = marginal * (0.7 + 0.3 * float(candidates[i]["learned_node_score"]))
            if val > best_val:
                best_val = val
                best_idx = i
        if best_idx < 0:
            break
        selected.append(best_idx)
        for j in range(n):
            if d_c2c[j][best_idx] <= service_radius_km:
                covered[j] = True

    recs: List[Dict] = []
    covered = [min(row) <= service_radius_km for row in d_c2e]
    for rank, idx in enumerate(selected, start=1):
        marginal = 0.0
        for j in range(n):
            if not covered[j] and d_c2c[j][idx] <= service_radius_km:
                marginal += float(candidates[j]["demand_weight"])
        for j in range(n):
            if d_c2c[j][idx] <= service_radius_km:
                covered[j] = True

        recs.append(
            {
                "rank": rank,
                "site_id": candidates[idx]["site_id"],
                "lat": candidates[idx]["lat"],
                "lon": candidates[idx]["lon"],
                "node_weight": candidates[idx]["learned_node_score"],
                "population_score": candidates[idx].get("population_score", ""),
                "marginal_demand_gain": marginal,
                "cumulative_coverage": sum(1 for x in covered if x) / n,
            }
        )
    return recs


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    vals = sorted(values)
    return vals[int((len(vals) - 1) * p)]


def community_metrics(existing: List[Dict], candidates: List[Dict], community_map: Dict[str, int], cfg: Config) -> Tuple[List[Dict], List[Dict]]:
    nodes = existing + candidates
    node_rows: List[Dict] = []
    for n in nodes:
        d = min(haversine_km(n["lat"], n["lon"], e["lat"], e["lon"]) for e in existing)
        node_rows.append(
            {
                "site_id": n["site_id"],
                "lat": n["lat"],
                "lon": n["lon"],
                "is_existing": n["is_existing"],
                "community_id": community_map.get(n["site_id"], -1),
                "distance_to_nearest_existing_km": d,
                "node_weight": n.get("learned_node_score", ""),
                "population_score": n.get("population_score", ""),
            }
        )

    by_comm: Dict[int, Dict] = {}
    for row in node_rows:
        cid = int(row["community_id"])
        if cid not in by_comm:
            by_comm[cid] = {"community_id": cid, "node_count": 0, "existing_count": 0, "dist": [], "w": []}
        by_comm[cid]["node_count"] += 1
        if row["is_existing"]:
            by_comm[cid]["existing_count"] += 1
        by_comm[cid]["dist"].append(float(row["distance_to_nearest_existing_km"]))
        if row["node_weight"] != "":
            by_comm[cid]["w"].append(float(row["node_weight"]))

    cutoff = percentile([float(c["learned_node_score"]) for c in candidates], 0.65)
    summary: List[Dict] = []
    for cid, agg in by_comm.items():
        avg_dist = sum(agg["dist"]) / len(agg["dist"]) if agg["dist"] else 0.0
        avg_w = sum(agg["w"]) / len(agg["w"]) if agg["w"] else 0.0
        underserved = ((avg_dist >= cfg.underserved_distance_km) or (agg["existing_count"] == 0)) and (avg_w >= cutoff)
        summary.append(
            {
                "community_id": cid,
                "node_count": agg["node_count"],
                "existing_count": agg["existing_count"],
                "avg_dist_to_existing_km": avg_dist,
                "avg_node_weight": avg_w,
                "underserved": underserved,
            }
        )

    summary.sort(key=lambda x: x["community_id"])
    return node_rows, summary


def write_csv(path: Path, rows: List[Dict], fields: List[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def to_geojson(rows: List[Dict], prop_fields: List[str]) -> Dict:
    feats = []
    for row in rows:
        feats.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(row["lon"]), float(row["lat"])]},
                "properties": {k: row.get(k, None) for k in prop_fields},
            }
        )
    return {"type": "FeatureCollection", "features": feats}


def run_pipeline(data_dir: Path, output_dir: Path, cfg: Config) -> None:
    existing, candidates, data_mode = load_data(data_dir, cfg)
    engineer_features(existing, candidates, cfg)

    scores, meta = train_gnn(candidates, cfg)
    for i, c in enumerate(candidates):
        c["learned_node_score"] = scores[i]

    nearest = candidate_distance_stats(existing, candidates)
    effective_radius, baseline_coverage, tuned = compute_effective_service_radius(cfg, nearest)

    full_graph, edge_count = build_full_graph(existing, candidates, cfg.edge_radius_km)
    community_map = connected_components(full_graph)
    node_clusters, community_summary = community_metrics(existing, candidates, community_map, cfg)

    scenarios = [10, 25, 50]
    scenario_rows: List[Dict] = []
    scenario_recs: Dict[int, List[Dict]] = {}
    for budget in scenarios:
        recs = greedy_facility_expansion(existing, candidates, budget, effective_radius)
        scenario_recs[budget] = recs
        scenario_rows.append(
            {
                "stations_added": budget,
                "selected_sites": len(recs),
                "coverage_ratio": recs[-1]["cumulative_coverage"] if recs else 0.0,
                "aggregate_marginal_demand_gain": sum(r["marginal_demand_gain"] for r in recs),
                "baseline_coverage_ratio": baseline_coverage,
                "effective_service_radius_km": effective_radius,
            }
        )

    ranked = scenario_recs[50]
    node_scores = [
        {
            "site_id": c["site_id"],
            "learned_node_score": c["learned_node_score"],
            "demand_weight": c["demand_weight"],
            "population_score": c.get("population_score", ""),
        }
        for c in candidates
    ]

    model_metadata = {
        **meta,
        "data_mode": data_mode,
        "baseline_coverage_ratio": baseline_coverage,
        "effective_service_radius_km": effective_radius,
        "service_radius_tuned": tuned,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(
        output_dir / "ranked_recommendations.csv",
        ranked,
        ["rank", "site_id", "lat", "lon", "node_weight", "population_score", "marginal_demand_gain", "cumulative_coverage"],
    )
    write_csv(
        output_dir / "scenario_summary.csv",
        scenario_rows,
        ["stations_added", "selected_sites", "coverage_ratio", "aggregate_marginal_demand_gain", "baseline_coverage_ratio", "effective_service_radius_km"],
    )
    write_csv(
        output_dir / "node_clusters.csv",
        node_clusters,
        ["site_id", "lat", "lon", "is_existing", "community_id", "distance_to_nearest_existing_km", "node_weight", "population_score"],
    )
    write_csv(
        output_dir / "underserved_communities.csv",
        community_summary,
        ["community_id", "node_count", "existing_count", "avg_dist_to_existing_km", "avg_node_weight", "underserved"],
    )
    write_csv(
        output_dir / "node_scores.csv",
        node_scores,
        ["site_id", "learned_node_score", "demand_weight", "population_score"],
    )

    rec_geo = to_geojson(ranked, ["rank", "site_id", "node_weight", "population_score", "marginal_demand_gain", "cumulative_coverage"])
    clu_geo = to_geojson(node_clusters, ["site_id", "community_id", "is_existing", "distance_to_nearest_existing_km", "node_weight", "population_score"])
    with (output_dir / "recommendations.geojson").open("w", encoding="utf-8") as f:
        json.dump(rec_geo, f, indent=2)
    with (output_dir / "clusters.geojson").open("w", encoding="utf-8") as f:
        json.dump(clu_geo, f, indent=2)
    with (output_dir / "model_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(model_metadata, f, indent=2)

    print("=== EV Charging Expansion Results (GNN) ===")
    print(f"Model: {cfg.model_type}")
    print(f"Nodes in graph: {len(existing) + len(candidates)}")
    print(f"Edges in graph: {edge_count}")
    if tuned:
        print(f"Service radius tuned: {cfg.service_radius_km:.3f} -> {effective_radius:.3f} km")
    print("\nScenario summary:")
    for row in scenario_rows:
        print(
            f"  add={row['stations_added']:>2} | selected={row['selected_sites']:>2} "
            f"| coverage={row['coverage_ratio']:.3f} | demand_gain={row['aggregate_marginal_demand_gain']:.3f}"
        )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="GNN-based EV charging expansion optimization")
    p.add_argument("--data-dir", type=Path, default=Path("data"))
    p.add_argument("--output-dir", type=Path, default=Path("outputs_gnn"))
    p.add_argument("--model", choices=["gcn", "graphsage", "gat"], default="gcn")
    p.add_argument("--edge-radius-km", type=float, default=3.0)
    p.add_argument("--service-radius-km", type=float, default=2.5)
    p.add_argument("--density-radius-km", type=float, default=2.0)
    p.add_argument("--underserved-distance-km", type=float, default=2.2)
    p.add_argument("--min-uncovered-ratio", type=float, default=0.15)
    p.add_argument("--hidden-dim", type=int, default=32)
    p.add_argument("--epochs", type=int, default=250)
    p.add_argument("--lr", type=float, default=0.01)
    p.add_argument("--weight-decay", type=float, default=1e-4)
    p.add_argument("--dropout", type=float, default=0.15)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cfg = Config(
        edge_radius_km=args.edge_radius_km,
        service_radius_km=args.service_radius_km,
        density_radius_km=args.density_radius_km,
        underserved_distance_km=args.underserved_distance_km,
        min_uncovered_ratio=args.min_uncovered_ratio,
        hidden_dim=args.hidden_dim,
        epochs=args.epochs,
        lr=args.lr,
        weight_decay=args.weight_decay,
        dropout=args.dropout,
        model_type=args.model,
        seed=args.seed,
    )
    run_pipeline(args.data_dir, args.output_dir, cfg)


if __name__ == "__main__":
    main()
