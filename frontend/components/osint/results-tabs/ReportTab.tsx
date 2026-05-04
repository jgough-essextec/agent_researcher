'use client';
import React from 'react';
import type { OsintJob } from '../../../types/osint';
import { Phase5ReportPanel } from '../phase-panels/Phase5ReportPanel';

interface ReportTabProps {
  job: OsintJob;
}

export function ReportTab({ job }: ReportTabProps) {
  return (
    <div className="space-y-4">
      <Phase5ReportPanel jobId={job.id} status={job.status} />
    </div>
  );
}
