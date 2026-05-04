'use client';
import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import type { OsintJob } from '../../../types/osint';
import { getOsintJob, executeOsintJob } from '../../../lib/api';
import { PhasesStepper } from '../../../components/osint/PhasesStepper';
import { Phase1RunningPanel } from '../../../components/osint/phase-panels/Phase1RunningPanel';
import { Phase2DnsPanel } from '../../../components/osint/phase-panels/Phase2DnsPanel';
import { Phase3ScreenshotPanel } from '../../../components/osint/phase-panels/Phase3ScreenshotPanel';
import { Phase4AnalysisPanel } from '../../../components/osint/phase-panels/Phase4AnalysisPanel';
import { Phase5ReportPanel } from '../../../components/osint/phase-panels/Phase5ReportPanel';
import { OverviewTab } from '../../../components/osint/results-tabs/OverviewTab';
import { EmailSecurityTab } from '../../../components/osint/results-tabs/EmailSecurityTab';
import { InfrastructureTab } from '../../../components/osint/results-tabs/InfrastructureTab';
import { RemediationTab } from '../../../components/osint/results-tabs/RemediationTab';
import { ReportTab } from '../../../components/osint/results-tabs/ReportTab';

const POLLING_STATUSES = [
  'phase1_research',
  'phase1_complete',
  'phase2_auto',
  'phase2_processing',
  'phase3_processing',
  'phase4_analysis',
  'phase5_report',
];

const RESULT_PHASES = ['phase4_analysis', 'phase5_report', 'completed'];

type ResultsTab = 'overview' | 'infrastructure' | 'email' | 'remediation' | 'report';

const RESULT_TABS: { key: ResultsTab; label: string }[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'infrastructure', label: 'Infrastructure' },
  { key: 'email', label: 'Email Security' },
  { key: 'remediation', label: 'Remediation' },
  { key: 'report', label: 'Report' },
];

export default function OsintJobPage() {
  const { id } = useParams<{ id: string }>();
  const [job, setJob] = useState<OsintJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<ResultsTab>('overview');
  const [executing, setExecuting] = useState(false);

  const fetchJob = useCallback(async () => {
    try {
      const data = await getOsintJob(id);
      setJob(data);
    } catch {
      // ignore transient fetch errors
    }
  }, [id]);

  useEffect(() => {
    fetchJob().finally(() => setLoading(false));
  }, [fetchJob]);

  useEffect(() => {
    if (!job || !POLLING_STATUSES.includes(job.status)) return;
    const interval = setInterval(fetchJob, 3000);
    return () => clearInterval(interval);
  }, [job, fetchJob]);

  const handleExecute = async () => {
    if (!job) return;
    setExecuting(true);
    try {
      const updated = await executeOsintJob(job.id);
      setJob(updated);
    } finally {
      setExecuting(false);
    }
  };

  if (loading) return <div className="p-8 text-gray-500">Loading...</div>;
  if (!job) return <div className="p-8 text-gray-500">Job not found.</div>;

  const showResults = RESULT_PHASES.includes(job.status) || job.status === 'completed';

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4">
        <h1 className="text-xl font-semibold text-gray-800">{job.organization_name}</h1>
        <p className="text-sm text-gray-500">{job.primary_domain} — OSINT Assessment</p>
      </div>

      <div className="flex">
        {/* Left rail: Phase stepper */}
        <div className="w-52 flex-shrink-0 border-r border-gray-200 p-4 sticky top-0 h-screen overflow-y-auto">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Phases</h2>
          <PhasesStepper status={job.status} phaseProgress={job.phase_progress} />
        </div>

        {/* Main content */}
        <div className="flex-1 p-6 space-y-6">
          {/* Pending state */}
          {job.status === 'pending' && (
            <div className="space-y-3">
              <p className="text-gray-600 text-sm">
                Ready to begin OSINT analysis for <strong>{job.organization_name}</strong>.
              </p>
              <button
                onClick={handleExecute}
                disabled={executing}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg disabled:opacity-50 transition-colors"
              >
                {executing ? 'Starting...' : 'Start OSINT Analysis'}
              </button>
            </div>
          )}

          {/* Phase 1 */}
          {(['phase1_research', 'phase1_complete'] as string[]).includes(job.status) && (
            <Phase1RunningPanel organizationName={job.organization_name} />
          )}

          {/* Phase 2 awaiting terminal */}
          {job.status === 'awaiting_terminal_output' && (
            <Phase2DnsPanel jobId={job.id} onSubmitted={fetchJob} />
          )}

          {/* Phase 2 processing */}
          {job.status === 'phase2_processing' && (
            <div className="space-y-3">
              <h2 className="text-xl font-semibold text-gray-800">Analysing DNS Output...</h2>
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                <span className="text-sm text-gray-700">
                  Processing your terminal output with Gemini AI...
                </span>
              </div>
            </div>
          )}

          {/* Phase 3 screenshots */}
          {job.status === 'awaiting_screenshots' && (
            <Phase3ScreenshotPanel
              jobId={job.id}
              primaryDomain={job.primary_domain}
              onSubmitted={fetchJob}
              onSkipped={fetchJob}
            />
          )}

          {/* Phase 3/4 processing */}
          {(['phase3_processing', 'phase4_analysis'] as string[]).includes(job.status) && (
            <Phase4AnalysisPanel />
          )}

          {/* Failed state */}
          {job.status === 'failed' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <h3 className="font-medium text-red-800">Analysis Failed</h3>
              <p className="text-sm text-red-600 mt-1">
                {job.error || 'An unexpected error occurred.'}
              </p>
            </div>
          )}

          {/* Results tabs — visible after Phase 4 */}
          {showResults && (
            <div className="space-y-4">
              <div className="border-b border-gray-200">
                <div className="flex gap-1 overflow-x-auto">
                  {RESULT_TABS.map((tab) => (
                    <button
                      key={tab.key}
                      onClick={() => setActiveTab(tab.key)}
                      className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                        activeTab === tab.key
                          ? 'border-blue-600 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700'
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="pt-2">
                {activeTab === 'overview' && <OverviewTab job={job} />}
                {activeTab === 'infrastructure' && <InfrastructureTab jobId={job.id} />}
                {activeTab === 'email' && <EmailSecurityTab jobId={job.id} />}
                {activeTab === 'remediation' && <RemediationTab jobId={job.id} />}
                {activeTab === 'report' && <ReportTab job={job} />}
              </div>
            </div>
          )}

          {/* Phase 5 report panel when status is phase5 but results not yet shown */}
          {(job.status === 'phase5_report' || job.status === 'completed') && !showResults && (
            <Phase5ReportPanel jobId={job.id} status={job.status} />
          )}
        </div>
      </div>
    </div>
  );
}
