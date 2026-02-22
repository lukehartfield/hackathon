import type { ScoredStation } from '@/lib/types';

export default function OverviewTab({ stations }: { stations: ScoredStation[] }) {
  const overloaded = stations.filter(s => s.status === 'overloaded').length;
  const balanced = stations.filter(s => s.status === 'balanced').length;
  const underutilized = stations.filter(s => s.status === 'underutilized').length;
  const avgUtil = stations.length
    ? Math.round(stations.reduce((sum, s) => sum + s.utilization, 0) / stations.length)
    : 0;
  const totalChargers = stations.reduce((sum, s) => sum + s.chargerCount, 0);

  return (
    <div className="space-y-4 p-4">
      <div>
        <h2 className="text-lg font-bold text-white">Austin Network Snapshot</h2>
        <p className="text-xs text-[var(--text-secondary)] mt-1">
          Start your demo here: establish baseline demand pressure before optimization.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Stat label="Stations" value={stations.length} />
        <Stat label="Charging Points" value={totalChargers} />
        <Stat label="Avg Utilization" value={`${avgUtil}%`} />
        <Stat label="Overloaded" value={overloaded} color="text-red-400" />
      </div>

      <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-3 space-y-2">
        <div className="text-xs uppercase tracking-wider text-[var(--text-muted)]">Utilization Mix</div>
        <Bar label="Overloaded" count={overloaded} total={stations.length} color="bg-red-500" />
        <Bar label="Balanced" count={balanced} total={stations.length} color="bg-yellow-500" />
        <Bar label="Underutilized" count={underutilized} total={stations.length} color="bg-green-500" />
      </div>

      <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
        Suggested script: "We loaded 684 real stations, scored utilization, and identified stressed corridors. Next we allocate expansion nodes where marginal demand coverage is highest."
      </p>
    </div>
  );
}

function Stat({ label, value, color = 'text-white' }: { label: string; value: string | number; color?: string }) {
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-3">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-[var(--text-secondary)] mt-1">{label}</div>
    </div>
  );
}

function Bar({ label, count, total, color }: { label: string; count: number; total: number; color: string }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div>
      <div className="flex justify-between text-xs text-[var(--text-secondary)] mb-1">
        <span>{label}</span><span>{count} ({pct}%)</span>
      </div>
      <div className="h-2 bg-gray-700/70 rounded">
        <div className={`h-2 ${color} rounded`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
