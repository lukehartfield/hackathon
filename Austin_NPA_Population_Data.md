# Austin NPA Population Data

## What this dataset is
This dataset estimates **population by Neighborhood Planning Area (NPA)** in Austin, Texas. NPAs are **City of Austin–curated boundaries** that are more granular than council districts and are commonly used for neighborhood-scale planning.

The data is built by combining:
- **City of Austin NPA polygons** (boundary layer)
- **ACS 2023 block‑group population** (B01003_001E) from the U.S. Census
- **TIGERweb block‑group internal points** for spatial assignment

## Files created
- `data/austin_npa.geojson`
  - GeoJSON of NPA polygons with a `population` field added
- `data/austin_npa_population.csv`
  - Table with `planning_area_name` and estimated `population`
- `data/austin_blockgroup_population.csv`
  - Block‑group centroids with population (used to build the NPA totals)

## How the population is calculated
1. Block‑group population is pulled from **ACS 2023**.
2. Each block group is represented by its internal centroid (INTPTLAT/INTPTLON).
3. The centroid is assigned to the NPA polygon it falls within.
4. NPA population = sum of all block‑group populations assigned to it.

This is a standard, lightweight spatial aggregation approach suitable for hackathon‑scale analysis.

## How to use this with EV charging station data
The EV charging station layer (from Open Charge Map) gives **supply** locations. This NPA layer provides **local population demand**. Together, they enable:

- **Coverage gaps**: Identify NPAs with high population but few nearby stations.
- **Charger density**: Compute chargers per 10k residents per NPA.
- **Equity checks**: Compare station distribution against neighborhood population.
- **Priority ranking**: Weight candidate sites higher in high‑population NPAs with low supply.

### Example join strategy
1. Assign each station to the nearest NPA (or spatial join by point‑in‑polygon).
2. Aggregate station counts per NPA.
3. Compute ratios:
   - `chargers_per_10k = (station_count / population) * 10,000`
4. Rank NPAs by lowest chargers per 10k to flag under‑served areas.

## Notes / limitations
- Block‑group centroids are used for assignment (fast but approximate).
- Population is ACS‑based and not real‑time.
- For more precision, use full block‑group polygons instead of centroids.

If you want, I can generate the station‑to‑NPA join and a summary table next.
