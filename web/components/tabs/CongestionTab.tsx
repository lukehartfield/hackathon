import type { ScoredStation } from '@/lib/types';

export default function CongestionTab({ stations }: { stations: ScoredStation[] }) {
  const sorted = [...stations].sort((a, b) => b.utilization - a.utilization).slice(0, 15);

  return (
    <div className="p-4 space-y-3">
      <h2 className="text-lg font-bold text-white">Congestion Ranking</h2>
      <p className="text-xs text-gray-400">Top 15 most utilized stations</p>
      <div className="space-y-2 overflow-y-auto max-h-96">
        {sorted.map(s => (
          <div key={s.ID} className="bg-gray-800 rounded p-2 flex justify-between items-center">
            <div className="flex-1 min-w-0">
              <div className="text-sm text-white truncate">{s.AddressInfo.Title}</div>
              <div className="text-xs text-gray-400">{s.chargerCount} charger(s)</div>
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
