import type { Recommendation } from '@/lib/types';

export default function NodesTab({
  recommendations,
  onSelect,
}: {
  recommendations: Recommendation[];
  onSelect?: (rec: Recommendation) => void;
}) {
  const sorted = [...recommendations].sort((a, b) => b.node_weight - a.node_weight).slice(0, 10);

  return (
    <div className="p-4 space-y-3">
      <div>
        <h2 className="text-lg font-bold text-white">Recommended Expansion Nodes</h2>
        <p className="text-xs text-[var(--text-secondary)] mt-1">Click any node to fly the map and present location-level rationale</p>
      </div>

      <div className="space-y-2 overflow-y-auto max-h-[430px] pr-1">
        {sorted.map((r, i) => (
          <button
            key={r.site_id}
            onClick={() => onSelect?.(r)}
            className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-2.5 text-left w-full hover:bg-[var(--bg-card-hover)] transition-colors"
          >
            <div className="flex justify-between items-start">
              <span className="text-xs text-blue-400 font-bold">Priority #{i + 1}</span>
              <span className="text-xs text-green-400">+{r.marginal_gain.toFixed(1)} demand pts</span>
            </div>
            <div className="text-xs text-[var(--text-secondary)] mt-1">
              {r.lat.toFixed(4)}, {r.lng.toFixed(4)}
            </div>
            <div className="mt-2 h-1.5 bg-gray-700 rounded">
              <div className="h-1.5 bg-blue-500 rounded" style={{ width: `${Math.min(100, Math.round(r.node_weight * 100))}%` }} />
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
