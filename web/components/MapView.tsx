'use client';

import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { ScoredStation, Recommendation } from '@/lib/types';

const STATUS_COLORS: Record<string, string> = {
  overloaded: '#ff3860',
  balanced: '#ffb020',
  underutilized: '#00e68a',
};

const OPT_COLORS = {
  good: '#00e68a',
  mid: '#ffb020',
  bad: '#ff3860',
};

function clamp01(n: number) {
  return Math.max(0, Math.min(1, n));
}

function hexToRgb(hex: string) {
  const value = hex.replace('#', '');
  const r = parseInt(value.slice(0, 2), 16);
  const g = parseInt(value.slice(2, 4), 16);
  const b = parseInt(value.slice(4, 6), 16);
  return { r, g, b };
}

function rgbToHex(r: number, g: number, b: number) {
  const toHex = (v: number) => Math.round(v).toString(16).padStart(2, '0');
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t;
}

function lerpColor(a: string, b: string, t: number) {
  const c1 = hexToRgb(a);
  const c2 = hexToRgb(b);
  return rgbToHex(
    lerp(c1.r, c2.r, t),
    lerp(c1.g, c2.g, t),
    lerp(c1.b, c2.b, t)
  );
}

function percentile(sorted: number[], p: number) {
  if (!sorted.length) return 0;
  const idx = (sorted.length - 1) * p;
  const lo = Math.floor(idx);
  const hi = Math.ceil(idx);
  if (lo === hi) return sorted[lo];
  const t = idx - lo;
  return lerp(sorted[lo], sorted[hi], t);
}

function utilizationToScore(utilization: number, p20: number, p50: number, p80: number) {
  // Map utilization into 0..1 so colors spread across the dataset.
  // Below p20 -> red, around p50 -> yellow, above p80 -> green.
  if (utilization <= p20) return 0;
  if (utilization >= p80) return 1;
  if (utilization <= p50) return clamp01((utilization - p20) / (p50 - p20));
  return clamp01(0.5 + (utilization - p50) / (p80 - p50) * 0.5);
}

function utilizationToColor(utilization: number, p20: number, p50: number, p80: number) {
  const score = utilizationToScore(utilization, p20, p50, p80);
  if (score >= 0.5) {
    return lerpColor(OPT_COLORS.mid, OPT_COLORS.good, (score - 0.5) / 0.5);
  }
  return lerpColor(OPT_COLORS.bad, OPT_COLORS.mid, score / 0.5);
}

function utilizationBand(utilization: number, p20: number, p80: number) {
  if (utilization <= p20) return 'low';
  if (utilization >= p80) return 'high';
  return 'mid';
}

export default function MapView({
  stations,
  recommendations = [],
}: {
  stations: ScoredStation[];
  recommendations?: Recommendation[];
}) {
  const mapRef = useRef<L.Map | null>(null);
  const layersRef = useRef<L.Layer[]>([]);

  /* ── Initialize map ────────────────────────────── */
  useEffect(() => {
    if (mapRef.current) return;
    mapRef.current = L.map('map', {
      center: [30.2672, -97.7431],
      zoom: 12,
      zoomControl: false,
    });

    // Zoom control in bottom-right to avoid header overlap
    L.control.zoom({ position: 'bottomright' }).addTo(mapRef.current);

    L.tileLayer(
      'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
      {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        maxZoom: 19,
      }
    ).addTo(mapRef.current);

    // Expose a simple global hook so other UI elements can pan/zoom the map.
    (window as any).__flyToStation = (lat: number, lng: number) => {
      if (!mapRef.current) return;
      mapRef.current.flyTo([lat, lng], 15, { duration: 0.9 });
    };
  }, []);

  /* ── Render station markers ────────────────────── */
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Clear previous layers
    layersRef.current.forEach(l => map.removeLayer(l));
    layersRef.current = [];

    const scores = stations.map(s => s.optimizationScore).sort((a, b) => a - b);
    const p10 = percentile(scores, 0.1);
    const p50 = percentile(scores, 0.5);
    const p90 = percentile(scores, 0.9);

    stations.forEach(s => {
      const color = utilizationToColor(s.optimizationScore, p10, p50, p90);
      const radius = Math.max(3, Math.min(9, 2 + s.chargerCount * 1.2));
      const statusColor = STATUS_COLORS[s.status] ?? '#00e68a';
      const optScore = utilizationToScore(s.optimizationScore, p10, p50, p90);
      const band = utilizationBand(s.optimizationScore, p10, p90);
      const bandLabel = band === 'low' ? 'Overloaded' : band === 'high' ? 'Underutilized' : 'Balanced';

      const circle = L.circleMarker(
        [s.AddressInfo.Latitude, s.AddressInfo.Longitude],
        {
          radius,
          color,
          fillColor: color,
          fillOpacity: 0.75,
          weight: 1.5,
          // Glow effect via shadow
          className: s.status === 'overloaded' ? 'marker-overloaded' : '',
        }
      ).bindTooltip(
        `<div style="min-width:140px">` +
          `<div style="font-weight:600;margin-bottom:4px">${s.AddressInfo.Title}</div>` +
          `<div style="display:flex;justify-content:space-between;gap:12px">` +
            `<span style="color:#7b8ea8">${s.chargerCount} charger${s.chargerCount !== 1 ? 's' : ''}</span>` +
            `<span style="color:${color};font-family:'Azeret Mono',monospace;font-weight:500">${(s.optimizationScore * 100).toFixed(0)}%</span>` +
          `</div>` +
        `</div>`,
        { direction: 'top', offset: [0, -6] }
      ).bindPopup(
        `<div style="min-width:220px">` +
          `<div style="font-weight:700;font-size:14px;margin-bottom:6px">${s.AddressInfo.Title}</div>` +
          `<div style="color:#9fb0c6;margin-bottom:8px">${s.AddressInfo.AddressLine1 ?? ''} ${s.AddressInfo.Town ?? ''}</div>` +
          `<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 12px;font-size:12px">` +
            `<div style="color:#7b8ea8">Operator</div><div>${s.OperatorInfo?.Title ?? 'Unknown'}</div>` +
            `<div style="color:#7b8ea8">Usage</div><div>${s.UsageType?.Title ?? 'Unknown'}</div>` +
            `<div style="color:#7b8ea8">Chargers</div><div>${s.chargerCount}</div>` +
            `<div style="color:#7b8ea8">Traffic score</div><div>${(s.trafficScore * 100).toFixed(0)}%</div>` +
            `<div style="color:#7b8ea8">Optimization score</div><div>${(s.optimizationScore * 100).toFixed(0)}%</div>` +
            `<div style="color:#7b8ea8">Status</div><div style="color:${color};font-weight:600">${bandLabel}</div>` +
          `</div>` +
        `</div>`,
        { offset: [0, -4] }
      );

      circle.addTo(map);
      layersRef.current.push(circle);
    });
  }, [stations, recommendations]);

  /* ── Render recommendation markers ─────────────── */
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const recLayers: L.Layer[] = [];
    const color = '#3b82f6';

    recommendations.forEach(r => {
      const circle = L.circleMarker([r.lat, r.lng], {
        radius: 6,
        color,
        fillColor: color,
        fillOpacity: 0.85,
        weight: 1.5,
        className: 'marker-recommendation',
      }).bindTooltip(
        `<div style="min-width:140px">` +
          `<div style="font-weight:600;margin-bottom:4px">Recommended Site</div>` +
          `<div style="display:flex;flex-direction:column;gap:2px;font-size:11px">` +
            `<div style="display:flex;justify-content:space-between"><span style="color:#7b8ea8">Node weight</span><span style="color:${color};font-family:'Azeret Mono',monospace;font-weight:500">${(r.node_weight * 100).toFixed(0)}%</span></div>` +
            `<div style="display:flex;justify-content:space-between"><span style="color:#7b8ea8">Marginal gain</span><span>${r.marginal_gain.toFixed(1)}</span></div>` +
          `</div>` +
        `</div>`,
        { direction: 'top', offset: [0, -6] }
      );

      circle.addTo(map);
      recLayers.push(circle);
    });

    return () => {
      recLayers.forEach(l => map.removeLayer(l));
    };
  }, [recommendations]);

  return <div id="map" className="w-full h-full" />;
}
