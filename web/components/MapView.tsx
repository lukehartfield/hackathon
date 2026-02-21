'use client';

import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { ScoredStation } from '@/lib/types';

const STATUS_COLORS: Record<string, string> = {
  overloaded:    '#ff3860',
  balanced:      '#ffb020',
  underutilized: '#00e68a',
};

export default function MapView({ stations }: { stations: ScoredStation[] }) {
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
  }, []);

  /* ── Render station markers ────────────────────── */
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Clear previous layers
    layersRef.current.forEach(l => map.removeLayer(l));
    layersRef.current = [];

    stations.forEach(s => {
      const color = STATUS_COLORS[s.status] ?? '#00e68a';
      const radius = Math.max(3, Math.min(9, 2 + s.chargerCount * 1.2));

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
            `<span style="color:${color};font-family:'Azeret Mono',monospace;font-weight:500">${s.utilization.toFixed(0)}%</span>` +
          `</div>` +
        `</div>`,
        { direction: 'top', offset: [0, -6] }
      );

      circle.addTo(map);
      layersRef.current.push(circle);
    });
  }, [stations]);

  return <div id="map" className="w-full h-full" />;
}
