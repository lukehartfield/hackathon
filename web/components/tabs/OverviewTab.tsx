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
