'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { ResearchJob } from '@/types';
import ResearchResults from '@/components/ResearchResults';
import Link from 'next/link';

export default function ResearchDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [job, setJob] = useState<ResearchJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    const loadJob = async () => {
      try {
        const data = await api.getResearch(id);
        setJob(data);
        setLoading(false);

        // If still running, poll for updates
        if (data.status === 'running' || data.status === 'pending') {
          api.pollResearch(id, (updated) => {
            setJob(updated);
          });
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load research');
        setLoading(false);
      }
    };

    loadJob();
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
      {job && <ResearchResults job={job} />}
    </div>
  );
}
