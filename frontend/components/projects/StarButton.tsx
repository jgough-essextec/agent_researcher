'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { WorkProductCategory } from '@/types';

interface StarButtonProps {
  projectId: string;
  contentType: string;
  objectId: string;
  category: WorkProductCategory;
  iterationId?: string;
  isStarred?: boolean;
  onToggle?: (starred: boolean) => void;
  size?: 'sm' | 'md' | 'lg';
}

export default function StarButton({
  projectId,
  contentType,
  objectId,
  category,
  iterationId,
  isStarred = false,
  onToggle,
  size = 'md',
}: StarButtonProps) {
  const [starred, setStarred] = useState(isStarred);
  const [isLoading, setIsLoading] = useState(false);

  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  const handleClick = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsLoading(true);

    try {
      if (starred) {
        // Find and delete the work product
        const workProducts = await api.listWorkProducts(projectId);
        const existing = workProducts.find(
          (wp) => wp.object_id === objectId && wp.content_type_name === contentType
        );
        if (existing) {
          await api.deleteWorkProduct(projectId, existing.id);
        }
        setStarred(false);
        onToggle?.(false);
      } else {
        // Create new work product
        await api.createWorkProduct(projectId, {
          content_type: contentType,
          object_id: objectId,
          category,
          source_iteration_id: iterationId,
        });
        setStarred(true);
        onToggle?.(true);
      }
    } catch (error) {
      console.error('Failed to toggle star:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={isLoading}
      className={`p-1 transition-colors ${
        starred
          ? 'text-yellow-500 hover:text-yellow-600'
          : 'text-gray-400 hover:text-yellow-500'
      } ${isLoading ? 'opacity-50 cursor-wait' : ''}`}
      title={starred ? 'Remove from saved items' : 'Save to work products'}
    >
      <svg
        className={sizeClasses[size]}
        fill={starred ? 'currentColor' : 'none'}
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
  );
}
