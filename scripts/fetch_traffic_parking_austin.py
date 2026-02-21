#!/usr/bin/env python3
"""
Fetch Austin traffic and parking data from City of Austin Open Data (Socrata API),
census tract population from COA ArcGIS FeatureServer, and radar traffic volumes,
then build existing_stations.csv + candidate_sites.csv for ev_network_optimization.py.

Data sources:
- Traffic incidents: Real-Time Traffic Incident Reports (dx9v-zd7x)
- Parking: Parking Lot Entrances and Exits (ij6a-fwpi) - candidate expansion sites
- EV: Uses existing data/ocm_austin.json (Open Charge Map)
- Census: COA 2020 Census Tracts (ArcGIS FeatureServer) - residential population
- Radar volumes: Radar Traffic Counts (i626-g7ub) + Travel Sensors (6yd9-yz29)
"""

from __future__ import annotations

import json
import math
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context()

# Austin Open Data (Socrata) - no API key required for public datasets
BASE_URL = "https://data.austintexas.gov/resource"
TRAFFIC_INCIDENTS_ID = "dx9v-zd7x"  # Real-Time Traffic Incident Reports (lat, lon)
PARKING_ENTRANCES_ID = "ij6a-fwpi"  # Parking Lot Entrances and Exits (lat, lon)
RADAR_COUNTS_ID = "i626-g7ub"       # Radar Traffic Counts (volume per sensor)
TRAVEL_SENSORS_ID = "6yd9-yz29"     # Travel Sensors (sensor locations)

# COA 2020 Census Tracts (ArcGIS FeatureServer) - public, no key required
CENSUS_ARCGIS_URL = (
    "https://services.arcgis.com/0L95CJ0VTaxqcmED/ArcGIS/rest/services/"
    "COA_2020_Census_Tracts_Data/FeatureServer/0/query"
)

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
CENSUS_CSV = OUTPUT_DIR / "census_tracts_austin.csv"
RADAR_CSV = OUTPUT_DIR / "radar_volumes_austin.csv"

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
        with urllib.request.urlopen(req, timeout=60, context=_SSL_CTX) as resp:
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


def fetch_arcgis_census_tracts() -> list[dict]:
    """Fetch 2020 census tract population data from COA ArcGIS FeatureServer."""
    print("Fetching census tract population (ArcGIS FeatureServer)...")
    tracts: list[dict] = []
    offset = 0
    page_size = 1000
    while True:
        params = urllib.parse.urlencode({
            "where": "1=1",
            "outFields": "POP100,HU100,INTPTLAT,INTPTLON,TOT_AREA_SQKM,GEOID20,NAME20",
            "returnGeometry": "false",
            "resultOffset": str(offset),
            "resultRecordCount": str(page_size),
            "f": "json",
        })
        url = f"{CENSUS_ARCGIS_URL}?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "ev-austin-etl/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=60, context=_SSL_CTX) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            print(f"  Warning: census fetch failed at offset {offset}: {e}")
            break

        features = data.get("features", [])
        if not features:
            break

        for feat in features:
            attrs = feat.get("attributes", {})
            lat = attrs.get("INTPTLAT")
            lon = attrs.get("INTPTLON")
            pop = attrs.get("POP100")
            if lat is None or lon is None or pop is None:
                continue
            try:
                lat, lon, pop = float(lat), float(lon), int(pop)
            except (TypeError, ValueError):
                continue
            if not (AUSTIN_BBOX["min_lat"] <= lat <= AUSTIN_BBOX["max_lat"]
                    and AUSTIN_BBOX["min_lon"] <= lon <= AUSTIN_BBOX["max_lon"]):
                continue
            tracts.append({
                "geoid": attrs.get("GEOID20", ""),
                "name": attrs.get("NAME20", ""),
                "lat": lat,
                "lon": lon,
                "pop": pop,
                "housing_units": int(attrs.get("HU100", 0)),
                "area_sqkm": float(attrs.get("TOT_AREA_SQKM", 1.0)),
            })

        if not data.get("exceededTransferLimit", False):
            break
        offset += page_size

    print(f"  -> {len(tracts)} census tracts in Austin bbox")
    return tracts


def fetch_radar_sensors() -> dict[str, dict]:
    """Fetch radar sensor locations from Socrata Travel Sensors dataset.
    Returns {kits_id: {lat, lon, name}} for RADAR-type sensors only."""
    print("Fetching radar sensor locations (Austin Open Data)...")
    rows = fetch_socrata(TRAVEL_SENSORS_ID, limit=5000)
    sensors: dict[str, dict] = {}
    for r in rows:
        if r.get("sensor_type") != "RADAR":
            continue
        kits_id = r.get("kits_id")
        if not kits_id:
            continue
        loc = r.get("location")
        if not isinstance(loc, dict) or "coordinates" not in loc:
            continue
        coords = loc["coordinates"]
        if len(coords) < 2:
            continue
        try:
            lon, lat = float(coords[0]), float(coords[1])
        except (TypeError, ValueError):
            continue
        if not (AUSTIN_BBOX["min_lat"] <= lat <= AUSTIN_BBOX["max_lat"]
                and AUSTIN_BBOX["min_lon"] <= lon <= AUSTIN_BBOX["max_lon"]):
            continue
        sensors[str(kits_id)] = {
            "lat": lat,
            "lon": lon,
            "name": r.get("location_name", ""),
        }
    print(f"  -> {len(sensors)} RADAR sensors with locations")
    return sensors


def fetch_radar_volumes(sensors: dict[str, dict]) -> list[dict]:
    """Fetch radar traffic counts and aggregate average volume per sensor location.
    Joins with sensor locations via int_id -> kits_id."""
    print("Fetching radar traffic volumes (Austin Open Data)...")
    volume_sums: dict[str, list[float]] = {}
    offset = 0
    batch_size = 50000
    total_rows = 0

    while True:
        rows = fetch_socrata(RADAR_COUNTS_ID, limit=batch_size, offset=offset)
        if not rows:
            break
        total_rows += len(rows)
        for r in rows:
            int_id = r.get("int_id")
            vol = r.get("volume")
            if int_id is None or vol is None:
                continue
            try:
                vol_f = float(vol)
            except (TypeError, ValueError):
                continue
            if vol_f <= 0:
                continue
            int_id_str = str(int_id)
            if int_id_str not in volume_sums:
                volume_sums[int_id_str] = []
            volume_sums[int_id_str].append(vol_f)

        if len(rows) < batch_size:
            break
        offset += batch_size
        print(f"  ... fetched {total_rows} radar rows so far")

    print(f"  -> {total_rows} total radar count rows across {len(volume_sums)} intersections")

    results: list[dict] = []
    for int_id, volumes in volume_sums.items():
        sensor = sensors.get(int_id)
        if not sensor:
            continue
        avg_vol = sum(volumes) / len(volumes)
        results.append({
            "int_id": int_id,
            "lat": sensor["lat"],
            "lon": sensor["lon"],
            "name": sensor["name"],
            "avg_volume": avg_vol,
            "sample_count": len(volumes),
        })

    print(f"  -> {len(results)} sensor locations matched with volume data")
    return results


def compute_nearby_population(
    lat: float, lon: float, tracts: list[dict], radius_km: float
) -> float:
    """Sum population of census tracts whose centroids fall within radius."""
    return sum(
        t["pop"] for t in tracts
        if haversine_km(lat, lon, t["lat"], t["lon"]) <= radius_km
    )


def compute_nearby_traffic_volume(
    lat: float, lon: float, sensor_volumes: list[dict], radius_km: float
) -> float:
    """Inverse-distance-weighted average of nearby sensor volumes.
    Closer sensors contribute more. Returns 0 if no sensors are nearby."""
    total_weight = 0.0
    weighted_vol = 0.0
    for sv in sensor_volumes:
        d = haversine_km(lat, lon, sv["lat"], sv["lon"])
        if d <= radius_km:
            w = 1.0 / max(d, 0.05)
            weighted_vol += w * sv["avg_volume"]
            total_weight += w
    return weighted_vol / total_weight if total_weight > 0 else 0.0


def count_nearby_incidents(lat: float, lon: float, incidents: list[dict], radius_km: float) -> int:
    return sum(1 for i in incidents if haversine_km(lat, lon, i["lat"], i["lon"]) <= radius_km)


def min_max_scale(values: list[float]) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if math.isclose(lo, hi):
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def build_candidates(
    parking: list[dict],
    incidents: list[dict],
    existing: list[dict],
    tracts: list[dict] | None = None,
    sensor_volumes: list[dict] | None = None,
) -> list[dict]:
    tracts = tracts or []
    sensor_volumes = sensor_volumes or []
    has_radar = len(sensor_volumes) > 0
    has_census = len(tracts) > 0

    rows = []
    for i, p in enumerate(parking):
        lat, lon = p["lat"], p["lon"]
        incident_count = count_nearby_incidents(lat, lon, incidents, TRAFFIC_RADIUS_KM)
        radar_vol = compute_nearby_traffic_volume(lat, lon, sensor_volumes, TRAFFIC_RADIUS_KM) if has_radar else 0.0
        pop_nearby = compute_nearby_population(lat, lon, tracts, TRAFFIC_RADIUS_KM) if has_census else 0.0

        rows.append({
            "site_id": f"PK_{p.get('parking_lo', i)}",
            "lat": lat,
            "lon": lon,
            "traffic_score_raw": radar_vol if has_radar else float(incident_count),
            "incident_density_raw": float(incident_count),
            "pop_density_raw": pop_nearby,
            "parking_score": 100.0,
        })

    traffic_scaled = min_max_scale([r["traffic_score_raw"] for r in rows])
    incident_scaled = min_max_scale([r["incident_density_raw"] for r in rows])
    pop_scaled = min_max_scale([r["pop_density_raw"] for r in rows])

    for i, r in enumerate(rows):
        r["traffic_score"] = traffic_scaled[i] * 80 + 20

        if has_census:
            blended = 0.6 * pop_scaled[i] + 0.4 * incident_scaled[i]
        else:
            blended = incident_scaled[i]
        r["demand_proxy"] = blended * 80 + 20

        del r["traffic_score_raw"]
        del r["incident_density_raw"]
        del r["pop_density_raw"]

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
    print("=== Austin EV Data ETL: OCM + Traffic + Parking + Census + Radar ===\n")

    ocm = load_ocm_stations(OCM_PATH)
    existing = ocm_to_existing(ocm)
    incidents = load_traffic_incidents()
    parking = load_parking_lots()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Export traffic incidents
    traffic_for_csv = [
        {k: str(rec.get(k, "")) for k in TRAFFIC_CSV_FIELDS}
        for rec in incidents
    ]
    write_csv(TRAFFIC_CSV, traffic_for_csv, TRAFFIC_CSV_FIELDS)
    with TRAFFIC_JSON.open("w", encoding="utf-8") as f:
        json.dump(incidents, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(incidents)} records to {TRAFFIC_JSON}")

    # Fetch census tract population
    tracts = fetch_arcgis_census_tracts()
    if tracts:
        write_csv(
            CENSUS_CSV, tracts,
            ["geoid", "name", "lat", "lon", "pop", "housing_units", "area_sqkm"],
        )

    # Fetch radar traffic volumes (sensor locations + counts)
    sensors = fetch_radar_sensors()
    sensor_volumes = fetch_radar_volumes(sensors) if sensors else []
    if sensor_volumes:
        write_csv(
            RADAR_CSV, sensor_volumes,
            ["int_id", "lat", "lon", "name", "avg_volume", "sample_count"],
        )

    if not parking:
        raise SystemExit("No parking locations fetched. Check API availability.")

    candidates = build_candidates(
        parking, incidents, existing,
        tracts=tracts,
        sensor_volumes=sensor_volumes,
    )

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
