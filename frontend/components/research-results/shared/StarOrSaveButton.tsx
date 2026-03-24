'use client';

import { useState } from 'react';
import StarButton from '@/components/projects/StarButton';
import SaveToDealModal from '@/components/SaveToDealModal';
import { WorkProductCategory } from '@/types';

interface StarOrSaveButtonProps {
  projectId?: string;
  iterationId?: string;
  clientName: string;
  contentType: string;
  objectId: string;
  category: WorkProductCategory;
  size?: 'sm' | 'md' | 'lg';
}

export default function StarOrSaveButton({
  projectId,
  iterationId,
  clientName,
  contentType,
  objectId,
  category,
  size = 'sm',
}: StarOrSaveButtonProps) {
  const [modalOpen, setModalOpen] = useState(false);
  const [saved, setSaved] = useState(false);

  if (projectId) {
    return (
      <StarButton
        projectId={projectId}
        contentType={contentType}
        objectId={objectId}
        category={category}
        iterationId={iterationId}
        size={size}
      />
    );
  }

  return (
    <>
      <button
        onClick={(e) => { e.stopPropagation(); setModalOpen(true); }}
        className={`p-1 transition-colors ${
          saved ? 'text-yellow-500 hover:text-yellow-600' : 'text-gray-400 hover:text-yellow-500'
        }`}
        title={saved ? 'Saved to deal' : 'Save to deal'}
      >
        <svg
          className="w-4 h-4"
          fill={saved ? 'currentColor' : 'none'}
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
          />
        </svg>
      </button>
      {modalOpen && (
        <SaveToDealModal
          clientName={clientName}
          contentType={contentType}
          objectId={objectId}
          category={category}
          onClose={() => setModalOpen(false)}
          onSaved={() => setSaved(true)}
        />
      )}
    </>
  );
}
