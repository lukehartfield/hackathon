import type { ScoredStation } from '@/lib/types';

export default function CongestionTab({ stations }: { stations: ScoredStation[] }) {
  const sorted = [...stations].sort((a, b) => b.utilization - a.utilization).slice(0, 15);

  return (
    <div className="p-4 space-y-3">
      <div>
        <h2 className="text-lg font-bold text-white">Congestion Hotspots</h2>
        <p className="text-xs text-[var(--text-secondary)] mt-1">Top 15 stations by estimated utilization pressure</p>
      </div>

      <div className="space-y-2 overflow-y-auto max-h-[430px] pr-1">
        {sorted.map((s, idx) => (
          <div key={s.ID} className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-2.5 flex justify-between items-center gap-2">
            <div className="flex items-start gap-2 min-w-0 flex-1">
              <div className="text-xs text-[var(--text-muted)] mt-0.5 w-5">#{idx + 1}</div>
              <div className="min-w-0">
                <div className="text-sm text-white truncate">{s.AddressInfo.Title}</div>
                <div className="text-xs text-[var(--text-secondary)] truncate">
                  {s.AddressInfo.Town ?? 'Austin'} · {s.chargerCount} charger(s)
                </div>
              </div>
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
