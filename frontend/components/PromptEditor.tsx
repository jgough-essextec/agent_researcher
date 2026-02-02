'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface PromptEditorProps {
  value: string;
  onChange: (value: string) => void;
}

export default function PromptEditor({ value, onChange }: PromptEditorProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [savedMessage, setSavedMessage] = useState('');

  useEffect(() => {
    // Load default prompt on mount if no value
    if (!value) {
      api.getDefaultPrompt().then((prompt) => {
        onChange(prompt.content);
      }).catch(console.error);
    }
  }, []);

  const handleSaveAsDefault = async () => {
    setIsSaving(true);
    try {
      await api.updateDefaultPrompt(value);
      setSavedMessage('Saved as default!');
      setTimeout(() => setSavedMessage(''), 3000);
    } catch (error) {
      console.error('Failed to save prompt:', error);
      setSavedMessage('Failed to save');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 bg-gray-50 flex items-center justify-between hover:bg-gray-100 transition-colors"
      >
        <span className="font-medium text-gray-700">
          Research Prompt
        </span>
        <svg
          className={`w-5 h-5 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isExpanded && (
        <div className="p-4 border-t border-gray-200">
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            rows={12}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
            placeholder="Enter your research prompt template..."
          />
          <div className="mt-3 flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Use <code className="bg-gray-100 px-1 rounded">{'{client_name}'}</code> and{' '}
              <code className="bg-gray-100 px-1 rounded">{'{sales_history}'}</code> as placeholders.
            </p>
            <div className="flex items-center gap-2">
              {savedMessage && (
                <span className="text-sm text-green-600">{savedMessage}</span>
              )}
              <button
                type="button"
                onClick={handleSaveAsDefault}
                disabled={isSaving}
                className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50 transition-colors"
              >
                {isSaving ? 'Saving...' : 'Save as Default'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
