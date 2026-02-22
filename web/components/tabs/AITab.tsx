interface AITabProps {
  narrative: string;
  coverageBefore: number;
  coverageAfter: number;
  isLoading: boolean;
}

export default function AITab({ narrative, coverageBefore, coverageAfter, isLoading }: AITabProps) {
  const delta = Math.max(0, coverageAfter - coverageBefore);

  return (
    <div className="p-4 space-y-4">
      <div>
        <h2 className="text-lg font-bold text-white">Executive AI Brief</h2>
        <p className="text-xs text-[var(--text-secondary)] mt-1">Auto-generated summary for judges and sponsors</p>
      </div>

      <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-3">
        <div className="grid grid-cols-3 items-center gap-2">
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-400">{coverageBefore}%</div>
            <div className="text-xs text-[var(--text-secondary)] mt-1">Current</div>
          </div>
          <div className="text-center text-sm text-[var(--text-muted)]">+{delta}% lift</div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">{coverageAfter}%</div>
            <div className="text-xs text-[var(--text-secondary)] mt-1">Projected</div>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-3 text-[var(--text-secondary)] text-sm animate-pulse">
          Running graph optimization and drafting AI narrative...
        </div>
      ) : narrative ? (
        <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-3 text-sm text-gray-300 leading-relaxed whitespace-pre-wrap overflow-y-auto max-h-[360px]">
          {narrative}
        </div>
      ) : (
        <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-3 text-[var(--text-secondary)] text-sm">
          Click "Run Optimization Demo" to generate a live executive summary.
        </div>
      )}
    </div>
  );
}
