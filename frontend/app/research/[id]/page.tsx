'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { ResearchJob } from '@/types';
import ResearchResults from '@/components/ResearchResults';
import Link from 'next/link';

const STUCK_THRESHOLD_MS = 5 * 60 * 1000; // 5 minutes

function isStuck(job: ResearchJob): boolean {
  if (job.status !== 'running') return false;
  const updatedAt = new Date(job.updated_at).getTime();
  return Date.now() - updatedAt > STUCK_THRESHOLD_MS;
}

function StuckJobBanner({ job, onRecovered }: { job: ResearchJob; onRecovered: (j: ResearchJob) => void }) {
  const [recovering, setRecovering] = useState(false);
  const [recoverError, setRecoverError] = useState('');
  const hasReport = !!job.report;

  const handleRecover = async () => {
    setRecovering(true);
    setRecoverError('');
    try {
      const result = await api.recoverResearch(job.id);
      onRecovered(result.job);
    } catch {
      setRecoverError('Recovery failed. Please try again.');
      setRecovering(false);
    }
  };

  return (
    <div className="mb-4 bg-amber-50 border border-amber-300 rounded-xl p-4 flex items-start justify-between gap-4">
      <div>
        <p className="font-medium text-amber-800 text-sm">
          {hasReport
            ? 'This job completed but was not marked as finished due to a server issue.'
            : 'This job appears to be stuck and may have encountered an error.'}
        </p>
        <p className="text-amber-700 text-xs mt-1">
          {hasReport
            ? 'Click "Mark Complete" to restore it — all your results are intact.'
            : 'Click "Retry" to re-run the research from scratch.'}
        </p>
        {recoverError && <p className="text-red-600 text-xs mt-1">{recoverError}</p>}
      </div>
      <button
        onClick={handleRecover}
        disabled={recovering}
        className="flex-shrink-0 px-4 py-2 text-sm font-medium rounded-lg bg-amber-600 hover:bg-amber-700 text-white disabled:opacity-50 transition-colors"
      >
        {recovering ? 'Working...' : hasReport ? 'Mark Complete' : 'Retry'}
      </button>
    </div>
  );
}

export default function ResearchDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [job, setJob] = useState<ResearchJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    let cancelPoll: (() => void) | null = null;

    const loadJob = async () => {
      try {
        const data = await api.getResearch(id);
        setJob(data);
        setLoading(false);

        // If still running, poll for updates (partial/completed/failed are terminal — no poll)
        if (data.status === 'running' || data.status === 'pending') {
          const poller = api.pollResearch(id, (updated) => {
            setJob(updated);
          });
          cancelPoll = poller.cancel;
          poller.promise.catch(console.error);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load research');
        setLoading(false);
      }
    };

    loadJob();

    return () => {
      if (cancelPoll) cancelPoll();
    };
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <p className="text-red-600">{error}</p>
        <Link href="/research" className="text-blue-600 hover:underline mt-2 inline-block">← Back to Research</Link>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4">
        <Link href="/research" className="text-sm text-blue-600 hover:underline">← Back to Research History</Link>
      </div>
      {job && isStuck(job) && (
        <StuckJobBanner job={job} onRecovered={(updated) => setJob(updated)} />
      )}
      {job && <ResearchResults job={job} />}
    </div>
  );
}
