'use client';
import React, { useEffect, useState } from 'react';
import type { SubdomainFinding, InfrastructureFinding } from '../../../types/osint';
import { getOsintSubdomains, getOsintInfrastructure } from '../../../lib/api';

interface InfrastructureTabProps {
  jobId: string;
}

export function InfrastructureTab({ jobId }: InfrastructureTabProps) {
  const [subdomains, setSubdomains] = useState<SubdomainFinding[]>([]);
  const [infra, setInfra] = useState<InfrastructureFinding[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getOsintSubdomains(jobId), getOsintInfrastructure(jobId)])
      .then(([s, i]) => {
        setSubdomains(s);
        setInfra(i);
      })
      .finally(() => setLoading(false));
  }, [jobId]);

  if (loading) return <div className="text-sm text-gray-500">Loading infrastructure data...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h3 className="font-medium text-gray-800 mb-3">Subdomains ({subdomains.length})</h3>
        {subdomains.length === 0 ? (
          <p className="text-sm text-gray-500">No subdomains discovered yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 pr-4 text-gray-600 font-medium">Subdomain</th>
                  <th className="text-left py-2 pr-4 text-gray-600 font-medium">Category</th>
                  <th className="text-left py-2 pr-4 text-gray-600 font-medium">Status</th>
                  <th className="text-left py-2 text-gray-600 font-medium">Source</th>
                </tr>
              </thead>
              <tbody>
                {subdomains.map((s) => (
                  <tr key={s.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-2 pr-4 font-mono text-xs">{s.subdomain}</td>
                    <td className="py-2 pr-4">
                      <span className="bg-gray-100 text-gray-700 text-xs px-2 py-0.5 rounded">
                        {s.category}
                      </span>
                    </td>
                    <td className="py-2 pr-4">
                      <span
                        className={`text-xs ${
                          s.is_alive === true
                            ? 'text-green-600'
                            : s.is_alive === false
                            ? 'text-red-500'
                            : 'text-gray-400'
                        }`}
                      >
                        {s.is_alive === true
                          ? '● Active'
                          : s.is_alive === false
                          ? '○ Inactive'
                          : '? Unknown'}
                      </span>
                    </td>
                    <td className="py-2 text-xs text-gray-500">{s.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      {infra.length > 0 && (
        <div>
          <h3 className="font-medium text-gray-800 mb-3">Infrastructure Providers</h3>
          <div className="space-y-2">
            {infra.map((f) => (
              <div key={f.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                  {f.infra_type}
                </span>
                <span className="font-medium text-sm text-gray-800">{f.provider_name}</span>
                <span className="text-xs text-gray-500 flex-1">{f.evidence}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
