#!/usr/bin/env python3
"""
Fetch Austin traffic and parking data from City of Austin Open Data (Socrata API)
and build existing_stations.csv + candidate_sites.csv for ev_network_optimization.py.

Data sources:
- Traffic: Real-Time Traffic Incident Reports (dx9v-zd7x) - demand proxy (incident density)
- Parking: Parking Lot Entrances and Exits (ij6a-fwpi) - candidate expansion sites
- EV: Uses existing data/ocm_austin.json (Open Charge Map)
"""

from __future__ import annotations

import json
import math
import os
import urllib.error
import urllib.request
from pathlib import Path

# Austin Open Data (Socrata) - no API key required for public datasets
BASE_URL = "https://data.austintexas.gov/resource"
TRAFFIC_INCIDENTS_ID = "dx9v-zd7x"  # Real-Time Traffic Incident Reports (lat, lon)
PARKING_ENTRANCES_ID = "ij6a-fwpi"  # Parking Lot Entrances and Exits (lat, lon)

# Austin bbox (approximate) for filtering
AUSTIN_BBOX = {
    "min_lat": 30.0,
    "max_lat": 30.6,
    "min_lon": -98.0,
    "max_lon": -97.5,
}

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
OCM_PATH = OUTPUT_DIR / "ocm_austin.json"
EXISTING_CSV = OUTPUT_DIR / "existing_stations.csv"
CANDIDATES_CSV = OUTPUT_DIR / "candidate_sites.csv"
TRAFFIC_CSV = OUTPUT_DIR / "traffic_incidents_austin.csv"
TRAFFIC_JSON = OUTPUT_DIR / "traffic_incidents_austin.json"

# Traffic CSV columns (excludes Socrata internal fields)
TRAFFIC_CSV_FIELDS = [
    "traffic_report_id",
    "published_date",
    "issue_reported",
    "latitude",
    "longitude",
    "address",
    "traffic_report_status",
    "agency",
]

# Radius in km for counting nearby traffic incidents
TRAFFIC_RADIUS_KM = 2.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = p2 - p1
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def fetch_socrata(dataset_id: str, limit: int = 50000, offset: int = 0) -> list[dict]:
    url = f"{BASE_URL}/{dataset_id}.json?$limit={limit}&$offset={offset}"
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "ev-austin-etl/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code} fetching {dataset_id}: {e}") from e
    except urllib.error.URLError as e:
        raise SystemExit(f"Network error fetching {dataset_id}: {e}") from e


def load_ocm_stations(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"OCM data not found: {path}. Run scripts/fetch_ocm_austin.py first.")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def ocm_to_existing(ocm_records: list[dict]) -> list[dict]:
    rows = []
    for rec in ocm_records:
        addr = rec.get("AddressInfo") or {}
        lat = addr.get("Latitude")
        lon = addr.get("Longitude")
        if lat is None or lon is None:
            continue
        if not (AUSTIN_BBOX["min_lat"] <= lat <= AUSTIN_BBOX["max_lat"] and
                AUSTIN_BBOX["min_lon"] <= lon <= AUSTIN_BBOX["max_lon"]):
            continue

        conns = rec.get("Connections") or []
        total_qty = sum(c.get("Quantity", 1) for c in conns)
        charger_count = total_qty or 1

        dc_fast = any(
            (c.get("Level") or {}).get("IsFastChargeCapable") or (c.get("Level") or {}).get("Title", "").lower().find("dc") >= 0
            for c in conns
        )
        charger_type = "DCFC" if dc_fast else "L2"

        op = rec.get("OperatorInfo") or {}
        network = op.get("Title", "unknown") if isinstance(op, dict) else "unknown"

        rows.append({
            "site_id": f"OCM_{rec.get('ID', len(rows))}",
            "lat": lat,
            "lon": lon,
            "charger_count": charger_count,
            "charger_type": charger_type,
            "network": str(network),
        })
    return rows


def _is_socrata_internal_key(key: str) -> bool:
    return key.startswith(":@computed_region") or key == "location"


def load_traffic_incidents() -> list[dict]:
    print("Fetching traffic incidents (Austin Open Data)...")
    rows = fetch_socrata(TRAFFIC_INCIDENTS_ID, limit=10000)
    records = []
    for r in rows:
        lat = r.get("latitude")
        lon = r.get("longitude")
        if lat is None or lon is None:
            loc = r.get("location")
            if isinstance(loc, dict) and "coordinates" in loc:
                coords = loc["coordinates"]
                if len(coords) >= 2:
                    lon, lat = float(coords[0]), float(coords[1])
                else:
                    continue
            else:
                continue
        try:
            lat, lon = float(lat), float(lon)
        except (TypeError, ValueError):
            continue
        if not (AUSTIN_BBOX["min_lat"] <= lat <= AUSTIN_BBOX["max_lat"] and
                AUSTIN_BBOX["min_lon"] <= lon <= AUSTIN_BBOX["max_lon"]):
            continue
        cleaned = {k: v for k, v in r.items() if not _is_socrata_internal_key(k)}
        cleaned["latitude"] = lat
        cleaned["longitude"] = lon
        cleaned["lat"] = lat
        cleaned["lon"] = lon
        records.append(cleaned)
    print(f"  -> {len(records)} incidents in Austin bbox")
    return records


def load_parking_lots() -> list[dict]:
    print("Fetching parking lot entrances (Austin Open Data)...")
    rows = fetch_socrata(PARKING_ENTRANCES_ID, limit=5000)
    points = []
    seen = set()
    for r in rows:
        lat = r.get("latitude")
        lon = r.get("longitude")
        if lat is None or lon is None:
            loc = r.get("location")
            if isinstance(loc, dict):
                lat = loc.get("latitude")
                lon = loc.get("longitude")
        if lat is None or lon is None:
            continue
        try:
            lat, lon = float(lat), float(lon)
        except (TypeError, ValueError):
            continue
        if not (AUSTIN_BBOX["min_lat"] <= lat <= AUSTIN_BBOX["max_lat"] and
                AUSTIN_BBOX["min_lon"] <= lon <= AUSTIN_BBOX["max_lon"]):
            continue
        key = (round(lat, 5), round(lon, 5))
        if key in seen:
            continue
        seen.add(key)
        parking_lo = r.get("parking_lo", "?")
        points.append({"lat": lat, "lon": lon, "parking_lo": str(parking_lo)})
    print(f"  -> {len(points)} parking locations in Austin bbox")
    return points


def count_nearby_incidents(lat: float, lon: float, incidents: list[dict], radius_km: float) -> int:
    return sum(1 for i in incidents if haversine_km(lat, lon, i["lat"], i["lon"]) <= radius_km)


def min_max_scale(values: list[float]) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if math.isclose(lo, hi):
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def build_candidates(parking: list[dict], incidents: list[dict], existing: list[dict]) -> list[dict]:
    rows = []
    for i, p in enumerate(parking):
        lat, lon = p["lat"], p["lon"]
        incident_count = count_nearby_incidents(lat, lon, incidents, TRAFFIC_RADIUS_KM)
        rows.append({
            "site_id": f"PK_{p.get('parking_lo', i)}",
            "lat": lat,
            "lon": lon,
            "traffic_score": float(incident_count),
            "parking_score": 100.0,  # Parking lots = high parking availability
            "demand_proxy": float(incident_count),
        })

    traffic_raw = [r["traffic_score"] for r in rows]
    traffic_scaled = min_max_scale(traffic_raw)
    demand_scaled = min_max_scale([r["demand_proxy"] for r in rows])
    for i, r in enumerate(rows):
        r["traffic_score"] = traffic_scaled[i] * 80 + 20
        r["demand_proxy"] = demand_scaled[i] * 80 + 20

    return rows


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    import csv
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})
    print(f"Wrote {len(rows)} rows to {path}")


def main() -> None:
    print("=== Austin EV Data ETL: OCM + Traffic + Parking ===\n")

    ocm = load_ocm_stations(OCM_PATH)
    existing = ocm_to_existing(ocm)
    incidents = load_traffic_incidents()
    parking = load_parking_lots()

    # Export traffic incidents for push/sharing
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    traffic_for_csv = [
        {k: str(rec.get(k, "")) for k in TRAFFIC_CSV_FIELDS}
        for rec in incidents
    ]
    write_csv(TRAFFIC_CSV, traffic_for_csv, TRAFFIC_CSV_FIELDS)
    with TRAFFIC_JSON.open("w", encoding="utf-8") as f:
        json.dump(incidents, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(incidents)} records to {TRAFFIC_JSON}")

    if not parking:
        raise SystemExit("No parking locations fetched. Check API availability.")

    candidates = build_candidates(parking, incidents, existing)

    write_csv(
        EXISTING_CSV,
        existing,
        ["site_id", "lat", "lon", "charger_count", "charger_type", "network"],
    )
    write_csv(
        CANDIDATES_CSV,
        candidates,
        ["site_id", "lat", "lon", "traffic_score", "parking_score", "demand_proxy"],
    )

    print(f"\nDone. Run: python ev_network_optimization.py --data-dir data --output-dir outputs")


if __name__ == "__main__":
    main()
