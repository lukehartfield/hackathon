# OCM Austin EV Charging Data

## What this dataset is
This dataset is a snapshot of EV charging station **points of interest (POIs)** in and around Austin, Texas pulled from the **Open Charge Map (OCM) API**. Each record represents a charging **site** with location, access details, operator/network, and one or more charging **connections** (ports).

Generated files:
- `data/ocm_austin.json`: Raw OCM POI records (one JSON object per station)
- `data/ocm_austin.geojson`: GeoJSON `FeatureCollection` for mapping (one feature per station)

## What fields it contains (high level)
Each station record in `data/ocm_austin.json` includes:
- `AddressInfo`: Name, address, **Latitude/Longitude**, contact info
- `Connections`: Charger ports (connection type, power kW, quantity, level)
- `OperatorInfo`: Network/operator (e.g., ChargePoint, Tesla, Blink)
- `UsageType`: Public / restricted access categories
- `StatusType`: Operational status
- `DataProvider`: Source of the record (often NREL/AFDC)

The GeoJSON file includes the same station data under `properties` and geometry as a point.

## How this fits the overall project
This dataset is the **Supply Layer** in the project’s graph model:

- **Existing station nodes**: Each station becomes a node with lat/lon and attributes.
- **Capacity features**: Derived from `Connections` and `NumberOfPoints` (if present)
  - L2 vs DC fast counts
  - Total power kW
  - Port quantity
- **Access features**: Derived from `UsageType` and `StatusType`
  - Public vs restricted access
  - Operational status
- **Network features**: Operator/network (useful for availability or ownership patterns)

These features can be combined with traffic and parking signals to compute:
- **Underperforming locations** (low utilization vs demand proxy)
- **Coverage gaps** (long distances to nearest public charger)
- **Priority expansion zones** (high demand, low supply)

## Can we generate a map of EV stations with this data?
Yes. The `data/ocm_austin.geojson` file is directly mappable in any standard GIS or web mapping library.

Examples:
- **QGIS / ArcGIS**: Load the GeoJSON as a vector layer.
- **Leaflet / Mapbox / deck.gl**: Use the GeoJSON as a layer source.
- **Python**: Use `geopandas` or `folium` to render a map.

If you want, I can generate a quick static map or an interactive HTML map next.

## Data quality notes
- OCM aggregates from multiple providers; some metadata completeness varies.
- A station can have multiple connectors, so port counts come from `Connections`.
- Duplicates are deduped by OCM `ID` when fetched.

## Next steps (recommended)
- Generate a station feature table for modeling (CSV or Parquet).
- Join traffic/parking layers to each station via spatial proximity.
- Build candidate expansion nodes from parking assets or a grid.
