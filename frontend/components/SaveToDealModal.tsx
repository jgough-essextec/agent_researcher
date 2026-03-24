'use client';

import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { api } from '@/lib/api';
import { ProjectListItem, WorkProductCategory } from '@/types';

interface SaveToDealModalProps {
  clientName: string;
  contentType: string;
  objectId: string;
  category: WorkProductCategory;
  onClose: () => void;
  onSaved: () => void;
}

function ModalContent({
  clientName,
  contentType,
  objectId,
  category,
  onClose,
  onSaved,
}: SaveToDealModalProps) {
  const [tab, setTab] = useState<'existing' | 'new'>('existing');
  const [projects, setProjects] = useState<ProjectListItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [newProjectName, setNewProjectName] = useState('');
  const [loading, setLoading] = useState(false);
  const [fetchingProjects, setFetchingProjects] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listProjects().then((list) => {
      setProjects(list);
      if (list.length === 0) setTab('new');
    }).catch(() => {
      setTab('new');
    }).finally(() => setFetchingProjects(false));
  }, []);

  const handleSave = async () => {
    setError(null);

    // Validate before touching loading state
    if (tab === 'new' && !newProjectName.trim()) {
      setError('Enter a deal name');
      return;
    }
    if (tab === 'existing' && !selectedProjectId) {
      setError('Select a deal');
      return;
    }

    setLoading(true);
    try {
      let projectId = selectedProjectId;
      if (tab === 'new') {
        const project = await api.createProject({
          name: newProjectName.trim(),
          client_name: clientName,
        });
        projectId = project.id;
      }
      await api.createWorkProduct(projectId, {
        content_type: contentType,
        object_id: objectId,
        category,
      });
      onSaved();
      onClose();
    } catch {
      setError('Failed to save — please try again');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">Save to Deal</h2>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
            aria-label="Close"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-5 space-y-4">
          {projects.length > 0 && (
            <div className="flex rounded-md border border-gray-200 overflow-hidden text-sm">
              <button
                onClick={() => setTab('existing')}
                className={`flex-1 py-2 font-medium transition-colors ${
                  tab === 'existing' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                Existing Deal
              </button>
              <button
                onClick={() => setTab('new')}
                className={`flex-1 py-2 font-medium transition-colors border-l border-gray-200 ${
                  tab === 'new' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                New Deal
              </button>
            </div>
          )}

          {tab === 'existing' ? (
            fetchingProjects ? (
              <div className="flex items-center justify-center py-6">
                <svg className="animate-spin h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              </div>
            ) : (
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">Select deal</label>
                <select
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Choose a deal...</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} {p.client_name !== p.name ? `(${p.client_name})` : ''}
                    </option>
                  ))}
                </select>
              </div>
            )
          ) : (
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Deal name</label>
                <input
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder={`${clientName} Deal`}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <p className="text-xs text-gray-500">
                A new deal will be created for <strong>{clientName}</strong>. You can add more research rounds from the deal dashboard.
              </p>
            </div>
          )}

          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>

        <div className="flex items-center justify-end gap-2 px-5 py-4 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50 transition-colors"
          >
            {loading && (
              <svg className="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            )}
            Save
          </button>
        </div>
      </div>
    </div>
  );
}

export default function SaveToDealModal(props: SaveToDealModalProps) {
  if (typeof document === 'undefined') return null;
  return createPortal(<ModalContent {...props} />, document.body);
}
