#!/usr/bin/env python3
import json
import os
import time
import urllib.parse
import urllib.request
from typing import Dict, List

API_URL = "https://api.openchargemap.io/v3/poi/"

# Approximate Austin city limits bounding box (lat_min, lon_min, lat_max, lon_max)
AUSTIN_BBOX = (30.0987, -97.9384, 30.5169, -97.5684)

OUTPUT_JSON = "data/ocm_austin.json"
OUTPUT_GEOJSON = "data/ocm_austin.geojson"


def load_env(path: str = ".env") -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not os.path.exists(path):
        return env
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    return env


def fetch_tile(api_key: str, bbox: str, max_results: int = 2000) -> List[dict]:
    params = {
        "boundingbox": bbox,
        "maxresults": str(max_results),
        "compact": "false",
        "verbose": "false",
        "key": api_key,
    }
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={
            "X-API-Key": api_key,
            "User-Agent": "ocm-austin-fetch/1.0 (+https://openchargemap.org)",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        return json.loads(data)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise SystemExit(f"OCM HTTP {e.code} for bbox {bbox}. Body: {body[:500]}") from e


def fetch_radius(api_key: str, latitude: float, longitude: float, distance_miles: float, max_results: int = 2000) -> List[dict]:
    params = {
        "latitude": f"{latitude}",
        "longitude": f"{longitude}",
        "distance": f"{distance_miles}",
        "distanceunit": "Miles",
        "maxresults": str(max_results),
        "compact": "false",
        "verbose": "false",
        "key": api_key,
    }
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={
            "X-API-Key": api_key,
            "User-Agent": "ocm-austin-fetch/1.0 (+https://openchargemap.org)",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        return json.loads(data)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise SystemExit(
            f"OCM HTTP {e.code} for lat/lon {latitude},{longitude}. Body: {body[:500]}"
        ) from e


def tile_bbox(bbox, rows=3, cols=3) -> List[str]:
    lat_min, lon_min, lat_max, lon_max = bbox
    lat_step = (lat_max - lat_min) / rows
    lon_step = (lon_max - lon_min) / cols
    tiles = []
    for r in range(rows):
        for c in range(cols):
            t_lat_min = lat_min + r * lat_step
            t_lat_max = lat_min + (r + 1) * lat_step
            t_lon_min = lon_min + c * lon_step
            t_lon_max = lon_min + (c + 1) * lon_step
            # Some OCM deployments return empty for boundingbox; keep for optional use.
            tiles.append((t_lat_min, t_lon_min, t_lat_max, t_lon_max))
    return tiles


def grid_centers(bbox, rows=3, cols=3) -> List[tuple]:
    lat_min, lon_min, lat_max, lon_max = bbox
    lat_step = (lat_max - lat_min) / rows
    lon_step = (lon_max - lon_min) / cols
    centers = []
    for r in range(rows):
        for c in range(cols):
            lat = lat_min + (r + 0.5) * lat_step
            lon = lon_min + (c + 0.5) * lon_step
            centers.append((lat, lon, lat_step, lon_step))
    return centers


def to_geojson(items: List[dict]) -> dict:
    features = []
    for item in items:
        addr = item.get("AddressInfo") or {}
        lat = addr.get("Latitude")
        lon = addr.get("Longitude")
        if lat is None or lon is None:
            continue
        properties = {
            "ID": item.get("ID"),
            "UUID": item.get("UUID"),
            "NumberOfPoints": item.get("NumberOfPoints"),
            "UsageType": item.get("UsageType"),
            "OperatorInfo": item.get("OperatorInfo"),
            "Connections": item.get("Connections"),
            "AddressInfo": addr,
        }
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": properties,
            }
        )
    return {"type": "FeatureCollection", "features": features}


def main() -> None:
    env = load_env()
    api_key = os.environ.get("OCM_API_KEY") or env.get("OCM_API_KEY")
    if not api_key:
        raise SystemExit("Missing OCM_API_KEY. Set it in .env or your environment.")

    rows, cols = 3, 3
    centers = grid_centers(AUSTIN_BBOX, rows=rows, cols=cols)

    # Approximate distance to cover each grid cell (miles)
    lat_mid = (AUSTIN_BBOX[0] + AUSTIN_BBOX[2]) / 2
    miles_per_lat = 69.0
    miles_per_lon = 69.0 * abs(__import__("math").cos(__import__("math").radians(lat_mid)))

    all_items: Dict[int, dict] = {}
    for i, (lat, lon, lat_step, lon_step) in enumerate(centers, 1):
        cell_height_mi = lat_step * miles_per_lat
        cell_width_mi = lon_step * miles_per_lon
        radius_mi = max(cell_height_mi, cell_width_mi) / 2 * 1.1
        print(f"Fetching tile {i}/{len(centers)}: {lat},{lon} (r={radius_mi:.2f} mi)")
        items = fetch_radius(api_key, lat, lon, radius_mi)
        print(f"  -> {len(items)} results")
        for item in items:
            item_id = item.get("ID")
            if item_id is not None:
                all_items[item_id] = item
        time.sleep(0.5)

    items_list = list(all_items.values())
    items_list.sort(key=lambda x: x.get("ID", 0))

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(items_list, f, ensure_ascii=False, indent=2)

    geojson = to_geojson(items_list)
    with open(OUTPUT_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(items_list)} records to {OUTPUT_JSON}")
    print(f"Wrote {len(geojson['features'])} features to {OUTPUT_GEOJSON}")


if __name__ == "__main__":
    main()
