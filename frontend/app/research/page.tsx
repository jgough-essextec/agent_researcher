'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { ResearchJob } from '@/types';
import Link from 'next/link';

export default function ResearchListPage() {
  const [jobs, setJobs] = useState<ResearchJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listResearch().then((data) => {
      setJobs(data);
      setLoading(false);
    }).catch((err) => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Research History</h2>
          <p className="text-sm text-gray-500 mt-1">{jobs.length} research job{jobs.length !== 1 ? 's' : ''}</p>
        </div>
        <Link
          href="/"
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          New Research
        </Link>
      </div>

      {jobs.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No research jobs yet. Start one from the home page.</p>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <Link
              key={job.id}
              href={`/research/${job.id}`}
              className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900">{job.client_name}</h3>
                  <div className="flex items-center gap-3 mt-1">
                    {job.vertical && (
                      <span className="text-sm text-gray-500 capitalize">{job.vertical.replace('_', ' ')}</span>
                    )}
                    <span className="text-sm text-gray-400">
                      {new Date(job.created_at).toLocaleDateString()} {new Date(job.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  job.status === 'completed' ? 'bg-green-100 text-green-800' :
                  job.status === 'failed' ? 'bg-red-100 text-red-800' :
                  job.status === 'running' ? 'bg-blue-100 text-blue-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {job.status}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
