'use client';

import Link from 'next/link';
import { ProjectListItem } from '@/types';

interface ProjectCardProps {
  project: ProjectListItem;
}

export default function ProjectCard({ project }: ProjectCardProps) {
  const statusColors = {
    pending: 'bg-gray-100 text-gray-600',
    running: 'bg-blue-100 text-blue-600',
    completed: 'bg-green-100 text-green-600',
    failed: 'bg-red-100 text-red-600',
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <Link href={`/projects/${project.id}`}>
      <div className="bg-white border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer">
        <div className="flex items-start justify-between mb-2">
          <h3 className="font-semibold text-gray-900 truncate">{project.name}</h3>
          {project.latest_iteration_status && (
            <span className={`text-xs px-2 py-1 rounded-full ${statusColors[project.latest_iteration_status]}`}>
              {project.latest_iteration_status}
            </span>
          )}
        </div>

        <p className="text-sm text-gray-600 mb-3">{project.client_name}</p>

        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              {project.iteration_count} iteration{project.iteration_count !== 1 ? 's' : ''}
            </span>
            <span className={`px-2 py-0.5 rounded ${project.context_mode === 'accumulate' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-700'}`}>
              {project.context_mode === 'accumulate' ? 'Builds context' : 'Fresh starts'}
            </span>
          </div>
          <span>{formatDate(project.updated_at)}</span>
        </div>
      </div>
    </Link>
  );
}
