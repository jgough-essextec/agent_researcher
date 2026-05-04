'use client';
import React from 'react';

interface RiskItem {
  finding: string;
  likelihood: number;
  impact: number;
  severity: string;
}

interface RiskHeatMapProps {
  items: RiskItem[];
}

function getCellColor(likelihood: number, impact: number): string {
  const score = likelihood * impact;
  if (score >= 15) return 'bg-red-600';
  if (score >= 9) return 'bg-orange-500';
  if (score >= 4) return 'bg-yellow-400';
  return 'bg-green-400';
}

export function RiskHeatMap({ items }: RiskHeatMapProps) {
  return (
    <div className="overflow-x-auto">
      <div className="flex items-start gap-2">
        {/* Y-axis label */}
        <div className="flex flex-col justify-between h-[140px] text-xs text-gray-500 text-right w-16 pt-1 pb-1">
          <span>Almost Certain (5)</span>
          <span>Likely (4)</span>
          <span>Possible (3)</span>
          <span>Unlikely (2)</span>
          <span>Rare (1)</span>
        </div>
        {/* Grid */}
        <div>
          <div className="grid grid-cols-5 gap-0.5">
            {[5, 4, 3, 2, 1].map((likelihood) =>
              [1, 2, 3, 4, 5].map((impact) => {
                const cellItems = items.filter(
                  (item) => item.likelihood === likelihood && item.impact === impact
                );
                return (
                  <div
                    key={`${likelihood}-${impact}`}
                    className={`w-12 h-7 flex items-center justify-center rounded-sm text-white text-xs font-bold relative ${getCellColor(likelihood, impact)}`}
                    title={cellItems.map((i) => i.finding).join(', ')}
                  >
                    {cellItems.length > 0 && (
                      <span className="bg-white bg-opacity-80 text-gray-800 rounded px-1 text-xs">
                        {cellItems.length}
                      </span>
                    )}
                  </div>
                );
              })
            )}
          </div>
          {/* X-axis labels */}
          <div className="grid grid-cols-5 gap-0.5 mt-1 text-xs text-gray-500 text-center">
            <span>Negligible</span>
            <span>Minor</span>
            <span>Moderate</span>
            <span>Major</span>
            <span>Critical</span>
          </div>
          <div className="text-xs text-gray-400 text-center mt-1">Impact</div>
        </div>
      </div>
      <div className="text-xs text-gray-400 mt-2">Likelihood</div>
    </div>
  );
}
