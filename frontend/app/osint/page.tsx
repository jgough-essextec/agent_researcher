'use client';
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import type { OsintJob } from '../../types/osint';
import { listOsintJobs } from '../../lib/api';

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending: { label: 'Pending', color: 'bg-gray-100 text-gray-600' },
  phase1_research: { label: 'Researching', color: 'bg-blue-100 text-blue-700' },
  phase1_complete: { label: 'Researching', color: 'bg-blue-100 text-blue-700' },
  phase2_auto: { label: 'DNS Analysis', color: 'bg-blue-100 text-blue-700' },
  awaiting_terminal_output: { label: 'Awaiting Terminal', color: 'bg-yellow-100 text-yellow-700' },
  phase2_processing: { label: 'Processing DNS', color: 'bg-blue-100 text-blue-700' },
  awaiting_screenshots: { label: 'Awaiting Screenshots', color: 'bg-yellow-100 text-yellow-700' },
  phase3_processing: { label: 'Processing Screenshots', color: 'bg-blue-100 text-blue-700' },
  phase4_analysis: { label: 'Analysing', color: 'bg-blue-100 text-blue-700' },
  phase5_report: { label: 'Generating Report', color: 'bg-blue-100 text-blue-700' },
  completed: { label: 'Complete', color: 'bg-green-100 text-green-700' },
  failed: { label: 'Failed', color: 'bg-red-100 text-red-700' },
};

export default function OsintListPage() {
  const [jobs, setJobs] = useState<OsintJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listOsintJobs().then(setJobs).finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-800">OSINT Assessments</h1>
        <Link
          href="/osint/new"
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
        >
          + New Assessment
        </Link>
      </div>

      {loading ? (
        <div className="text-gray-500 text-sm">Loading...</div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <p className="text-lg mb-2">No OSINT assessments yet</p>
          <Link href="/osint/new" className="text-blue-600 hover:underline text-sm">
            Create your first assessment
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => {
            const statusInfo =
              STATUS_LABELS[job.status] || { label: job.status, color: 'bg-gray-100 text-gray-600' };
            return (
              <Link
                key={job.id}
                href={`/osint/${job.id}`}
                className="block border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-sm transition-all"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium text-gray-800">{job.organization_name}</span>
                    <span className="text-sm text-gray-500 ml-2">{job.primary_domain}</span>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded font-medium ${statusInfo.color}`}>
                    {statusInfo.label}
                  </span>
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  {new Date(job.created_at).toLocaleDateString()}
                  {job.findings_summary.subdomains_found > 0 &&
                    ` · ${job.findings_summary.subdomains_found} subdomains`}
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
