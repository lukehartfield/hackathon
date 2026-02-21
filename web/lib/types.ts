export type UtilizationStatus = 'overloaded' | 'balanced' | 'underutilized';

export interface OcmConnection {
  Quantity: number | null;
  Level?: { IsFastChargeCapable: boolean; Title: string };
  ConnectionType?: { Title: string };
}

export interface OcmStation {
  ID: number;
  UUID: string;
  NumberOfPoints: number | null;
  Connections: OcmConnection[] | null;
  AddressInfo: {
    Latitude: number;
    Longitude: number;
    Title: string;
    Town?: string;
    AddressLine1?: string;
  };
  UsageType?: { Title: string };
  OperatorInfo?: { Title: string };
}

export interface ScoredStation extends OcmStation {
  chargerCount: number;
  trafficScore: number;
  balanceScore: number;
  utilization: number;
  status: UtilizationStatus;
}

export interface Recommendation {
  lat: number;
  lng: number;
  site_id: string;
  node_weight: number;
  marginal_gain: number;
  reasoning?: string;
}

export interface ClusterFeature {
  lat: number;
  lng: number;
  community_id: string | number;
  is_underserved: boolean;
}

export type ActiveTab = 'overview' | 'congestion' | 'nodes' | 'ai';
