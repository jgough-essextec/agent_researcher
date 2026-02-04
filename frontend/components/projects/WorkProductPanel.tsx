'use client';

import { useState } from 'react';
import { WorkProduct } from '@/types';
import { api } from '@/lib/api';

interface WorkProductPanelProps {
  projectId: string;
  workProducts: WorkProduct[];
  onUpdate: () => void;
}

export default function WorkProductPanel({
  projectId,
  workProducts,
  onUpdate,
}: WorkProductPanelProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const categoryIcons: Record<string, string> = {
    play: 'M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z',
    persona: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
    insight: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
    one_pager: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    case_study: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10',
    use_case: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01',
    gap: 'M13 10V3L4 14h7v7l9-11h-7z',
    other: 'M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4',
  };

  const categoryColors: Record<string, string> = {
    play: 'bg-purple-100 text-purple-600',
    persona: 'bg-blue-100 text-blue-600',
    insight: 'bg-yellow-100 text-yellow-600',
    one_pager: 'bg-green-100 text-green-600',
    case_study: 'bg-orange-100 text-orange-600',
    use_case: 'bg-cyan-100 text-cyan-600',
    gap: 'bg-red-100 text-red-600',
    other: 'bg-gray-100 text-gray-600',
  };

  const handleRemove = async (id: string) => {
    try {
      await api.deleteWorkProduct(projectId, id);
      onUpdate();
    } catch (error) {
      console.error('Failed to remove work product:', error);
    }
  };

  if (workProducts.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        <svg className="w-12 h-12 mx-auto mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
        </svg>
        <p className="text-sm">No starred items yet</p>
        <p className="text-xs mt-1">Star important findings to save them here</p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-gray-100">
      {workProducts.map((wp) => (
        <div key={wp.id} className="p-3">
          <div
            className="flex items-start gap-3 cursor-pointer"
            onClick={() => setExpandedId(expandedId === wp.id ? null : wp.id)}
          >
            <div className={`p-2 rounded-lg ${categoryColors[wp.category] || categoryColors.other}`}>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={categoryIcons[wp.category] || categoryIcons.other} />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-medium text-gray-900 truncate">
                {wp.content_preview?.title || wp.category}
              </h4>
              <p className="text-xs text-gray-500 mt-0.5">
                From iteration {wp.source_iteration_sequence || '?'}
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleRemove(wp.id);
              }}
              className="p-1 text-gray-400 hover:text-red-500 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {expandedId === wp.id && (
            <div className="mt-2 pl-11">
              {wp.content_preview?.summary && (
                <p className="text-sm text-gray-600">{wp.content_preview.summary}</p>
              )}
              {wp.notes && (
                <div className="mt-2 p-2 bg-gray-50 rounded text-sm text-gray-600">
                  <span className="font-medium">Notes: </span>
                  {wp.notes}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
