'use client';

import { IterationComparison, IterationComparisonData, ListDiff } from '@/types';

interface IterationCompareProps {
  comparison: IterationComparison;
  onClose: () => void;
}

export default function IterationCompare({ comparison, onClose }: IterationCompareProps) {
  const { iteration_a, iteration_b, differences } = comparison;

  const DiffList = ({ diff, label }: { diff: ListDiff; label: string }) => (
    <div className="mb-6">
      <h4 className="text-sm font-semibold text-gray-700 mb-2">{label}</h4>
      <div className="space-y-2">
        {diff.added.length > 0 && (
          <div>
            <span className="text-xs text-green-600 font-medium">+ Added ({diff.added.length})</span>
            <ul className="mt-1 space-y-1">
              {diff.added.map((item, idx) => (
                <li key={idx} className="text-sm text-green-700 bg-green-50 px-2 py-1 rounded">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}
        {diff.removed.length > 0 && (
          <div>
            <span className="text-xs text-red-600 font-medium">- Removed ({diff.removed.length})</span>
            <ul className="mt-1 space-y-1">
              {diff.removed.map((item, idx) => (
                <li key={idx} className="text-sm text-red-700 bg-red-50 px-2 py-1 rounded line-through">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}
        {diff.unchanged.length > 0 && (
          <div>
            <span className="text-xs text-gray-500 font-medium">= Unchanged ({diff.unchanged.length})</span>
            <ul className="mt-1 space-y-1">
              {diff.unchanged.slice(0, 3).map((item, idx) => (
                <li key={idx} className="text-sm text-gray-600 bg-gray-50 px-2 py-1 rounded">
                  {item}
                </li>
              ))}
              {diff.unchanged.length > 3 && (
                <li className="text-sm text-gray-400 px-2">
                  ...and {diff.unchanged.length - 3} more
                </li>
              )}
            </ul>
          </div>
        )}
      </div>
    </div>
  );

  const IterationColumn = ({ data }: { data: IterationComparisonData }) => (
    <div className="flex-1 min-w-0">
      <div className="bg-gray-50 rounded-lg p-4 h-full">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">{data.name}</h3>
          <span className={`text-xs px-2 py-1 rounded-full ${
            data.status === 'completed' ? 'bg-green-100 text-green-700' :
            data.status === 'failed' ? 'bg-red-100 text-red-700' :
            'bg-gray-100 text-gray-600'
          }`}>
            {data.status}
          </span>
        </div>

        {data.report && (
          <div className="space-y-4 text-sm">
            <div>
              <span className="text-gray-500">Digital Maturity:</span>
              <span className="ml-2 font-medium">{data.report.digital_maturity || 'N/A'}</span>
            </div>
            <div>
              <span className="text-gray-500">AI Adoption:</span>
              <span className="ml-2 font-medium">{data.report.ai_adoption_stage || 'N/A'}</span>
            </div>
            <div>
              <span className="text-gray-500">Pain Points:</span>
              <span className="ml-2 font-medium">{data.report.pain_points?.length || 0}</span>
            </div>
            <div>
              <span className="text-gray-500">Opportunities:</span>
              <span className="ml-2 font-medium">{data.report.opportunities?.length || 0}</span>
            </div>
            <div>
              <span className="text-gray-500">Decision Makers:</span>
              <span className="ml-2 font-medium">{data.report.decision_makers?.length || 0}</span>
            </div>
          </div>
        )}

        <div className="mt-4 pt-4 border-t border-gray-200 space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-500">Use Cases:</span>
            <span className="font-medium">{data.use_cases_count || 0}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Personas:</span>
            <span className="font-medium">{data.personas_count || 0}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Case Studies:</span>
            <span className="font-medium">{data.competitor_case_studies_count || 0}</span>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-5xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Compare Iterations
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto p-6" style={{ maxHeight: 'calc(90vh - 120px)' }}>
          {/* Side by side overview */}
          <div className="flex gap-4 mb-8">
            <IterationColumn data={iteration_a} />
            <div className="flex items-center">
              <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </div>
            <IterationColumn data={iteration_b} />
          </div>

          {/* Differences */}
          <div className="border-t border-gray-200 pt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Changes</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <DiffList diff={differences.pain_points} label="Pain Points" />
              <DiffList diff={differences.opportunities} label="Opportunities" />
              <DiffList diff={differences.talking_points} label="Talking Points" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
