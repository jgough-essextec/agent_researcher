'use client';

import { IterationListItem } from '@/types';

interface IterationTabsProps {
  iterations: IterationListItem[];
  selectedSequence?: number;
  onSelect: (sequence: number) => void;
  onCompare?: () => void;
}

export default function IterationTabs({
  iterations,
  selectedSequence,
  onSelect,
  onCompare,
}: IterationTabsProps) {
  const statusIndicators = {
    pending: 'bg-gray-300',
    running: 'bg-blue-500 animate-pulse',
    completed: 'bg-green-500',
    failed: 'bg-red-500',
  };

  if (iterations.length === 0) {
    return null;
  }

  return (
    <div className="border-b border-gray-200 bg-gray-50">
      <div className="flex items-center justify-between px-4">
        <div className="flex items-center gap-1 overflow-x-auto">
          {iterations.map((iteration) => (
            <button
              key={iteration.id}
              onClick={() => onSelect(iteration.sequence)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                selectedSequence === iteration.sequence
                  ? 'border-blue-500 text-blue-600 bg-white'
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${statusIndicators[iteration.status]}`}
              />
              <span>{iteration.name || `Iteration ${iteration.sequence}`}</span>
            </button>
          ))}
        </div>

        {iterations.length >= 2 && onCompare && (
          <button
            onClick={onCompare}
            className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Compare
          </button>
        )}
      </div>
    </div>
  );
}
