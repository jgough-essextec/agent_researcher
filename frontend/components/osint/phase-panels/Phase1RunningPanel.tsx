'use client';
import React from 'react';

interface Phase1RunningPanelProps {
  organizationName: string;
}

const RESEARCH_TASKS = [
  'Company profile & history',
  'Breach & incident history',
  'Job postings & technology gaps',
  'Vendor relationships',
  'Regulatory framework',
  'Leadership intelligence',
];

export function Phase1RunningPanel({ organizationName }: Phase1RunningPanelProps) {
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-800">Phase 1: Web Research</h2>
      <p className="text-gray-600">
        Researching <strong>{organizationName}</strong> using Gemini AI with Google Search grounding...
      </p>
      <div className="space-y-2">
        {RESEARCH_TASKS.map((task) => (
          <div key={task} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin flex-shrink-0" />
            <span className="text-sm text-gray-700">{task}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
