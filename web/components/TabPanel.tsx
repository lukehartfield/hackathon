'use client';

import type { ActiveTab, ScoredStation, Recommendation } from '@/lib/types';
import OverviewTab from './tabs/OverviewTab';
import CongestionTab from './tabs/CongestionTab';
import NodesTab from './tabs/NodesTab';
import AITab from './tabs/AITab';

const TABS: { id: ActiveTab; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'congestion', label: 'Congestion' },
  { id: 'nodes', label: 'Nodes' },
  { id: 'ai', label: 'AI Insights' },
];

interface TabPanelProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  stations: ScoredStation[];
  recommendations: Recommendation[];
  narrative: string;
  coverageBefore: number;
  coverageAfter: number;
  isInsightsLoading: boolean;
  onRunOptimization: () => void;
  onSelectRecommendation?: (rec: Recommendation) => void;
}

export default function TabPanel({
  activeTab, onTabChange, stations, recommendations,
  narrative, coverageBefore, coverageAfter, isInsightsLoading, onRunOptimization, onSelectRecommendation,
}: TabPanelProps) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex border-b border-[var(--border)]">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => onTabChange(t.id)}
            className={`flex-1 px-2 py-3 text-xs font-medium transition-colors ${
              activeTab === t.id
                ? 'text-white border-b-2 border-blue-500 bg-[var(--bg-card)]'
                : 'text-[var(--text-secondary)] hover:text-white'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto">
        {activeTab === 'overview' && <OverviewTab stations={stations} />}
        {activeTab === 'congestion' && <CongestionTab stations={stations} />}
        {activeTab === 'nodes' && (
          <NodesTab recommendations={recommendations} onSelect={onSelectRecommendation} />
        )}
        {activeTab === 'ai' && (
          <AITab
            narrative={narrative}
            coverageBefore={coverageBefore}
            coverageAfter={coverageAfter}
            isLoading={isInsightsLoading}
          />
        )}
      </div>

      <div className="p-4 border-t border-[var(--border)]">
        <button
          onClick={onRunOptimization}
          disabled={isInsightsLoading}
          className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-400 text-white font-semibold rounded-lg transition-colors"
        >
          {isInsightsLoading ? 'Computing Scenario...' : 'Run Optimization Demo'}
        </button>
      </div>
    </div>
  );
}
