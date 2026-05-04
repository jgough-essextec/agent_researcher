'use client';
import React from 'react';
import type { OsintJob } from '../../../types/osint';
import { RiskHeatMap } from '../shared/RiskHeatMap';

interface OverviewTabProps {
  job: OsintJob;
}

export function OverviewTab({ job }: OverviewTabProps) {
  const { findings_summary } = job;
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-blue-600">{findings_summary.subdomains_found}</div>
          <div className="text-xs text-gray-500 mt-1">Subdomains</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-blue-600">{findings_summary.dns_records}</div>
          <div className="text-xs text-gray-500 mt-1">DNS Records</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-blue-600">{findings_summary.email_assessments}</div>
          <div className="text-xs text-gray-500 mt-1">Email Domains</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-blue-600">{findings_summary.screenshots}</div>
          <div className="text-xs text-gray-500 mt-1">Screenshots</div>
        </div>
      </div>
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-3">Risk Distribution</h3>
        <RiskHeatMap items={[]} />
        <p className="text-xs text-gray-400 mt-2">Risk heat map will populate after Phase 4 analysis.</p>
      </div>
    </div>
  );
}
