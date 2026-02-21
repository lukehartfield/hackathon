'use client';

import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface Station {
  lat: number;
  lng: number;
  title: string;
  chargerCount: number;
}

export default function MapView({ stations }: { stations: Station[] }) {
  const mapRef = useRef<L.Map | null>(null);
  const layersRef = useRef<L.Layer[]>([]);

  useEffect(() => {
    if (mapRef.current) return;
    mapRef.current = L.map('map', {
      center: [30.2672, -97.7431],
      zoom: 12,
    });
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap &copy; CARTO',
      maxZoom: 19,
    }).addTo(mapRef.current);
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    layersRef.current.forEach(l => map.removeLayer(l));
    layersRef.current = [];

    stations.forEach(s => {
      const circle = L.circleMarker([s.lat, s.lng], {
        radius: 5,
        color: '#22c55e',
        fillColor: '#22c55e',
        fillOpacity: 0.8,
        weight: 1,
      }).bindTooltip(
        `<b>${s.title}</b><br>${s.chargerCount} charger(s)`
      );
      circle.addTo(map);
      layersRef.current.push(circle);
    });
  }, [stations]);

  return <div id="map" className="w-full h-full" />;
}
