'use client';
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import type { OsintJob } from '../../types/osint';
import { listOsintJobs } from '../../lib/api';

interface OsintLaunchPanelProps {
  researchJobId: string;
  companyName?: string;
  domain?: string;
}

export function OsintLaunchPanel({
  researchJobId,
  companyName = '',
  domain = '',
}: OsintLaunchPanelProps) {
  const [linkedJob, setLinkedJob] = useState<OsintJob | null | undefined>(undefined);

  useEffect(() => {
    listOsintJobs()
      .then((jobs) => {
        const found = jobs.find((j) => j.research_job === researchJobId);
        setLinkedJob(found || null);
      })
      .catch(() => setLinkedJob(null));
  }, [researchJobId]);

  const params = new URLSearchParams({
    researchJobId,
    ...(companyName && { name: companyName }),
    ...(domain && { domain }),
  });

  if (linkedJob === undefined) {
    return <div className="text-sm text-gray-500 p-4">Loading OSINT status...</div>;
  }

  if (linkedJob) {
    const statusMap: Record<string, string> = {
      completed: 'Complete',
      awaiting_terminal_output: 'Awaiting your terminal commands',
      awaiting_screenshots: 'Awaiting screenshots',
      failed: 'Failed',
    };
    return (
      <div className="p-4 space-y-4">
        <h3 className="font-medium text-gray-800">OSINT Assessment Active</h3>
        <p className="text-sm text-gray-500">
          Status: {statusMap[linkedJob.status] || linkedJob.status}
        </p>
        <Link
          href={`/osint/${linkedJob.id}`}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
        >
          View Assessment
        </Link>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      <h3 className="font-medium text-gray-800">OSINT Infrastructure Assessment</h3>
      <p className="text-sm text-gray-600">
        Run a passive OSINT analysis to map the infrastructure, identify security gaps, and generate
        a professional assessment report for this prospect.
      </p>
      <ul className="text-xs text-gray-500 space-y-1 list-disc list-inside">
        <li>Certificate transparency &amp; subdomain discovery</li>
        <li>Email security posture (SPF/DKIM/DMARC)</li>
        <li>Infrastructure &amp; technology fingerprinting</li>
        <li>Professional .docx report with Pellera service mapping</li>
      </ul>
      <Link
        href={`/osint/new?${params.toString()}`}
        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
      >
        Launch OSINT Analysis
      </Link>
    </div>
  );
}
