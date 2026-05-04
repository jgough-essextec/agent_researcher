'use client';
import React from 'react';

interface PhasesStepperProps {
  status: string;
  phaseProgress: {
    phase1: string;
    phase2_auto: string;
    phase2_manual: string;
    phase3: string;
    phase4: string;
    phase5: string;
  };
}

const PHASES = [
  { num: 1, label: 'Web Research', key: 'phase1' as const },
  { num: 2, label: 'DNS & Infrastructure', key: 'phase2_auto' as const },
  { num: 3, label: 'Browser OSINT', key: 'phase3' as const },
  { num: 4, label: 'Analysis', key: 'phase4' as const },
  { num: 5, label: 'Final Report', key: 'phase5' as const },
];

function getPhaseStatus(
  phaseKey: string,
  phaseProgress: PhasesStepperProps['phaseProgress'],
  currentStatus: string
): 'done' | 'active' | 'locked' {
  const val = phaseProgress[phaseKey as keyof typeof phaseProgress];
  if (val === 'completed') return 'done';

  const activeStatuses: Record<string, string[]> = {
    phase1: ['phase1_research', 'phase1_complete'],
    phase2_auto: ['phase2_auto', 'awaiting_terminal_output', 'phase2_processing'],
    phase3: ['awaiting_screenshots', 'phase3_processing'],
    phase4: ['phase4_analysis'],
    phase5: ['phase5_report', 'completed'],
  };

  const active = activeStatuses[phaseKey] || [];
  if (active.includes(currentStatus)) return 'active';
  return 'locked';
}

export function PhasesStepper({ status, phaseProgress }: PhasesStepperProps) {
  return (
    <div className="flex flex-col gap-1">
      {PHASES.map((phase) => {
        const phaseStatus = getPhaseStatus(phase.key, phaseProgress, status);
        return (
          <div key={phase.num} className="flex items-center gap-3 p-2 rounded">
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 ${
                phaseStatus === 'done'
                  ? 'bg-green-500 text-white'
                  : phaseStatus === 'active'
                  ? 'bg-blue-500 text-white animate-pulse'
                  : 'bg-gray-200 text-gray-400'
              }`}
            >
              {phaseStatus === 'done' ? '✓' : phase.num}
            </div>
            <span
              className={`text-sm ${
                phaseStatus === 'done'
                  ? 'text-green-700 font-medium'
                  : phaseStatus === 'active'
                  ? 'text-blue-700 font-medium'
                  : 'text-gray-400'
              }`}
            >
              {phase.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
