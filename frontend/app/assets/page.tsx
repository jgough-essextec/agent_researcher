'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { ResearchJob, UseCase, Persona, OnePager, AccountPlan } from '@/types';
import { api } from '@/lib/api';

type AssetType = 'use_cases' | 'personas' | 'one_pagers' | 'account_plans';

interface JobAssets {
  job: ResearchJob;
  useCases: UseCase[];
  personas: Persona[];
  onePagers: OnePager[];
  accountPlans: AccountPlan[];
  loaded: boolean;
}

export default function AssetsPage() {
  const [jobs, setJobs] = useState<ResearchJob[]>([]);
  const [jobAssets, setJobAssets] = useState<Record<string, JobAssets>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [activeType, setActiveType] = useState<AssetType>('use_cases');
  const [expandedJobs, setExpandedJobs] = useState<Set<string>>(new Set());

  useEffect(() => {
    api.listResearch()
      .then((all) => {
        const completed = all.filter((j) => j.status === 'completed');
        setJobs(completed);
        // Pre-populate empty entries
        const initial: Record<string, JobAssets> = {};
        completed.forEach((j) => {
          initial[j.id] = { job: j, useCases: [], personas: [], onePagers: [], accountPlans: [], loaded: false };
        });
        setJobAssets(initial);
      })
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  const loadJobAssets = async (jobId: string) => {
    if (jobAssets[jobId]?.loaded) return;
    try {
      const [useCases, personas, onePagers, accountPlans] = await Promise.all([
        api.listUseCases(jobId),
        api.listPersonas(jobId),
        api.listOnePagers(jobId),
        api.listAccountPlans(jobId),
      ]);
      setJobAssets((prev) => ({
        ...prev,
        [jobId]: { ...prev[jobId], useCases, personas, onePagers, accountPlans, loaded: true },
      }));
    } catch (err) {
      console.error('Failed to load assets for job:', jobId, err);
    }
  };

  const toggleJob = (jobId: string) => {
    setExpandedJobs((prev) => {
      const next = new Set(prev);
      if (next.has(jobId)) {
        next.delete(jobId);
      } else {
        next.add(jobId);
        loadJobAssets(jobId);
      }
      return next;
    });
  };

  const typeLabels: Record<AssetType, string> = {
    use_cases: 'Use Cases',
    personas: 'Personas',
    one_pagers: 'One-Pagers',
    account_plans: 'Account Plans',
  };

  const getAssetsForType = (assets: JobAssets, type: AssetType) => {
    switch (type) {
      case 'use_cases': return assets.useCases;
      case 'personas': return assets.personas;
      case 'one_pagers': return assets.onePagers;
      case 'account_plans': return assets.accountPlans;
    }
  };

  const getTitleForAsset = (asset: UseCase | Persona | OnePager | AccountPlan) => {
    return 'title' in asset ? asset.title : ('name' in asset ? (asset as Persona).name : '');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="text-center py-16">
        <h1 className="text-2xl font-bold text-gray-900 mb-3">Assets</h1>
        <p className="text-gray-500 mb-6">No completed research jobs yet. Generated assets will appear here.</p>
        <Link href="/" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
          Start Research
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Assets</h1>
        <p className="text-sm text-gray-500">{jobs.length} completed research job{jobs.length !== 1 ? 's' : ''}</p>
      </div>

      {/* Asset type filter */}
      <div className="flex gap-2 mb-6 border-b border-gray-200 pb-4">
        {(Object.keys(typeLabels) as AssetType[]).map((type) => (
          <button
            key={type}
            onClick={() => setActiveType(type)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              activeType === type
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {typeLabels[type]}
          </button>
        ))}
      </div>

      {/* Jobs list */}
      <div className="space-y-3">
        {jobs.map((job) => {
          const assets = jobAssets[job.id];
          const isExpanded = expandedJobs.has(job.id);
          const typeAssets = assets?.loaded ? getAssetsForType(assets, activeType) : [];

          return (
            <div key={job.id} className="border border-gray-200 rounded-lg bg-white overflow-hidden">
              <button
                onClick={() => toggleJob(job.id)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors text-left"
              >
                <div className="flex items-center gap-3">
                  <svg
                    className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <div>
                    <p className="font-medium text-gray-900">{job.client_name}</p>
                    {job.vertical && (
                      <p className="text-xs text-gray-500 capitalize">{job.vertical.replace('_', ' ')}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {assets?.loaded && (
                    <span className="text-xs text-gray-500">
                      {typeAssets.length} {typeLabels[activeType].toLowerCase()}
                    </span>
                  )}
                  <Link
                    href={`/research/${job.id}`}
                    onClick={(e) => e.stopPropagation()}
                    className="text-xs text-blue-600 hover:text-blue-800 hover:underline"
                  >
                    View Research →
                  </Link>
                </div>
              </button>

              {isExpanded && (
                <div className="border-t border-gray-100 px-4 py-3">
                  {!assets?.loaded ? (
                    <div className="flex items-center justify-center py-4">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500" />
                    </div>
                  ) : typeAssets.length === 0 ? (
                    <p className="text-sm text-gray-500 py-2">
                      No {typeLabels[activeType].toLowerCase()} generated yet.{' '}
                      <Link href={`/research/${job.id}`} className="text-blue-600 hover:underline">
                        Generate from research →
                      </Link>
                    </p>
                  ) : (
                    <ul className="space-y-2">
                      {typeAssets.map((asset) => (
                        <li key={asset.id} className="flex items-start gap-2 text-sm text-gray-800">
                          <span className="text-blue-400 mt-0.5">•</span>
                          <span>{getTitleForAsset(asset)}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
