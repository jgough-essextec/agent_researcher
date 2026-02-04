'use client';

import { useState } from 'react';
import { Project, ContextMode } from '@/types';
import { api } from '@/lib/api';

interface ProjectHeaderProps {
  project: Project;
  onUpdate: (project: Project) => void;
}

export default function ProjectHeader({ project, onUpdate }: ProjectHeaderProps) {
  const [contextMode, setContextMode] = useState<ContextMode>(project.context_mode);
  const [isSaving, setIsSaving] = useState(false);

  const handleContextModeChange = async (mode: ContextMode) => {
    setContextMode(mode);
    setIsSaving(true);
    try {
      const updated = await api.updateProject(project.id, { context_mode: mode });
      onUpdate(updated);
    } catch (error) {
      console.error('Failed to update context mode:', error);
      setContextMode(project.context_mode);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
          <p className="text-gray-600 mt-1">{project.client_name}</p>
          {project.description && (
            <p className="text-sm text-gray-500 mt-2 max-w-2xl">{project.description}</p>
          )}
        </div>

        <div className="flex items-center gap-4">
          {/* Context Mode Toggle */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Context:</span>
            <div className="flex rounded-lg overflow-hidden border border-gray-200">
              <button
                onClick={() => handleContextModeChange('accumulate')}
                disabled={isSaving}
                className={`px-3 py-1.5 text-sm font-medium transition-colors ${
                  contextMode === 'accumulate'
                    ? 'bg-purple-100 text-purple-700'
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                }`}
              >
                Build
              </button>
              <button
                onClick={() => handleContextModeChange('fresh')}
                disabled={isSaving}
                className={`px-3 py-1.5 text-sm font-medium transition-colors ${
                  contextMode === 'fresh'
                    ? 'bg-gray-200 text-gray-700'
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                }`}
              >
                Fresh
              </button>
            </div>
          </div>

          {/* Stats */}
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span>{project.iterations.length} iterations</span>
            <span>{project.work_products_count} saved items</span>
          </div>
        </div>
      </div>
    </div>
  );
}
