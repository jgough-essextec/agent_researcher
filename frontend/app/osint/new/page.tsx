'use client';
import React, { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import type { CreateOsintJobParams } from '../../../types/osint';
import { createOsintJob, executeOsintJob } from '../../../lib/api';

const DOMAIN_REGEX =
  /^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$/;

function NewOsintJobForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const [form, setForm] = useState<CreateOsintJobParams>({
    organization_name: searchParams.get('name') || '',
    primary_domain: searchParams.get('domain') || '',
    additional_domains: [],
    engagement_context: '',
    research_job: searchParams.get('researchJobId') || null,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.organization_name.trim() || !form.primary_domain.trim()) {
      setError('Organization name and primary domain are required.');
      return;
    }
    if (!DOMAIN_REGEX.test(form.primary_domain.trim())) {
      setError('Please enter a valid domain (e.g., example.com)');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      const job = await createOsintJob({
        ...form,
        primary_domain: form.primary_domain.trim().toLowerCase(),
      });
      // Auto-execute and redirect
      await executeOsintJob(job.id).catch(() => {});
      router.push(`/osint/${job.id}`);
    } catch {
      setError('Failed to create job. Please try again.');
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-800">New OSINT Assessment</h1>
        <p className="text-sm text-gray-500 mt-1">Passive, legal reconnaissance. No active scanning.</p>
      </div>

      {searchParams.get('researchJobId') && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-700">
          Launched from existing research job — fields pre-filled from research results.
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-4">
          <h2 className="font-medium text-gray-800 text-sm uppercase tracking-wide">Core Identity</h2>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Prospect Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={form.organization_name}
              onChange={(e) =>
                setForm((f) => ({ ...f, organization_name: e.target.value }))
              }
              placeholder="e.g., Acme Corporation"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Primary Domain <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={form.primary_domain}
              onChange={(e) =>
                setForm((f) => ({ ...f, primary_domain: e.target.value }))
              }
              placeholder="e.g., acme.com"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Engagement Context
            </label>
            <textarea
              value={form.engagement_context}
              onChange={(e) =>
                setForm((f) => ({ ...f, engagement_context: e.target.value }))
              }
              placeholder="Brief context about this engagement..."
              rows={2}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>
        </div>

        {error && <p className="text-red-600 text-sm">{error}</p>}

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={submitting}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg disabled:opacity-50 transition-colors"
          >
            {submitting ? 'Creating...' : 'Launch OSINT Analysis'}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 text-sm"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

export default function NewOsintJobPage() {
  return (
    <Suspense fallback={<div className="p-6 text-gray-500">Loading...</div>}>
      <NewOsintJobForm />
    </Suspense>
  );
}
