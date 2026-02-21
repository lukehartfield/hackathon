interface AITabProps {
  narrative: string;
  coverageBefore: number;
  coverageAfter: number;
  isLoading: boolean;
}

export default function AITab({ narrative, coverageBefore, coverageAfter, isLoading }: AITabProps) {
  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-bold text-white">AI Insights</h2>
      <div className="flex gap-4">
        <div className="flex-1 bg-gray-800 rounded p-3 text-center">
          <div className="text-2xl font-bold text-yellow-400">{coverageBefore}%</div>
          <div className="text-xs text-gray-400 mt-1">Current Coverage</div>
        </div>
        <div className="flex items-center text-gray-500">&rarr;</div>
        <div className="flex-1 bg-gray-800 rounded p-3 text-center">
          <div className="text-2xl font-bold text-green-400">{coverageAfter}%</div>
          <div className="text-xs text-gray-400 mt-1">After Expansion</div>
        </div>
      </div>
      {isLoading ? (
        <div className="text-gray-400 text-sm animate-pulse">Generating analysis...</div>
      ) : narrative ? (
        <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap overflow-y-auto max-h-72">
          {narrative}
        </div>
      ) : (
        <div className="text-gray-500 text-sm">Click &quot;Run Optimization&quot; to generate insights.</div>
      )}
    </div>
  );
}
