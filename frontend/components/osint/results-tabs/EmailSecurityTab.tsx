'use client';
import React, { useEffect, useState } from 'react';
import type { EmailSecurityFinding } from '../../../types/osint';
import { getOsintEmailSecurity } from '../../../lib/api';

interface EmailSecurityTabProps {
  jobId: string;
}

function GradeColor({ grade }: { grade: string }) {
  const colors: Record<string, string> = {
    A: 'text-green-600 bg-green-100',
    B: 'text-blue-600 bg-blue-100',
    C: 'text-yellow-600 bg-yellow-100',
    D: 'text-orange-600 bg-orange-100',
    F: 'text-red-600 bg-red-100',
  };
  return (
    <span className={`text-2xl font-bold px-3 py-1 rounded ${colors[grade] || 'text-gray-600 bg-gray-100'}`}>
      {grade || '?'}
    </span>
  );
}

export function EmailSecurityTab({ jobId }: EmailSecurityTabProps) {
  const [findings, setFindings] = useState<EmailSecurityFinding[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOsintEmailSecurity(jobId)
      .then(setFindings)
      .finally(() => setLoading(false));
  }, [jobId]);

  if (loading) return <div className="text-sm text-gray-500">Loading email security analysis...</div>;
  if (!findings.length) return <div className="text-sm text-gray-500">No email security data yet.</div>;

  return (
    <div className="space-y-6">
      {findings.map((f) => (
        <div key={f.id} className="border border-gray-200 rounded-lg p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-gray-800">{f.domain}</h3>
            <GradeColor grade={f.overall_grade} />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div
              className={`rounded-lg p-3 text-center ${
                f.has_spf
                  ? 'bg-green-50 border border-green-200'
                  : 'bg-red-50 border border-red-200'
              }`}
            >
              <div className={`font-bold text-sm ${f.has_spf ? 'text-green-700' : 'text-red-700'}`}>
                SPF
              </div>
              <div className={`text-xs mt-1 ${f.has_spf ? 'text-green-600' : 'text-red-600'}`}>
                {f.has_spf ? f.spf_assessment : 'MISSING'}
              </div>
            </div>
            <div
              className={`rounded-lg p-3 text-center ${
                f.has_dmarc
                  ? 'bg-green-50 border border-green-200'
                  : 'bg-red-50 border border-red-200'
              }`}
            >
              <div className={`font-bold text-sm ${f.has_dmarc ? 'text-green-700' : 'text-red-700'}`}>
                DMARC
              </div>
              <div className={`text-xs mt-1 ${f.has_dmarc ? 'text-green-600' : 'text-red-600'}`}>
                {f.dmarc_policy || 'MISSING'}
              </div>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-center">
              <div className="font-bold text-sm text-gray-700">MX Providers</div>
              <div className="text-xs mt-1 text-gray-600">
                {f.mx_providers.length > 0 ? f.mx_providers.join(', ') : 'Unknown'}
              </div>
            </div>
          </div>
          {f.risk_summary && (
            <p className="text-sm text-gray-600 bg-yellow-50 border border-yellow-200 rounded p-3">
              {f.risk_summary}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
