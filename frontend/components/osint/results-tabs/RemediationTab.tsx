'use client';
import React, { useEffect, useState } from 'react';
import type { ServiceMapping } from '../../../types/osint';
import { getOsintServiceMappings } from '../../../lib/api';

const SERVICE_LABELS: Record<string, string> = {
  mdr_soc: 'MDR / SOC / Threat Monitoring',
  pen_test: 'Penetration Testing / Red Team / ASM',
  vciso_grc: 'vCISO / GRC / Compliance Advisory',
  ir_retainer: 'IR Retainer / Incident Response',
  infrastructure: 'Infrastructure Services',
  digital_workplace: 'Digital Workplace (M365, Endpoint)',
  app_modernization: 'Application Modernization',
  ai_ops: 'AI / Intelligent Operations',
  field_cto: 'Field CTO / Strategic Advisory',
};

const URGENCY_COLORS: Record<string, string> = {
  immediate: 'text-red-700 bg-red-100',
  short_term: 'text-orange-700 bg-orange-100',
  strategic: 'text-blue-700 bg-blue-100',
};

interface RemediationTabProps {
  jobId: string;
}

export function RemediationTab({ jobId }: RemediationTabProps) {
  const [mappings, setMappings] = useState<ServiceMapping[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOsintServiceMappings(jobId).then(setMappings).finally(() => setLoading(false));
  }, [jobId]);

  if (loading) return <div className="text-sm text-gray-500">Loading service mappings...</div>;
  if (!mappings.length) {
    return (
      <div className="text-sm text-gray-500">
        No service mappings yet — complete Phase 4 analysis first.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="font-medium text-gray-800">Recommended Services</h3>
      {mappings.map((m) => (
        <div key={m.id} className="border border-gray-200 rounded-lg p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-medium text-gray-800 text-sm">
              {SERVICE_LABELS[m.service] || m.service}
            </span>
            <span
              className={`text-xs px-2 py-0.5 rounded font-medium ${
                URGENCY_COLORS[m.urgency] || 'text-gray-700 bg-gray-100'
              }`}
            >
              {m.urgency.replace('_', ' ')}
            </span>
          </div>
          <p className="text-sm text-gray-600">{m.finding_summary}</p>
          <p className="text-xs text-gray-500 italic">{m.justification}</p>
        </div>
      ))}
    </div>
  );
}
