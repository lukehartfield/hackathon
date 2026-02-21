'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import type { ScoredStation } from '@/lib/types';

const MapView = dynamic(() => import('@/components/MapView'), { ssr: false });

export default function Home() {
  const [stations, setStations] = useState<ScoredStation[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetch('/api/stations')
      .then(r => r.json())
      .then((data: ScoredStation[]) => {
        setStations(data);
        setTimeout(() => setIsLoading(false), 600);
      })
      .catch(() => setIsLoading(false));
  }, []);

  const overloaded = stations.filter(s => s.status === 'overloaded').length;
  const balanced = stations.filter(s => s.status === 'balanced').length;
  const underutilized = stations.filter(s => s.status === 'underutilized').length;

  return (
    <div className="h-screen w-screen relative overflow-hidden">
      {/* ── Loading Screen ──────────────────────────── */}
      <div className={`loading-screen ${!isLoading ? 'fade-out' : ''}`}>
        <div className="font-display text-3xl font-bold tracking-tight text-accent animate-logo-glow">
          ⚡ CHARGEPILOT
        </div>
        <p className="text-sm text-[var(--text-secondary)] mt-3 font-body">
          Loading Austin EV Network...
        </p>
        <div className="loading-bar">
          <div className="loading-bar-fill" />
        </div>
      </div>

      {/* ── Map ─────────────────────────────────────── */}
      <MapView stations={stations} />

      {/* ── Header Overlay ──────────────────────────── */}
      <div className="absolute top-0 left-0 right-0 z-[1000] pointer-events-none">
        <div className="flex items-center justify-between px-5 py-3">
          {/* Brand */}
          <div className="glass-strong rounded-xl px-5 py-3 glow-border pointer-events-auto animate-fade-in">
            <div className="flex items-center gap-3">
              <span className="font-display text-xl font-bold tracking-tight text-accent">
                ⚡ CHARGEPILOT
              </span>
              <div className="w-px h-6 bg-border" />
              <span className="text-sm text-[var(--text-secondary)] font-body">
                Austin, TX
              </span>
            </div>
          </div>

          {/* Live Stats */}
          <div
            className="glass-strong rounded-xl px-4 py-2.5 glow-border pointer-events-auto animate-fade-in"
            style={{ animationDelay: '0.1s' }}
          >
            <div className="flex items-center gap-4 text-xs font-mono">
              <div className="flex items-center gap-1.5">
                <span className="text-[var(--text-secondary)]">Stations</span>
                <span className="text-[var(--text-primary)] font-semibold">{stations.length}</span>
              </div>
              <div className="w-px h-4 bg-border" />
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-overloaded" />
                <span className="text-overloaded font-semibold">{overloaded}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-balanced" />
                <span className="text-balanced font-semibold">{balanced}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-underutilized" />
                <span className="text-underutilized font-semibold">{underutilized}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Legend ───────────────────────────────────── */}
      <div className="absolute bottom-6 left-5 z-[1000] pointer-events-none">
        <div
          className="glass-strong rounded-xl px-4 py-3 glow-border pointer-events-auto animate-slide-up"
          style={{ animationDelay: '0.3s' }}
        >
          <div className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-2 font-body font-medium">
            Utilization
          </div>
          <div className="flex items-center gap-4 text-xs font-body">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-overloaded shadow-[0_0_6px_var(--overloaded)]" />
              <span className="text-[var(--text-secondary)]">&gt;150% Overloaded</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-balanced shadow-[0_0_6px_var(--balanced)]" />
              <span className="text-[var(--text-secondary)]">60–150% Balanced</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-underutilized shadow-[0_0_6px_var(--underutilized)]" />
              <span className="text-[var(--text-secondary)]">&lt;60% Underutilized</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
