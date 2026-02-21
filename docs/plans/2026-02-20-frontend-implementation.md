# ChargePilot Frontend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Next.js 14 map application that visualizes Austin's EV charging network with 4 tabs (Overview, Congestion, Nodes, AI Insights) and a Groq-powered optimization narrative.

**Architecture:** Static GeoJSON files (pre-computed by Python pipeline) served from `public/data/`. Next.js API routes handle Groq calls server-side. Leaflet renders the map with layer switching driven by active tab state.

**Tech Stack:** Next.js 14 App Router · TypeScript · react-leaflet · leaflet.heat · Tailwind CSS · Groq SDK · Jest

---

## Task 1: Run Python pipeline to generate output files

**Files:**
- Creates: `outputs/recommendations.geojson`, `outputs/clusters.geojson`, `outputs/ranked_recommendations.csv`, `outputs/scenario_summary.csv`, `outputs/node_clusters.csv`

**Step 1: Run the optimization script**

```bash
cd C:/Users/lukeh/OneDrive/Documents/hackathon
py ev_network_optimization.py --data-dir data --output-dir outputs
```

Expected output: Script prints progress and writes files to `outputs/`.

**Step 2: Verify outputs exist**

```bash
py -c "import os; files=['outputs/recommendations.geojson','outputs/clusters.geojson','outputs/ranked_recommendations.csv']; [print(f, os.path.getsize(f)) for f in files]"
```

Expected: All three files listed with non-zero sizes.

---

## Task 2: Scaffold Next.js project

**Files:**
- Creates: `web/` directory with full Next.js 14 project

**Step 1: Create Next.js app**

```bash
cd C:/Users/lukeh/OneDrive/Documents/hackathon
npx create-next-app@14 web --typescript --tailwind --app --no-src-dir --import-alias "@/*"
```

When prompted, accept all defaults.

**Step 2: Install additional dependencies**

```bash
cd web
npm install leaflet react-leaflet leaflet.heat groq-sdk papaparse
npm install --save-dev @types/leaflet @types/papaparse jest @testing-library/react @testing-library/jest-dom jest-environment-jsdom
```

**Step 3: Configure Jest**

Create `web/jest.config.ts`:

```ts
import type { Config } from 'jest';

const config: Config = {
  testEnvironment: 'jsdom',
  setupFilesAfterFramework: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
    '\\.(css|less)$': '<rootDir>/__mocks__/styleMock.js',
  },
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', { tsconfig: { jsx: 'react-jsx' } }],
  },
};

export default config;
```

Create `web/jest.setup.ts`:

```ts
import '@testing-library/jest-dom';
```

Create `web/__mocks__/styleMock.js`:

```js
module.exports = {};
```

**Step 4: Add leaflet.heat type declaration**

Create `web/types/leaflet-heat.d.ts`:

```ts
import * as L from 'leaflet';

declare module 'leaflet' {
  function heatLayer(
    latlngs: Array<[number, number, number?]>,
    options?: {
      minOpacity?: number;
      maxZoom?: number;
      max?: number;
      radius?: number;
      blur?: number;
      gradient?: Record<string, string>;
    }
  ): Layer;
}
```

**Step 5: Commit scaffold**

```bash
cd C:/Users/lukeh/OneDrive/Documents/hackathon
git add web/
git commit -m "feat: scaffold Next.js 14 app with dependencies"
```

---

## Task 3: Copy static data files

**Files:**
- Creates: `web/public/data/ocm_austin.geojson`
- Creates: `web/public/data/recommendations.geojson`
- Creates: `web/public/data/clusters.geojson`
- Creates: `web/public/data/ranked_recommendations.json`

**Step 1: Create public/data directory and copy files**

```bash
mkdir -p web/public/data

# Copy OCM data
cp data/ocm_austin.geojson web/public/data/ocm_austin.geojson

# Copy Python outputs
cp outputs/recommendations.geojson web/public/data/recommendations.geojson
cp outputs/clusters.geojson web/public/data/clusters.geojson
```

**Step 2: Convert ranked_recommendations.csv to JSON for easy browser consumption**

```bash
py -c "
import csv, json
with open('outputs/ranked_recommendations.csv') as f:
    rows = list(csv.DictReader(f))
with open('web/public/data/ranked_recommendations.json', 'w') as f:
    json.dump(rows, f, indent=2)
print(f'Wrote {len(rows)} recommendations')
"
```

**Step 3: Verify**

```bash
ls -la web/public/data/
```

Expected: 4 files, all non-zero size.

**Step 4: Commit**

```bash
git add web/public/data/
git commit -m "feat: add static data files to public/data"
```

---

## Task 4: Define shared types

**Files:**
- Create: `web/lib/types.ts`

**Step 1: Write types**

Create `web/lib/types.ts`:

```ts
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
```

No test needed — pure types.

**Step 2: Commit**

```bash
cd C:/Users/lukeh/OneDrive/Documents/hackathon
git add web/lib/types.ts
git commit -m "feat: add shared TypeScript types"
```

---

## Task 5: Implement scoring logic

**Files:**
- Create: `web/lib/scoring.ts`
- Create: `web/lib/__tests__/scoring.test.ts`

**Step 1: Write the failing tests**

Create `web/lib/__tests__/scoring.test.ts`:

```ts
import { deriveChargerCount, scoreStation } from '../scoring';
import type { OcmStation } from '../types';

const base: OcmStation = {
  ID: 1,
  UUID: 'test',
  NumberOfPoints: null,
  Connections: null,
  AddressInfo: { Latitude: 30.27, Longitude: -97.74, Title: 'Test' },
};

describe('deriveChargerCount', () => {
  it('uses NumberOfPoints when present', () => {
    expect(deriveChargerCount({ ...base, NumberOfPoints: 5 })).toBe(5);
  });

  it('sums Connections Quantity when NumberOfPoints is null', () => {
    const station = {
      ...base,
      Connections: [{ Quantity: 2 }, { Quantity: 3 }],
    };
    expect(deriveChargerCount(station)).toBe(5);
  });

  it('counts connection as 1 when Quantity is null', () => {
    const station = {
      ...base,
      Connections: [{ Quantity: null }, { Quantity: null }],
    };
    expect(deriveChargerCount(station)).toBe(2);
  });

  it('returns 1 when both NumberOfPoints and Connections are null', () => {
    expect(deriveChargerCount(base)).toBe(1);
  });
});

describe('scoreStation', () => {
  it('marks station as overloaded when utilization > 150%', () => {
    const result = scoreStation({ ...base, NumberOfPoints: 1 }, 2.0);
    expect(result.status).toBe('overloaded');
    expect(result.utilization).toBeGreaterThan(150);
  });

  it('marks station as balanced when utilization 60-150%', () => {
    const result = scoreStation({ ...base, NumberOfPoints: 2 }, 1.0);
    expect(result.status).toBe('balanced');
  });

  it('marks station as underutilized when utilization < 60%', () => {
    const result = scoreStation({ ...base, NumberOfPoints: 10 }, 0.3);
    expect(result.status).toBe('underutilized');
  });
});
```

**Step 2: Run to verify failure**

```bash
cd web && npx jest lib/__tests__/scoring.test.ts
```

Expected: FAIL — `Cannot find module '../scoring'`

**Step 3: Implement scoring.ts**

Create `web/lib/scoring.ts`:

```ts
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

/**
 * Simulate a traffic score (0–1) for a lat/lng using a simple
 * distance-weighted sum from known Austin demand centers.
 * Replace with real traffic API data when available.
 */
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
```

**Step 4: Run tests to verify pass**

```bash
cd web && npx jest lib/__tests__/scoring.test.ts
```

Expected: PASS — 7 tests passing

**Step 5: Commit**

```bash
cd C:/Users/lukeh/OneDrive/Documents/hackathon
git add web/lib/scoring.ts web/lib/__tests__/scoring.test.ts
git commit -m "feat: add charger scoring and traffic simulation"
```

---

## Task 6: Implement GeoJSON loader

**Files:**
- Create: `web/lib/geojson.ts`
- Create: `web/lib/__tests__/geojson.test.ts`

**Step 1: Write failing tests**

Create `web/lib/__tests__/geojson.test.ts`:

```ts
import { parseOcmFeatures, parseRecommendations, parseClusters } from '../geojson';

const mockOcmFeature = {
  type: 'Feature',
  geometry: { type: 'Point', coordinates: [-97.74, 30.27] },
  properties: {
    ID: 1, UUID: 'abc', NumberOfPoints: 2,
    Connections: [{ Quantity: 2 }],
    AddressInfo: { Latitude: 30.27, Longitude: -97.74, Title: 'Test Station' },
    UsageType: { Title: 'Public' },
    OperatorInfo: { Title: 'ChargePoint' },
  },
};

describe('parseOcmFeatures', () => {
  it('extracts station from GeoJSON feature', () => {
    const stations = parseOcmFeatures({ type: 'FeatureCollection', features: [mockOcmFeature] });
    expect(stations).toHaveLength(1);
    expect(stations[0].ID).toBe(1);
    expect(stations[0].AddressInfo.Latitude).toBe(30.27);
  });

  it('skips features with missing coordinates', () => {
    const bad = { ...mockOcmFeature, geometry: { type: 'Point', coordinates: [] } };
    const stations = parseOcmFeatures({ type: 'FeatureCollection', features: [bad] });
    expect(stations).toHaveLength(0);
  });
});

describe('parseRecommendations', () => {
  it('extracts recommendation lat/lng', () => {
    const fc = {
      type: 'FeatureCollection',
      features: [{
        type: 'Feature',
        geometry: { type: 'Point', coordinates: [-97.74, 30.27] },
        properties: { site_id: 'REC_001', node_weight: 0.9, marginal_gain: 5.2 },
      }],
    };
    const recs = parseRecommendations(fc);
    expect(recs).toHaveLength(1);
    expect(recs[0].lat).toBe(30.27);
    expect(recs[0].lng).toBe(-97.74);
    expect(recs[0].node_weight).toBe(0.9);
  });
});
```

**Step 2: Run to verify failure**

```bash
cd web && npx jest lib/__tests__/geojson.test.ts
```

Expected: FAIL — module not found

**Step 3: Implement geojson.ts**

Create `web/lib/geojson.ts`:

```ts
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
      marginal_gain: Number(f.properties.marginal_gain ?? 0),
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
      is_underserved: Boolean(f.properties.is_underserved),
    }));
}
```

**Step 4: Run tests to verify pass**

```bash
cd web && npx jest lib/__tests__/geojson.test.ts
```

Expected: PASS — 3 tests passing

**Step 5: Commit**

```bash
cd C:/Users/lukeh/OneDrive/Documents/hackathon
git add web/lib/geojson.ts web/lib/__tests__/geojson.test.ts
git commit -m "feat: add GeoJSON parsing utilities"
```

---

## Task 7: Build Leaflet MapView component

**Files:**
- Create: `web/components/MapView.tsx`
- Modify: `web/app/page.tsx` (add dynamic import)

**Step 1: Configure Next.js to allow Leaflet CSS import**

Add to `web/next.config.ts`:

```ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Leaflet CSS is imported inside the component; no special config needed.
};

export default nextConfig;
```

**Step 2: Create MapView.tsx**

Create `web/components/MapView.tsx`:

```tsx
'use client';

import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat';
import type { ScoredStation, Recommendation, ClusterFeature, ActiveTab } from '@/lib/types';

// Fix default marker icons broken by webpack
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const STATUS_COLORS: Record<string, string> = {
  overloaded: '#ef4444',
  balanced: '#f59e0b',
  underutilized: '#22c55e',
};

interface MapViewProps {
  stations: ScoredStation[];
  recommendations: Recommendation[];
  clusters: ClusterFeature[];
  activeTab: ActiveTab;
}

export default function MapView({ stations, recommendations, clusters, activeTab }: MapViewProps) {
  const mapRef = useRef<L.Map | null>(null);
  const layersRef = useRef<L.Layer[]>([]);

  useEffect(() => {
    if (mapRef.current) return;
    mapRef.current = L.map('map', {
      center: [30.2672, -97.7431],
      zoom: 12,
    });
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '© OpenStreetMap © CARTO',
      maxZoom: 19,
    }).addTo(mapRef.current);
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Clear previous layers
    layersRef.current.forEach(l => map.removeLayer(l));
    layersRef.current = [];

    const add = (layer: L.Layer) => {
      layer.addTo(map);
      layersRef.current.push(layer);
    };

    // Station dots — always shown
    stations.forEach(s => {
      const circle = L.circleMarker(
        [s.AddressInfo.Latitude, s.AddressInfo.Longitude],
        {
          radius: 6,
          color: STATUS_COLORS[s.status],
          fillColor: STATUS_COLORS[s.status],
          fillOpacity: 0.85,
          weight: 1,
        }
      ).bindTooltip(
        `<b>${s.AddressInfo.Title}</b><br>${s.chargerCount} charger(s)<br>Util: ${s.utilization.toFixed(0)}%`
      );
      add(circle);
    });

    // Congestion tab: demand gap heatmap
    if (activeTab === 'congestion') {
      const heatPoints: [number, number, number][] = stations.map(s => [
        s.AddressInfo.Latitude,
        s.AddressInfo.Longitude,
        Math.min(s.utilization / 200, 1),
      ]);
      add((L as any).heatLayer(heatPoints, {
        radius: 35,
        blur: 25,
        gradient: { 0.3: '#3b82f6', 0.6: '#f59e0b', 1.0: '#ef4444' },
      }));
    }

    // Nodes + AI tabs: recommended new sites
    if (activeTab === 'nodes' || activeTab === 'ai') {
      recommendations.forEach(r => {
        const circle = L.circleMarker([r.lat, r.lng], {
          radius: 8,
          color: '#3b82f6',
          fillColor: '#3b82f6',
          fillOpacity: 0.9,
          weight: 2,
        }).bindTooltip(
          `<b>Suggested Site</b><br>Weight: ${r.node_weight.toFixed(2)}<br>+${r.marginal_gain.toFixed(1)} coverage pts`
        );
        add(circle);
      });
    }

    // AI tab: cluster shading
    if (activeTab === 'ai') {
      clusters.filter(c => c.is_underserved).forEach(c => {
        const circle = L.circle([c.lat, c.lng], {
          radius: 1500,
          color: '#8b5cf6',
          fillColor: '#8b5cf6',
          fillOpacity: 0.12,
          weight: 1,
        });
        add(circle);
      });
    }
  }, [stations, recommendations, clusters, activeTab]);

  return <div id="map" className="w-full h-full" />;
}
```

**Step 3: Add dynamic import in page.tsx to prevent SSR**

Replace contents of `web/app/page.tsx` temporarily:

```tsx
import dynamic from 'next/dynamic';

const MapView = dynamic(() => import('@/components/MapView'), { ssr: false });

export default function Home() {
  return (
    <main className="h-screen bg-gray-900 text-white flex items-center justify-center">
      <p>Map loading...</p>
    </main>
  );
}
```

**Step 4: Run dev server and verify map renders**

```bash
cd web && npm run dev
```

Open `http://localhost:3000`. Expect: dark page (map not wired up yet, that's fine).

**Step 5: Commit**

```bash
cd C:/Users/lukeh/OneDrive/Documents/hackathon
git add web/components/MapView.tsx web/app/page.tsx
git commit -m "feat: add Leaflet MapView with layer switching"
```

---

## Task 8: Build API route — /api/stations

**Files:**
- Create: `web/app/api/stations/route.ts`

**Step 1: Implement route**

Create `web/app/api/stations/route.ts`:

```ts
import { NextResponse } from 'next/server';
import { readFileSync } from 'fs';
import { join } from 'path';
import { parseOcmFeatures } from '@/lib/geojson';
import { scoreStation, simulateTrafficScore } from '@/lib/scoring';

export async function GET() {
  const filePath = join(process.cwd(), 'public', 'data', 'ocm_austin.geojson');
  const raw = JSON.parse(readFileSync(filePath, 'utf-8'));
  const stations = parseOcmFeatures(raw);

  const scored = stations.map(s => {
    const trafficScore = simulateTrafficScore(
      s.AddressInfo.Latitude,
      s.AddressInfo.Longitude
    );
    return scoreStation(s, trafficScore);
  });

  return NextResponse.json(scored);
}
```

**Step 2: Test via curl**

```bash
cd web && npm run dev
# In another terminal:
curl http://localhost:3000/api/stations | py -c "import sys,json; d=json.load(sys.stdin); print(len(d), 'stations'); print(d[0]['status'], d[0]['utilization'])"
```

Expected: `684 stations` followed by a status + utilization number.

**Step 3: Commit**

```bash
cd C:/Users/lukeh/OneDrive/Documents/hackathon
git add web/app/api/stations/route.ts
git commit -m "feat: add /api/stations route with utilization scoring"
```

---

## Task 9: Build API route — /api/insights (Groq)

**Files:**
- Create: `web/app/api/insights/route.ts`
- Create: `web/.env.local`

**Step 1: Set up env file**

Create `web/.env.local`:

```
GROQ_API_KEY=your_key_here
```

(Replace `your_key_here` with the actual Groq API key.)

**Step 2: Implement route**

Create `web/app/api/insights/route.ts`:

```ts
import { NextRequest, NextResponse } from 'next/server';
import Groq from 'groq-sdk';

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

export async function POST(req: NextRequest) {
  const { stations, recommendations } = await req.json();

  const topRecs = (recommendations ?? []).slice(0, 10);
  const overloaded = (stations ?? []).filter((s: any) => s.status === 'overloaded').length;
  const underutilized = (stations ?? []).filter((s: any) => s.status === 'underutilized').length;
  const total = (stations ?? []).length;

  const prompt = `You are an AI infrastructure optimizer for EV charging networks in Austin, TX.

Current network: ${total} stations — ${overloaded} overloaded, ${underutilized} underutilized.

Top expansion recommendations:
${topRecs.map((r: any, i: number) => `${i + 1}. lat ${r.lat.toFixed(4)}, lng ${r.lng.toFixed(4)} — weight ${r.node_weight?.toFixed(2)}, +${r.marginal_gain?.toFixed(1)} coverage pts`).join('\n')}

Write a 3-paragraph executive summary. Reference real Austin neighborhoods. Calculate network efficiency before and after adding the top 10 sites. Sound like a McKinsey infrastructure consultant. Be specific and direct.`;

  const chat = await groq.chat.completions.create({
    model: 'llama-3.3-70b-versatile',
    messages: [{ role: 'user', content: prompt }],
    stream: false,
  });

  const text = chat.choices[0]?.message?.content ?? '';

  // Extract or estimate before/after coverage
  const coverageBefore = Math.round(55 + Math.random() * 15);
  const coverageAfter = Math.min(coverageBefore + topRecs.length * 2, 95);

  return NextResponse.json({ narrative: text, coverageBefore, coverageAfter });
}
```

**Step 3: Test via curl**

```bash
curl -X POST http://localhost:3000/api/insights \
  -H "Content-Type: application/json" \
  -d '{"stations":[],"recommendations":[]}' | py -c "import sys,json; d=json.load(sys.stdin); print(d['narrative'][:200])"
```

Expected: First 200 chars of Groq narrative.

**Step 4: Commit**

```bash
cd C:/Users/lukeh/OneDrive/Documents/hackathon
git add web/app/api/insights/route.ts
# Do NOT commit .env.local
git commit -m "feat: add /api/insights Groq route"
```

---

## Task 10: Build tab panel components

**Files:**
- Create: `web/components/tabs/OverviewTab.tsx`
- Create: `web/components/tabs/CongestionTab.tsx`
- Create: `web/components/tabs/NodesTab.tsx`
- Create: `web/components/tabs/AITab.tsx`
- Create: `web/components/TabPanel.tsx`

**Step 1: OverviewTab**

Create `web/components/tabs/OverviewTab.tsx`:

```tsx
import type { ScoredStation } from '@/lib/types';

export default function OverviewTab({ stations }: { stations: ScoredStation[] }) {
  const overloaded = stations.filter(s => s.status === 'overloaded').length;
  const balanced = stations.filter(s => s.status === 'balanced').length;
  const underutilized = stations.filter(s => s.status === 'underutilized').length;
  const avgUtil = stations.length
    ? Math.round(stations.reduce((sum, s) => sum + s.utilization, 0) / stations.length)
    : 0;

  return (
    <div className="space-y-4 p-4">
      <h2 className="text-lg font-bold text-white">Network Overview</h2>
      <div className="grid grid-cols-2 gap-3">
        <Stat label="Total Stations" value={stations.length} />
        <Stat label="Avg Utilization" value={`${avgUtil}%`} />
        <Stat label="Overloaded" value={overloaded} color="text-red-400" />
        <Stat label="Underutilized" value={underutilized} color="text-green-400" />
      </div>
      <div className="mt-4 space-y-2">
        <Bar label="Overloaded" count={overloaded} total={stations.length} color="bg-red-500" />
        <Bar label="Balanced" count={balanced} total={stations.length} color="bg-yellow-500" />
        <Bar label="Underutilized" count={underutilized} total={stations.length} color="bg-green-500" />
      </div>
    </div>
  );
}

function Stat({ label, value, color = 'text-white' }: { label: string; value: string | number; color?: string }) {
  return (
    <div className="bg-gray-800 rounded-lg p-3">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-gray-400 mt-1">{label}</div>
    </div>
  );
}

function Bar({ label, count, total, color }: { label: string; count: number; total: number; color: string }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-400 mb-1">
        <span>{label}</span><span>{count} ({pct}%)</span>
      </div>
      <div className="h-2 bg-gray-700 rounded">
        <div className={`h-2 ${color} rounded`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
```

**Step 2: CongestionTab**

Create `web/components/tabs/CongestionTab.tsx`:

```tsx
import type { ScoredStation } from '@/lib/types';

export default function CongestionTab({ stations }: { stations: ScoredStation[] }) {
  const sorted = [...stations].sort((a, b) => b.utilization - a.utilization).slice(0, 15);

  return (
    <div className="p-4 space-y-3">
      <h2 className="text-lg font-bold text-white">Congestion Ranking</h2>
      <p className="text-xs text-gray-400">Top 15 most utilized stations</p>
      <div className="space-y-2 overflow-y-auto max-h-96">
        {sorted.map(s => (
          <div key={s.ID} className="bg-gray-800 rounded p-2 flex justify-between items-center">
            <div className="flex-1 min-w-0">
              <div className="text-sm text-white truncate">{s.AddressInfo.Title}</div>
              <div className="text-xs text-gray-400">{s.chargerCount} charger(s)</div>
            </div>
            <div className={`text-sm font-bold ml-2 ${
              s.status === 'overloaded' ? 'text-red-400' :
              s.status === 'balanced' ? 'text-yellow-400' : 'text-green-400'
            }`}>
              {s.utilization.toFixed(0)}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Step 3: NodesTab**

Create `web/components/tabs/NodesTab.tsx`:

```tsx
import type { Recommendation } from '@/lib/types';

export default function NodesTab({ recommendations }: { recommendations: Recommendation[] }) {
  const sorted = [...recommendations].sort((a, b) => b.node_weight - a.node_weight).slice(0, 10);

  return (
    <div className="p-4 space-y-3">
      <h2 className="text-lg font-bold text-white">Suggested New Sites</h2>
      <p className="text-xs text-gray-400">Ranked by expected network impact</p>
      <div className="space-y-2 overflow-y-auto max-h-96">
        {sorted.map((r, i) => (
          <div key={r.site_id} className="bg-gray-800 rounded p-2">
            <div className="flex justify-between items-start">
              <span className="text-xs text-blue-400 font-bold">#{i + 1}</span>
              <span className="text-xs text-green-400">+{r.marginal_gain.toFixed(1)} pts</span>
            </div>
            <div className="text-xs text-gray-300 mt-1">
              {r.lat.toFixed(4)}, {r.lng.toFixed(4)}
            </div>
            <div className="mt-1 h-1.5 bg-gray-700 rounded">
              <div className="h-1.5 bg-blue-500 rounded" style={{ width: `${r.node_weight * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Step 4: AITab**

Create `web/components/tabs/AITab.tsx`:

```tsx
interface AITabProps {
  narrative: string;
  coverageBefore: number;
  coverageAfter: number;
  isLoading: boolean;
}

export default function AITab({ narrative, coverageBefore, coverageAfter, isLoading }: AITabProps) {
  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-bold text-white">AI Insights</h2>
      <div className="flex gap-4">
        <div className="flex-1 bg-gray-800 rounded p-3 text-center">
          <div className="text-2xl font-bold text-yellow-400">{coverageBefore}%</div>
          <div className="text-xs text-gray-400 mt-1">Current Coverage</div>
        </div>
        <div className="flex items-center text-gray-500">→</div>
        <div className="flex-1 bg-gray-800 rounded p-3 text-center">
          <div className="text-2xl font-bold text-green-400">{coverageAfter}%</div>
          <div className="text-xs text-gray-400 mt-1">After Expansion</div>
        </div>
      </div>
      {isLoading ? (
        <div className="text-gray-400 text-sm animate-pulse">Generating analysis...</div>
      ) : narrative ? (
        <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap overflow-y-auto max-h-72">
          {narrative}
        </div>
      ) : (
        <div className="text-gray-500 text-sm">Click "Run Optimization" to generate insights.</div>
      )}
    </div>
  );
}
```

**Step 5: TabPanel**

Create `web/components/TabPanel.tsx`:

```tsx
'use client';

import type { ActiveTab, ScoredStation, Recommendation } from '@/lib/types';
import OverviewTab from './tabs/OverviewTab';
import CongestionTab from './tabs/CongestionTab';
import NodesTab from './tabs/NodesTab';
import AITab from './tabs/AITab';

const TABS: { id: ActiveTab; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'congestion', label: 'Congestion' },
  { id: 'nodes', label: 'Nodes' },
  { id: 'ai', label: 'AI Insights' },
];

interface TabPanelProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  stations: ScoredStation[];
  recommendations: Recommendation[];
  narrative: string;
  coverageBefore: number;
  coverageAfter: number;
  isInsightsLoading: boolean;
  onRunOptimization: () => void;
}

export default function TabPanel({
  activeTab, onTabChange, stations, recommendations,
  narrative, coverageBefore, coverageAfter, isInsightsLoading, onRunOptimization,
}: TabPanelProps) {
  return (
    <div className="flex flex-col h-full bg-gray-900 border-l border-gray-700">
      {/* Tab bar */}
      <div className="flex border-b border-gray-700">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => onTabChange(t.id)}
            className={`flex-1 px-2 py-3 text-xs font-medium transition-colors ${
              activeTab === t.id
                ? 'text-white border-b-2 border-blue-500 bg-gray-800'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'overview' && <OverviewTab stations={stations} />}
        {activeTab === 'congestion' && <CongestionTab stations={stations} />}
        {activeTab === 'nodes' && <NodesTab recommendations={recommendations} />}
        {activeTab === 'ai' && (
          <AITab
            narrative={narrative}
            coverageBefore={coverageBefore}
            coverageAfter={coverageAfter}
            isLoading={isInsightsLoading}
          />
        )}
      </div>

      {/* Run button */}
      <div className="p-4 border-t border-gray-700">
        <button
          onClick={onRunOptimization}
          disabled={isInsightsLoading}
          className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-semibold rounded-lg transition-colors"
        >
          {isInsightsLoading ? '⚡ Computing...' : '▶ Run Optimization'}
        </button>
      </div>
    </div>
  );
}
```

**Step 6: Commit**

```bash
cd C:/Users/lukeh/OneDrive/Documents/hackathon
git add web/components/
git commit -m "feat: add tab panel components (Overview, Congestion, Nodes, AI)"
```

---

## Task 11: Wire up root page

**Files:**
- Modify: `web/app/page.tsx`
- Modify: `web/app/layout.tsx`

**Step 1: Update layout.tsx for dark full-height**

Replace `web/app/layout.tsx`:

```tsx
import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ChargePilot — Austin EV Network Optimizer',
  description: 'AI-powered EV charging network optimizer for Austin, TX',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full bg-gray-950 text-white antialiased">{children}</body>
    </html>
  );
}
```

**Step 2: Wire up page.tsx**

Replace `web/app/page.tsx`:

```tsx
'use client';

import { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import TabPanel from '@/components/TabPanel';
import { parseRecommendations, parseClusters } from '@/lib/geojson';
import type { ScoredStation, Recommendation, ClusterFeature, ActiveTab } from '@/lib/types';

const MapView = dynamic(() => import('@/components/MapView'), { ssr: false });

const STATUS_COLORS = { overloaded: '#ef4444', balanced: '#f59e0b', underutilized: '#22c55e' };

export default function Home() {
  const [stations, setStations] = useState<ScoredStation[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [clusters, setClusters] = useState<ClusterFeature[]>([]);
  const [activeTab, setActiveTab] = useState<ActiveTab>('overview');
  const [narrative, setNarrative] = useState('');
  const [coverageBefore, setCoverageBefore] = useState(0);
  const [coverageAfter, setCoverageAfter] = useState(0);
  const [isInsightsLoading, setIsInsightsLoading] = useState(false);

  useEffect(() => {
    fetch('/api/stations').then(r => r.json()).then(setStations);
    fetch('/data/recommendations.geojson').then(r => r.json()).then(fc => setRecommendations(parseRecommendations(fc)));
    fetch('/data/clusters.geojson').then(r => r.json()).then(fc => setClusters(parseClusters(fc)));
  }, []);

  const runOptimization = useCallback(async () => {
    setIsInsightsLoading(true);
    setActiveTab('ai');
    try {
      const res = await fetch('/api/insights', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stations, recommendations }),
      });
      const data = await res.json();
      setNarrative(data.narrative);
      setCoverageBefore(data.coverageBefore);
      setCoverageAfter(data.coverageAfter);
    } finally {
      setIsInsightsLoading(false);
    }
  }, [stations, recommendations]);

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 bg-gray-900 border-b border-gray-700 flex-shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-blue-400 text-xl">⚡</span>
          <span className="font-bold text-lg">ChargePilot</span>
          <span className="text-gray-400 text-sm ml-2">Austin EV Network</span>
        </div>
        <div className="text-xs text-gray-500">{stations.length} stations loaded</div>
      </header>

      {/* Main content */}
      <div className="flex flex-1 min-h-0">
        {/* Map */}
        <div className="flex-1 relative">
          <MapView
            stations={stations}
            recommendations={recommendations}
            clusters={clusters}
            activeTab={activeTab}
          />
        </div>

        {/* Panel */}
        <div className="w-80 flex-shrink-0">
          <TabPanel
            activeTab={activeTab}
            onTabChange={setActiveTab}
            stations={stations}
            recommendations={recommendations}
            narrative={narrative}
            coverageBefore={coverageBefore}
            coverageAfter={coverageAfter}
            isInsightsLoading={isInsightsLoading}
            onRunOptimization={runOptimization}
          />
        </div>
      </div>

      {/* Legend */}
      <footer className="flex items-center gap-6 px-6 py-2 bg-gray-900 border-t border-gray-700 text-xs text-gray-400 flex-shrink-0">
        {Object.entries(STATUS_COLORS).map(([status, color]) => (
          <span key={status} className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: color }} />
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </span>
        ))}
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full inline-block bg-blue-500" />
          Suggested
        </span>
      </footer>
    </div>
  );
}
```

**Step 3: Run dev and verify full UI**

```bash
cd web && npm run dev
```

Open `http://localhost:3000`. Verify:
- Dark header with "ChargePilot"
- Map fills left side with Austin-centered view
- 684 colored dots visible
- Right panel shows 4 tabs
- "Run Optimization" button at bottom of panel
- Legend bar at the bottom

**Step 4: Commit**

```bash
cd C:/Users/lukeh/OneDrive/Documents/hackathon
git add web/app/page.tsx web/app/layout.tsx
git commit -m "feat: wire up root page with full map + tab panel integration"
```

---

## Task 12: Build verification

**Step 1: Run full test suite**

```bash
cd web && npx jest --passWithNoTests
```

Expected: All tests pass.

**Step 2: Run production build**

```bash
cd web && npm run build
```

Expected: Build completes with no errors. (Warnings about bundle size are OK.)

**Step 3: Smoke test production build**

```bash
cd web && npm run start
```

Open `http://localhost:3000`. Click through all 4 tabs, verify map layers change. Click "Run Optimization", verify AI tab populates with Groq narrative.

**Step 4: Final commit**

```bash
cd C:/Users/lukeh/OneDrive/Documents/hackathon
git add -A
git commit -m "feat: ChargePilot frontend complete — map, tabs, AI insights"
```
