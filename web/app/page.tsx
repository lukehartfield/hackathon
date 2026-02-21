'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import type { ScoredStation, Recommendation } from '@/lib/types';
import { parseRecommendations } from '@/lib/geojson';
import NodesTab from '@/components/tabs/NodesTab';

const MapView = dynamic(() => import('@/components/MapView'), { ssr: false });

export default function Home() {
  const [stations, setStations] = useState<ScoredStation[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
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

  useEffect(() => {
    fetch('/data/recommendations.geojson')
      .then(r => r.json())
      .then((fc) => setRecommendations(parseRecommendations(fc)))
      .catch(() => setRecommendations([]));
  }, []);

  const balances = stations.map(s => s.balanceScore).sort((a, b) => a - b);
  const percentile = (p: number) => {
    if (!balances.length) return 0;
    const idx = (balances.length - 1) * p;
    const lo = Math.floor(idx);
    const hi = Math.ceil(idx);
    if (lo === hi) return balances[lo];
    const t = idx - lo;
    return balances[lo] + (balances[hi] - balances[lo]) * t;
  };
  const p20 = percentile(0.2);
  const p80 = percentile(0.8);
  const redCount = stations.filter(s => s.utilization <= p20).length;
  const greenCount = stations.filter(s => s.utilization >= p80).length;
  const yellowCount = Math.max(0, stations.length - redCount - greenCount);
  const totalPoints = stations.reduce((sum, s) => sum + s.chargerCount, 0);

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
                <span className="text-[var(--text-secondary)]">Points</span>
                <span className="text-[var(--text-primary)] font-semibold">{totalPoints}</span>
              </div>
              <div className="w-px h-4 bg-border" />
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-overloaded" />
                <span className="text-overloaded font-semibold">{redCount}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-balanced" />
                <span className="text-balanced font-semibold">{yellowCount}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-underutilized" />
                <span className="text-underutilized font-semibold">{greenCount}</span>
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
            Balance
          </div>
          <div className="flex items-center gap-4 text-xs font-body">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-overloaded shadow-[0_0_6px_var(--overloaded)]" />
              <span className="text-[var(--text-secondary)]">Bottom 20% (low match)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-balanced shadow-[0_0_6px_var(--balanced)]" />
              <span className="text-[var(--text-secondary)]">Middle 60% (mid match)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-underutilized shadow-[0_0_6px_var(--underutilized)]" />
              <span className="text-[var(--text-secondary)]">Top 20% (high match)</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Top 10 Recommendations ───────────────────── */}
      <div className="absolute top-20 right-5 z-[1000] w-[320px] pointer-events-none">
        <div className="glass-strong rounded-xl glow-border pointer-events-auto animate-slide-up">
          <NodesTab recommendations={recommendations} />
        </div>
      </div>
    </div>
  );
}
