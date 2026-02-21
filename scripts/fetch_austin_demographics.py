#!/usr/bin/env python3
"""
Generate higher-precision population estimates for Austin using:
1) City of Austin Neighborhood Planning Areas (NPA) polygons (curated boundary layer)
2) ACS 5-year block group population (B01003_001E)
3) TIGERweb block group internal point (INTPTLAT/INTPTLON) for spatial assignment

Outputs:
- data/austin_npa.geojson
- data/austin_npa_population.csv
- data/austin_blockgroup_population.csv (debug/trace)
"""

import argparse
import csv
import json
import math
import os
import sys
import urllib.parse
import urllib.request
from typing import Dict, Iterable, List, Tuple


NPA_LAYER_URL = (
    "https://maps.austintexas.gov/gis/rest/Shared/Zoning_2/MapServer/20/query"
)
TIGER_BG_LAYER_URL = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/11/query"
)
ACS_API_URL = "https://api.census.gov/data/2023/acs/acs5"

DEFAULT_GEOJSON_OUT = "data/austin_npa.geojson"
DEFAULT_NPA_CSV_OUT = "data/austin_npa_population.csv"
DEFAULT_BG_CSV_OUT = "data/austin_blockgroup_population.csv"

# Counties overlapping Austin city limits (FIPS)
DEFAULT_COUNTIES = ["453", "491", "209", "021", "055"]  # Travis, Williamson, Hays, Bastrop, Caldwell


def http_get_json(url: str) -> dict | list:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def fetch_npa_geojson() -> dict:
    params = {
        "where": "1=1",
        "outFields": "*",
        "f": "geojson",
        "outSR": "4326",
    }
    url = f"{NPA_LAYER_URL}?{urllib.parse.urlencode(params)}"
    return http_get_json(url)


def fetch_tiger_block_groups(counties: Iterable[str]) -> List[dict]:
    # Grab GEOID + internal point lat/lon for all block groups in selected counties
    where = "STATE='48' AND COUNTY IN ({})".format(
        ",".join(f"'{c}'" for c in counties)
    )
    out_fields = "GEOID,STATE,COUNTY,TRACT,BLKGRP,INTPTLAT,INTPTLON"
    result_offset = 0
    result_record_count = 2000
    all_features: List[dict] = []

    while True:
        params = {
            "where": where,
            "outFields": out_fields,
            "returnGeometry": "false",
            "f": "json",
            "resultOffset": str(result_offset),
            "resultRecordCount": str(result_record_count),
        }
        url = f"{TIGER_BG_LAYER_URL}?{urllib.parse.urlencode(params)}"
        data = http_get_json(url)
        features = data.get("features", [])
        if not features:
            break
        all_features.extend(features)
        result_offset += result_record_count
        if len(features) < result_record_count:
            break

    return all_features


def fetch_acs_population(counties: Iterable[str]) -> Dict[str, int]:
    # ACS B01003_001E: total population
    pop_by_geoid: Dict[str, int] = {}
    for county in counties:
        params = {
            "get": "B01003_001E",
            "for": "block group:*",
            "in": f"state:48 county:{county}",
        }
        url = f"{ACS_API_URL}?{urllib.parse.urlencode(params)}"
        rows = http_get_json(url)
        header = rows[0]
        idx_val = header.index("B01003_001E")
        idx_state = header.index("state")
        idx_county = header.index("county")
        idx_tract = header.index("tract")
        idx_bg = header.index("block group")
        for r in rows[1:]:
            geoid = f"{r[idx_state]}{r[idx_county]}{r[idx_tract]}{r[idx_bg]}"
            try:
                pop_by_geoid[geoid] = int(r[idx_val])
            except ValueError:
                pop_by_geoid[geoid] = 0
    return pop_by_geoid


def point_in_ring(x: float, y: float, ring: List[Tuple[float, float]]) -> bool:
    inside = False
    n = len(ring)
    if n < 3:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        intersects = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def point_in_polygon(x: float, y: float, coords: list) -> bool:
    # coords: list of rings (outer + holes)
    outer = coords[0]
    if not point_in_ring(x, y, outer):
        return False
    # if in any hole, exclude
    for hole in coords[1:]:
        if point_in_ring(x, y, hole):
            return False
    return True


def point_in_geometry(x: float, y: float, geom: dict) -> bool:
    gtype = geom.get("type")
    coords = geom.get("coordinates")
    if gtype == "Polygon":
        return point_in_polygon(x, y, coords)
    if gtype == "MultiPolygon":
        for poly in coords:
            if point_in_polygon(x, y, poly):
                return True
        return False
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Austin NPA population from ACS block group data."
    )
    parser.add_argument("--geojson-out", default=DEFAULT_GEOJSON_OUT)
    parser.add_argument("--npa-csv-out", default=DEFAULT_NPA_CSV_OUT)
    parser.add_argument("--bg-csv-out", default=DEFAULT_BG_CSV_OUT)
    parser.add_argument(
        "--counties",
        default=",".join(DEFAULT_COUNTIES),
        help="Comma-separated county FIPS (default includes Travis/Williamson/Hays/Bastrop/Caldwell).",
    )
    args = parser.parse_args()

    counties = [c.strip() for c in args.counties.split(",") if c.strip()]
    os.makedirs(os.path.dirname(args.geojson_out), exist_ok=True)

    print("Fetching NPA polygons...")
    npa_geojson = fetch_npa_geojson()
    npa_features = npa_geojson.get("features", [])
    print(f"Loaded {len(npa_features)} NPA polygons")

    print("Fetching block group centroids (TIGERweb)...")
    bg_features = fetch_tiger_block_groups(counties)
    print(f"Loaded {len(bg_features)} block group points")

    print("Fetching ACS block group population...")
    pop_by_geoid = fetch_acs_population(counties)
    print(f"Loaded population for {len(pop_by_geoid)} block groups")

    # Build block group rows with lat/lon + population
    block_groups: List[dict] = []
    for feat in bg_features:
        attrs = feat.get("attributes", {})
        geoid = attrs.get("GEOID")
        lat = attrs.get("INTPTLAT")
        lon = attrs.get("INTPTLON")
        if geoid is None or lat is None or lon is None:
            continue
        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except ValueError:
            continue
        pop = pop_by_geoid.get(geoid, 0)
        block_groups.append(
            {
                "geoid": geoid,
                "lat": lat_f,
                "lon": lon_f,
                "population": pop,
            }
        )

    # Assign block groups to NPA via point-in-polygon
    npa_pop: Dict[str, int] = {}
    for npa in npa_features:
        name = npa.get("properties", {}).get("PLANNING_AREA_NAME", "UNKNOWN")
        npa_pop[name] = 0

    for bg in block_groups:
        for npa in npa_features:
            geom = npa.get("geometry")
            if not geom:
                continue
            if point_in_geometry(bg["lon"], bg["lat"], geom):
                name = npa.get("properties", {}).get("PLANNING_AREA_NAME", "UNKNOWN")
                npa_pop[name] = npa_pop.get(name, 0) + bg["population"]
                break

    # Write block group debug CSV
    with open(args.bg_csv_out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["geoid", "lat", "lon", "population"])
        w.writeheader()
        w.writerows(block_groups)

    # Attach population to NPA GeoJSON and write CSV summary
    for npa in npa_features:
        name = npa.get("properties", {}).get("PLANNING_AREA_NAME", "UNKNOWN")
        npa["properties"]["population"] = npa_pop.get(name, 0)

    with open(args.geojson_out, "w", encoding="utf-8") as f:
        json.dump(npa_geojson, f, ensure_ascii=False)

    with open(args.npa_csv_out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["planning_area_name", "population"])
        w.writeheader()
        for name, pop in sorted(npa_pop.items()):
            w.writerow({"planning_area_name": name, "population": pop})

    print(f"Wrote {args.geojson_out}")
    print(f"Wrote {args.npa_csv_out}")
    print(f"Wrote {args.bg_csv_out}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        sys.exit(1)
