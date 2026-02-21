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
      <h2 className="text-lg font-bold text-white">Suggested New Sites</h2>
      <p className="text-xs text-gray-400">Ranked by expected network impact</p>
      <div className="space-y-2 overflow-y-auto max-h-96">
        {sorted.map((r, i) => (
          <button
            key={r.site_id}
            onClick={() => onSelect?.(r)}
            className="bg-gray-800 rounded p-2 text-left w-full hover:bg-gray-700 transition-colors"
          >
            <div className="flex justify-between items-start">
              <span className="text-xs text-blue-400 font-bold">#{i + 1}</span>
              <span className="text-xs text-green-400">+{r.marginal_gain.toFixed(1)} pts</span>
            </div>
            <div className="text-xs text-gray-300 mt-1">
              {r.lat.toFixed(4)}, {r.lng.toFixed(4)}
            </div>
            <div className="mt-1 h-1.5 bg-gray-700 rounded">
              <div className="h-1.5 bg-blue-500 rounded" style={{ width: `${r.node_weight * 100}%` }} />
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
