'use client';

import { useState } from 'react';
import { Annotation } from '@/types';
import { api } from '@/lib/api';

interface AnnotationPanelProps {
  projectId: string;
  annotations: Annotation[];
  onUpdate: () => void;
}

export default function AnnotationPanel({
  projectId,
  annotations,
  onUpdate,
}: AnnotationPanelProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState('');

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleEdit = (annotation: Annotation) => {
    setEditingId(annotation.id);
    setEditText(annotation.text);
  };

  const handleSave = async (id: string) => {
    try {
      await api.updateAnnotation(projectId, id, { text: editText });
      setEditingId(null);
      setEditText('');
      onUpdate();
    } catch (error) {
      console.error('Failed to update annotation:', error);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteAnnotation(projectId, id);
      onUpdate();
    } catch (error) {
      console.error('Failed to delete annotation:', error);
    }
  };

  if (annotations.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        <svg className="w-12 h-12 mx-auto mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
        </svg>
        <p className="text-sm">No notes yet</p>
        <p className="text-xs mt-1">Add notes to track your thoughts</p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-gray-100">
      {annotations.map((annotation) => (
        <div key={annotation.id} className="p-3">
          {editingId === annotation.id ? (
            <div>
              <textarea
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
              />
              <div className="flex justify-end gap-2 mt-2">
                <button
                  onClick={() => setEditingId(null)}
                  className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleSave(annotation.id)}
                  className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  Save
                </button>
              </div>
            </div>
          ) : (
            <div>
              <p className="text-sm text-gray-700">{annotation.text}</p>
              <div className="flex items-center justify-between mt-2">
                <span className="text-xs text-gray-500">
                  {formatDate(annotation.created_at)}
                </span>
                <div className="flex gap-1">
                  <button
                    onClick={() => handleEdit(annotation)}
                    className="p-1 text-gray-400 hover:text-blue-500 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => handleDelete(annotation.id)}
                    className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
