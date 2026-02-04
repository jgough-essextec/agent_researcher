'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Project, IterationCreateData } from '@/types';
import { api } from '@/lib/api';

export default function NewIterationPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<IterationCreateData>({
    name: '',
    sales_history: '',
    prompt_override: '',
  });

  useEffect(() => {
    const loadProject = async () => {
      try {
        const data = await api.getProject(projectId);
        setProject(data);

        // Pre-fill with client name context
        setFormData((prev) => ({
          ...prev,
          name: `v${data.iterations.length + 1}`,
        }));
      } catch (err) {
        setError('Failed to load project');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    loadProject();
  }, [projectId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      // Create the iteration
      const iteration = await api.createIteration(projectId, formData);

      // Optionally start it immediately
      await api.startIteration(projectId, iteration.sequence);

      // Redirect to project dashboard
      router.push(`/projects/${projectId}`);
    } catch (err) {
      setError('Failed to create iteration');
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500 mb-4">{error || 'Project not found'}</p>
        <Link
          href="/projects"
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          Back to Projects
        </Link>
      </div>
    );
  }

  const nextSequence = project.iterations.length + 1;

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <Link
          href={`/projects/${projectId}`}
          className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 mb-4"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to {project.name}
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">New Iteration</h1>
        <p className="text-gray-600 mt-1">
          Start iteration #{nextSequence} for {project.client_name}
        </p>
      </div>

      {/* Context info */}
      {project.context_mode === 'accumulate' && project.iterations.length > 0 && (
        <div className="mb-6 p-4 bg-purple-50 border border-purple-200 rounded-lg">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-purple-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <h4 className="font-medium text-purple-900">Building on Previous Research</h4>
              <p className="text-sm text-purple-700 mt-1">
                This iteration will inherit context from {project.iterations.length} previous iteration{project.iterations.length !== 1 ? 's' : ''},
                including identified pain points, opportunities, and starred items.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-lg border border-gray-200 p-6">
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Iteration Name */}
        <div className="mb-4">
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            Iteration Name
          </label>
          <input
            type="text"
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g., v2 - Focus on AI Solutions"
            className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            Optional label to identify this iteration
          </p>
        </div>

        {/* Sales History */}
        <div className="mb-4">
          <label htmlFor="sales_history" className="block text-sm font-medium text-gray-700 mb-1">
            Sales History / Context
          </label>
          <textarea
            id="sales_history"
            value={formData.sales_history}
            onChange={(e) => setFormData({ ...formData, sales_history: e.target.value })}
            placeholder="Paste any relevant sales notes, meeting summaries, or context about the client engagement..."
            rows={6}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none font-mono text-sm"
          />
        </div>

        {/* Prompt Override */}
        <div className="mb-6">
          <label htmlFor="prompt_override" className="block text-sm font-medium text-gray-700 mb-1">
            Additional Instructions
          </label>
          <textarea
            id="prompt_override"
            value={formData.prompt_override}
            onChange={(e) => setFormData({ ...formData, prompt_override: e.target.value })}
            placeholder="Any specific focus areas or questions for this iteration..."
            rows={3}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
          <p className="text-xs text-gray-500 mt-1">
            Customize the research focus for this iteration
          </p>
        </div>

        {/* Submit */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
          <Link
            href={`/projects/${projectId}`}
            className="px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={isSubmitting}
            className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                Starting...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Start Iteration
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
