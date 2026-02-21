'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';

const MapView = dynamic(() => import('@/components/MapView'), { ssr: false });

interface Station {
  lat: number;
  lng: number;
  title: string;
  chargerCount: number;
}

export default function Home() {
  const [stations, setStations] = useState<Station[]>([]);

  useEffect(() => {
    fetch('/data/ocm_austin.geojson')
      .then(r => r.json())
      .then(fc => {
        const parsed = fc.features
          .filter((f: any) => f.geometry?.coordinates?.length === 2)
          .map((f: any) => ({
            lat: f.geometry.coordinates[1],
            lng: f.geometry.coordinates[0],
            title: f.properties.AddressInfo?.Title ?? 'Charging Station',
            chargerCount: f.properties.NumberOfPoints
              ?? f.properties.Connections?.reduce((s: number, c: any) => s + (c.Quantity ?? 1), 0)
              ?? 1,
          }));
        setStations(parsed);
      });
  }, []);

  return (
    <div className="h-screen w-screen">
      <MapView stations={stations} />
    </div>
  );
}
