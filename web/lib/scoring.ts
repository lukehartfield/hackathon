import type { OcmStation, ScoredStation } from './types';

export function deriveChargerCount(station: OcmStation): number {
  if (station.NumberOfPoints != null) return station.NumberOfPoints;
  if (station.Connections?.length) {
    return station.Connections.reduce((sum, c) => sum + (c.Quantity ?? 1), 0);
  }
  return 1;
}

export function scoreStation(station: OcmStation, trafficScore: number): ScoredStation {
  const chargerCount = deriveChargerCount(station);
  const utilization = (trafficScore * 100) / chargerCount;
  const status =
    utilization > 150 ? 'overloaded' :
    utilization > 60  ? 'balanced' :
    'underutilized';

  return { ...station, chargerCount, trafficScore, utilization, status };
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
    score += weight * Math.exp(-dist / 3);
  }
  return Math.min(score, 1.0);
}
