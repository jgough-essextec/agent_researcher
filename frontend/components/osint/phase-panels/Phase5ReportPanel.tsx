'use client';
import React, { useState } from 'react';
import { generateOsintReport, getOsintReportDownloadUrl } from '../../../lib/api';

interface Phase5ReportPanelProps {
  jobId: string;
  status: string;
}

export function Phase5ReportPanel({ jobId, status }: Phase5ReportPanelProps) {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    setGenerating(true);
    setError('');
    try {
      await generateOsintReport(jobId);
    } catch {
      setError('Failed to start report generation. Please try again.');
      setGenerating(false);
    }
  };

  if (status === 'completed') {
    return (
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-800">Report Ready</h2>
        <p className="text-gray-600 text-sm">Your OSINT assessment report has been generated.</p>
        <a
          href={getOsintReportDownloadUrl(jobId)}
          download
          className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors"
        >
          Download .docx Report
        </a>
      </div>
    );
  }

  if (status === 'phase5_report') {
    return (
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-800">Generating Report...</h2>
        <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
          <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin flex-shrink-0" />
          <span className="text-sm text-gray-700">Building your OSINT assessment report...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-800">Phase 5: Generate Report</h2>
      <p className="text-gray-600 text-sm">
        All findings have been processed. Generate your final .docx assessment report.
      </p>
      {error && <p className="text-red-600 text-sm">{error}</p>}
      <button
        onClick={handleGenerate}
        disabled={generating}
        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg disabled:opacity-50 transition-colors"
      >
        {generating ? 'Starting...' : 'Generate Report'}
      </button>
    </div>
  );
}
