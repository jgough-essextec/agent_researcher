'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { api } from '@/lib/api';
import { ResearchFormData, ResearchJob } from '@/types';
import PromptEditor from './PromptEditor';

export default function ResearchForm() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentJob, setCurrentJob] = useState<ResearchJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [prompt, setPrompt] = useState('');

  const { register, handleSubmit, formState: { errors } } = useForm<ResearchFormData>();

  useEffect(() => {
    // Load default prompt
    api.getDefaultPrompt().then((p) => {
      setPrompt(p.content);
    }).catch(console.error);
  }, []);

  const onSubmit = async (data: ResearchFormData) => {
    setIsSubmitting(true);
    setError(null);
    setCurrentJob(null);

    try {
      const job = await api.createResearch({
        ...data,
        prompt,
      });
      setCurrentJob(job);

      // Poll for results
      await api.pollResearch(job.id, (updatedJob) => {
        setCurrentJob(updatedJob);
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div>
          <label htmlFor="client_name" className="block text-sm font-medium text-gray-700 mb-1">
            Client Name <span className="text-red-500">*</span>
          </label>
          <input
            id="client_name"
            type="text"
            {...register('client_name', { required: 'Client name is required' })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter client or company name"
          />
          {errors.client_name && (
            <p className="mt-1 text-sm text-red-500">{errors.client_name.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="sales_history" className="block text-sm font-medium text-gray-700 mb-1">
            Past Sales History
          </label>
          <textarea
            id="sales_history"
            {...register('sales_history')}
            rows={4}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter any relevant past sales history, interactions, or notes about this client..."
          />
        </div>

        <PromptEditor value={prompt} onChange={setPrompt} />

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? 'Running Research...' : 'Run Research'}
        </button>
      </form>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {currentJob && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-gray-900">Research Results</h3>
              <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                currentJob.status === 'completed' ? 'bg-green-100 text-green-800' :
                currentJob.status === 'failed' ? 'bg-red-100 text-red-800' :
                currentJob.status === 'running' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {currentJob.status}
              </span>
            </div>
          </div>
          <div className="p-4">
            {currentJob.status === 'running' || currentJob.status === 'pending' ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-3 text-gray-600">Researching...</span>
              </div>
            ) : currentJob.status === 'failed' ? (
              <p className="text-red-600">{currentJob.error || 'Research failed'}</p>
            ) : (
              <div className="prose prose-sm max-w-none">
                <pre className="whitespace-pre-wrap text-sm text-gray-800 bg-gray-50 p-4 rounded-lg overflow-auto">
                  {currentJob.result}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
