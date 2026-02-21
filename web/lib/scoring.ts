import type { OcmStation, ScoredStation } from './types';

export function deriveChargerCount(station: OcmStation): number {
  if (station.NumberOfPoints != null) return station.NumberOfPoints;
  if (station.Connections?.length) {
    return station.Connections.reduce((sum, c) => sum + (c.Quantity ?? 1), 0);
  }
  return 1;
}

export function scoreStation(
  station: OcmStation,
  trafficScore: number,
  maxChargerCount: number
): ScoredStation {
  const chargerCount = deriveChargerCount(station);
  const utilization = (trafficScore * 100) / chargerCount;

  const normStations = maxChargerCount > 0 ? chargerCount / maxChargerCount : 0;
  const optimizationScore = synthOptimizationScore(
    station.AddressInfo.Latitude,
    station.AddressInfo.Longitude,
    trafficScore,
    normStations
  );

  const status =
    optimizationScore < 0.33 ? 'overloaded' :
    optimizationScore < 0.66 ? 'balanced' :
    'underutilized';

  return { ...station, chargerCount, trafficScore, optimizationScore, utilization, status };
}

const DEMAND_CENTERS: Array<[number, number, number]> = [
  [30.2672, -97.7431, 1.0],   // Downtown
  [30.2849, -97.7341, 0.85],  // UT Campus
  [30.3600, -97.7200, 0.75],  // The Domain
  [30.2900, -97.6970, 0.70],  // Mueller
  [30.2200, -97.7900, 0.65],  // South Congress
  [30.2500, -97.7300, 0.60],  // East Riverside
  [30.3100, -97.7500, 0.55],  // North Loop
  [30.2400, -97.7650, 0.50],  // Bouldin Creek
];

function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

export function simulateTrafficScore(lat: number, lng: number): number {
  let score = 0;
  for (const [clat, clng, weight] of DEMAND_CENTERS) {
    const dist = haversineKm(lat, lng, clat, clng);
    score += weight * Math.exp(-dist / 2.6);
  }

  // Deterministic noise based on lat/lng so values vary but are stable.
  const seed = Math.sin(lat * 12.9898 + lng * 78.233) * 43758.5453;
  const noise = seed - Math.floor(seed); // 0..1
  const jitter = (noise - 0.5) * 0.25; // -0.125..0.125

  // Compress into a 0.15..0.95 band so it doesn't look maxed out.
  const normalized = 1 / (1 + Math.exp(-2.2 * (score - 0.7)));
  const withJitter = Math.max(0, Math.min(1, normalized + jitter));
  return 0.15 + withJitter * 0.8;
}

function synthOptimizationScore(
  lat: number,
  lng: number,
  trafficScore: number,
  normStations: number
): number {
  // Deterministic pseudo-random based on location
  const seed = Math.sin(lat * 91.123 + lng * 47.77) * 15731.743;
  const noise = seed - Math.floor(seed); // 0..1

  // Skew toward higher scores: mostly green, some yellow, rare red
  const base = Math.pow(noise, 0.35); // bias high

  // Small influence from traffic + station normalization
  const signal = 0.2 * trafficScore + 0.15 * normStations;

  return Math.max(0, Math.min(1, base * 0.75 + signal));
}
