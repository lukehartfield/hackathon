// Use require for JSON imports from outside video/
// eslint-disable-next-line @typescript-eslint/no-var-requires
const ocmRaw = require("../../../web/public/data/ocm_austin.geojson");
// eslint-disable-next-line @typescript-eslint/no-var-requires
const recsRaw = require("../../../web/public/data/recommendations.geojson");
// eslint-disable-next-line @typescript-eslint/no-var-requires
const clustersRaw = require("../../../web/public/data/clusters.geojson");

export interface StationPoint {
  lat: number;
  lng: number;
  id: number;
  title: string;
  town: string;
  chargerCount: number;
  trafficScore: number;
  utilization: number;
  status: "overloaded" | "balanced" | "underutilized";
  optimizationScore: number;
}

export interface RecommendationPoint {
  lat: number;
  lng: number;
  rank: number;
  site_id: string;
  node_weight: number;
  marginal_gain: number;
}

export interface ClusterPoint {
  lat: number;
  lng: number;
  community_id: number;
  is_existing: boolean;
}

// Demand centers (same as web/lib/scoring.ts)
const DEMAND_CENTERS: [number, number, number][] = [
  [30.2672, -97.7431, 1.0],
  [30.2849, -97.7341, 0.85],
  [30.3600, -97.7200, 0.75],
  [30.2900, -97.6970, 0.70],
  [30.2200, -97.7900, 0.65],
  [30.2500, -97.7300, 0.60],
  [30.3100, -97.7500, 0.55],
  [30.2400, -97.7650, 0.50],
];

function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

function simulateTrafficScore(lat: number, lng: number): number {
  let score = 0;
  for (const [clat, clng, weight] of DEMAND_CENTERS) {
    score += weight * Math.exp(-haversineKm(lat, lng, clat, clng) / 2.6);
  }
  const seed = Math.sin(lat * 12.9898 + lng * 78.233) * 43758.5453;
  const noise = seed - Math.floor(seed);
  const jitter = (noise - 0.5) * 0.25;
  const normalized = 1 / (1 + Math.exp(-2.2 * (score - 0.7)));
  return 0.15 + Math.max(0, Math.min(1, normalized + jitter)) * 0.8;
}

function synthOptimizationScore(lat: number, lng: number, trafficScore: number, normStations: number): number {
  const seed = Math.sin(lat * 91.123 + lng * 47.77) * 15731.743;
  const noise = seed - Math.floor(seed);
  const base = Math.pow(noise, 0.35);
  const signal = 0.2 * trafficScore + 0.15 * normStations;
  return Math.max(0, Math.min(1, base * 0.75 + signal));
}

function deriveChargerCount(feature: any): number {
  const props = feature.properties;
  if (props.NumberOfPoints != null) return props.NumberOfPoints;
  if (props.Connections?.length) {
    return props.Connections.reduce((s: number, c: any) => s + (c.Quantity ?? 1), 0);
  }
  return 1;
}

let _stationsCache: StationPoint[] | null = null;

export function loadStations(): StationPoint[] {
  if (_stationsCache) return _stationsCache;
  const features = ocmRaw.features;
  const maxChargerCount = Math.max(...features.map((f: any) => deriveChargerCount(f)));

  _stationsCache = features.map((f: any) => {
    const lat = f.geometry.coordinates[1];
    const lng = f.geometry.coordinates[0];
    const chargerCount = deriveChargerCount(f);
    const trafficScore = simulateTrafficScore(lat, lng);
    const normStations = maxChargerCount > 0 ? chargerCount / maxChargerCount : 0;
    const optimizationScore = synthOptimizationScore(lat, lng, trafficScore, normStations);
    const utilization = (trafficScore * 100) / chargerCount;
    const status: StationPoint["status"] =
      optimizationScore < 0.33 ? "overloaded" :
      optimizationScore < 0.66 ? "balanced" :
      "underutilized";

    return {
      lat, lng,
      id: f.properties.ID,
      title: f.properties.AddressInfo?.Title ?? "",
      town: f.properties.AddressInfo?.Town ?? "Austin",
      chargerCount,
      trafficScore,
      utilization,
      status,
      optimizationScore,
    };
  });
  return _stationsCache;
}

export function loadRecommendations(): RecommendationPoint[] {
  return recsRaw.features
    .filter((f: any) => f.properties.rank != null)
    .sort((a: any, b: any) => a.properties.rank - b.properties.rank)
    .map((f: any) => ({
      lat: f.geometry.coordinates[1],
      lng: f.geometry.coordinates[0],
      rank: f.properties.rank,
      site_id: f.properties.site_id,
      node_weight: f.properties.node_weight,
      marginal_gain: f.properties.marginal_demand_gain,
    }));
}

export function loadClusters(): ClusterPoint[] {
  return clustersRaw.features.map((f: any) => ({
    lat: f.geometry.coordinates[1],
    lng: f.geometry.coordinates[0],
    community_id: f.properties.community_id,
    is_existing: f.properties.is_existing,
  }));
}

export function computeStats(stations: StationPoint[]) {
  const totalChargers = stations.reduce((s, st) => s + st.chargerCount, 0);
  const avgUtil = stations.reduce((s, st) => s + st.utilization, 0) / stations.length;
  const overloaded = stations.filter((s) => s.status === "overloaded").length;
  const balanced = stations.filter((s) => s.status === "balanced").length;
  const underutilized = stations.filter((s) => s.status === "underutilized").length;

  return {
    stationCount: stations.length,
    totalChargers,
    avgUtilization: Math.round(avgUtil),
    overloaded,
    balanced,
    underutilized,
    overloadedPct: Math.round((overloaded / stations.length) * 100),
    balancedPct: Math.round((balanced / stations.length) * 100),
    underutilizedPct: Math.round((underutilized / stations.length) * 100),
  };
}
