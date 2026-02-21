import type { OcmStation, Recommendation, ClusterFeature } from './types';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function parseOcmFeatures(fc: any): OcmStation[] {
  return (fc.features ?? [])
    .filter((f: any) => f.geometry?.coordinates?.length === 2)
    .map((f: any) => ({
      ...f.properties,
      AddressInfo: {
        ...f.properties.AddressInfo,
        Latitude: f.geometry.coordinates[1],
        Longitude: f.geometry.coordinates[0],
      },
    }));
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function parseRecommendations(fc: any): Recommendation[] {
  return (fc.features ?? [])
    .filter((f: any) => f.geometry?.coordinates?.length === 2)
    .map((f: any) => ({
      lat: f.geometry.coordinates[1],
      lng: f.geometry.coordinates[0],
      site_id: f.properties.site_id ?? '',
      node_weight: Number(f.properties.node_weight ?? 0),
      marginal_gain: Number(f.properties.marginal_demand_gain ?? f.properties.marginal_gain ?? 0),
      rank: f.properties.rank != null ? Number(f.properties.rank) : undefined,
      reasoning: f.properties.reasoning,
    }));
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function parseClusters(fc: any): ClusterFeature[] {
  return (fc.features ?? [])
    .filter((f: any) => f.geometry?.coordinates?.length === 2)
    .map((f: any) => ({
      lat: f.geometry.coordinates[1],
      lng: f.geometry.coordinates[0],
      community_id: f.properties.community_id ?? 0,
      is_underserved: Boolean(f.properties.is_underserved ?? f.properties.underserved ?? false),
    }));
}
