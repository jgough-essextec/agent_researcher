import React from 'react';
import type { Severity } from '../../../types/osint';

const SEVERITY_STYLES: Record<Severity, string> = {
  critical: 'bg-red-100 text-red-800 border border-red-300',
  high: 'bg-orange-100 text-orange-800 border border-orange-300',
  medium: 'bg-yellow-100 text-yellow-800 border border-yellow-300',
  low: 'bg-green-100 text-green-800 border border-green-300',
  info: 'bg-blue-100 text-blue-800 border border-blue-300',
};

interface SeverityBadgeProps {
  severity: Severity;
  size?: 'sm' | 'md';
}

export function SeverityBadge({ severity, size = 'md' }: SeverityBadgeProps) {
  const sizeClass = size === 'sm' ? 'px-1.5 py-0.5 text-xs' : 'px-2 py-1 text-sm';
  return (
    <span className={`inline-flex items-center rounded font-medium ${sizeClass} ${SEVERITY_STYLES[severity]}`}>
      {severity.toUpperCase()}
    </span>
  );
}
