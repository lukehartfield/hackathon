import { NextResponse } from 'next/server';
import { readFileSync } from 'fs';
import { join } from 'path';
import { parseOcmFeatures } from '@/lib/geojson';
import { scoreStation, simulateTrafficScore } from '@/lib/scoring';

export async function GET() {
  const filePath = join(process.cwd(), 'public', 'data', 'ocm_austin.geojson');
  const raw = JSON.parse(readFileSync(filePath, 'utf-8'));
  const stations = parseOcmFeatures(raw);

  const maxChargerCount = stations.reduce((max, s) => {
    const count = s.NumberOfPoints ?? (s.Connections?.reduce((sum, c) => sum + (c.Quantity ?? 1), 0) ?? 1);
    return Math.max(max, count);
  }, 1);

  const scored = stations.map(s => {
    const trafficScore = simulateTrafficScore(
      s.AddressInfo.Latitude,
      s.AddressInfo.Longitude
    );
    return scoreStation(s, trafficScore, maxChargerCount);
  });

  return NextResponse.json(scored);
}
