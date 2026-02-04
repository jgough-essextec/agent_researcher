'use client';

import { IterationListItem } from '@/types';

interface IterationTimelineProps {
  iterations: IterationListItem[];
  selectedSequence?: number;
  onSelect: (sequence: number) => void;
}

export default function IterationTimeline({
  iterations,
  selectedSequence,
  onSelect,
}: IterationTimelineProps) {
  const statusColors = {
    pending: 'bg-gray-300',
    running: 'bg-blue-500 animate-pulse',
    completed: 'bg-green-500',
    failed: 'bg-red-500',
  };

  const statusBorderColors = {
    pending: 'border-gray-300',
    running: 'border-blue-500',
    completed: 'border-green-500',
    failed: 'border-red-500',
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  if (iterations.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No iterations yet</p>
        <p className="text-sm mt-1">Start your first iteration to begin research</p>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Timeline line */}
      <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />

      {/* Timeline items */}
      <div className="space-y-4">
        {iterations.map((iteration) => (
          <div
            key={iteration.id}
            onClick={() => onSelect(iteration.sequence)}
            className={`relative flex items-start gap-4 p-3 rounded-lg cursor-pointer transition-all ${
              selectedSequence === iteration.sequence
                ? 'bg-blue-50 border border-blue-200'
                : 'hover:bg-gray-50'
            }`}
          >
            {/* Status dot */}
            <div
              className={`relative z-10 w-8 h-8 rounded-full flex items-center justify-center border-2 ${statusBorderColors[iteration.status]} bg-white`}
            >
              <div className={`w-3 h-3 rounded-full ${statusColors[iteration.status]}`} />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <h4 className="font-medium text-gray-900">
                  {iteration.name || `Iteration ${iteration.sequence}`}
                </h4>
                <span className="text-xs text-gray-500">
                  {formatDate(iteration.created_at)}
                </span>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    iteration.status === 'completed'
                      ? 'bg-green-100 text-green-700'
                      : iteration.status === 'running'
                      ? 'bg-blue-100 text-blue-700'
                      : iteration.status === 'failed'
                      ? 'bg-red-100 text-red-700'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {iteration.status}
                </span>
                {!iteration.has_research_job && iteration.status === 'pending' && (
                  <span className="text-xs text-gray-500">Not started</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
