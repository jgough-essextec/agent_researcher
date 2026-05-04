'use client';
import React from 'react';

const ANALYSIS_TASKS = [
  'Mapping physical infrastructure',
  'Fingerprinting technology stack',
  'Assessing email security posture',
  'Building risk matrix',
  'Mapping findings to services',
];

export function Phase4AnalysisPanel() {
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-800">Phase 4: Analysis &amp; Enrichment</h2>
      <p className="text-gray-600 text-sm">AI is correlating all findings...</p>
      <div className="space-y-2">
        {ANALYSIS_TASKS.map((task) => (
          <div key={task} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin flex-shrink-0" />
            <span className="text-sm text-gray-700">{task}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
